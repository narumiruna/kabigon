import asyncio
import time
from typing import ClassVar
from typing import cast

import pytest

from kabigon.core.errors import LoaderContentError
from kabigon.core.execution import reset_deadline
from kabigon.core.execution import set_deadline
from kabigon.core.resources import HttpClient
from kabigon.core.retrieval import RetrievedHtml
from kabigon.loaders import curl_cffi as curl_module
from kabigon.loaders import httpx as httpx_module
from kabigon.loaders import news_article as news_article_module
from kabigon.loaders.html_extractors import extract_article_body_from_json_ld
from kabigon.loaders.news_article import extract_news_article_main_html
from kabigon.loaders.news_article import fetch_news_article_html
from kabigon.loaders.news_article import load_news_article


def test_extract_article_body_from_json_ld() -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {"@type":"NewsArticle","headline":"Example","articleBody":"Line 1\\n\\nLine 2"}
        </script>
      </head>
      <body></body>
    </html>
    """

    result = extract_article_body_from_json_ld(html)

    assert result == "Line 1\nLine 2"


def test_extract_news_article_main_html_prefers_article() -> None:
    html = """
    <html>
      <body>
        <header>Nav</header>
        <article><h1>Title</h1><p>Body</p></article>
        <footer>Footer</footer>
      </body>
    </html>
    """

    extracted = extract_news_article_main_html(html)

    assert "<article>" in extracted
    assert "Body" in extracted
    assert "Nav" not in extracted


def test_load_news_article_prefers_json_ld_body(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {"@type":"NewsArticle","articleBody":"News body paragraph"}
        </script>
      </head>
      <body>
        <article><p>fallback html</p></article>
      </body>
    </html>
    """

    async def fake_fetch_html(url: str, *, loader_name: str, headers: dict[str, str]) -> str:
        assert url == "https://example.com/article"
        assert loader_name == "ExampleLoader"
        assert headers == {}
        return html

    monkeypatch.setattr(news_article_module, "fetch_news_article_html", fake_fetch_html)

    result = asyncio.run(
        load_news_article(
            "https://example.com/article",
            loader_name="ExampleLoader",
            validate_url=lambda url: None,
            headers={},
        )
    )

    assert result == "News body paragraph"


def test_news_article_preserves_extractor_across_curl_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    html = "<html><nav>unrelated</nav><article><p>article body only</p></article></html>"

    async def fail_httpx(*_args, **_kwargs) -> str:
        raise LoaderContentError("ExampleLoader", "https://example.com/article", "transport failed")

    async def curl_success(*_args, **_kwargs) -> RetrievedHtml:
        return RetrievedHtml(html, "text/html")

    monkeypatch.setattr(news_article_module, "fetch_news_article_html", fail_httpx)
    monkeypatch.setattr(curl_module, "fetch_curl_html", curl_success)

    result = asyncio.run(
        load_news_article(
            "https://example.com/article",
            loader_name="ExampleLoader",
            validate_url=lambda _url: None,
            headers={},
        )
    )

    assert result == "article body only"
    assert "unrelated" not in result


def test_news_http_transport_receives_remaining_deadline() -> None:
    class Response:
        text = "<article>body</article>"
        headers: ClassVar[dict[str, str]] = {"content-type": "text/html"}

        def raise_for_status(self) -> None:
            return None

    class Client:
        timeout = 0.0

        async def get(self, _url: str, **kwargs):
            self.timeout = kwargs["timeout"]
            return Response()

    async def scenario() -> float:
        client = Client()
        token = set_deadline(time.monotonic() + 0.1)
        try:
            await fetch_news_article_html(
                "https://example.com/article",
                loader_name="ExampleLoader",
                headers={},
                http_client=cast("HttpClient", client),
            )
        finally:
            reset_deadline(token)
        return client.timeout

    timeout = asyncio.run(scenario())
    assert 0 < timeout <= 0.1


def test_fetch_news_article_html_rejects_non_html(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockResponse:
        text = "not html"
        headers: ClassVar[dict[str, str]] = {"content-type": "application/json"}

        def raise_for_status(self) -> None:
            return

    class MockAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url: str, headers: dict[str, str], follow_redirects: bool):
            return MockResponse()

    monkeypatch.setattr(httpx_module.httpx, "AsyncClient", MockAsyncClient)

    with pytest.raises(LoaderContentError, match="Expected HTML content"):
        asyncio.run(
            fetch_news_article_html(
                "https://example.com/article",
                loader_name="ExampleLoader",
                headers={},
            )
        )
