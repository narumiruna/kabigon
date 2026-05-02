import asyncio
from typing import ClassVar

import pytest

from kabigon.domain.errors import LoaderContentError
from kabigon.loaders import news_article as news_article_module
from kabigon.loaders.html_extractors import extract_article_body_from_json_ld
from kabigon.loaders.news_article import extract_news_article_main_html
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

    class MockResponse:
        text = html
        headers: ClassVar[dict[str, str]] = {"content-type": "text/html; charset=utf-8"}

        def raise_for_status(self) -> None:
            return

    class MockAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url: str, headers: dict[str, str], follow_redirects: bool):
            return MockResponse()

    monkeypatch.setattr(news_article_module.httpx, "AsyncClient", MockAsyncClient)

    result = asyncio.run(
        load_news_article(
            "https://example.com/article",
            loader_name="ExampleLoader",
            validate_url=lambda url: None,
            headers={},
        )
    )

    assert result == "News body paragraph"


def test_load_news_article_rejects_non_html(monkeypatch: pytest.MonkeyPatch) -> None:
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

    monkeypatch.setattr(news_article_module.httpx, "AsyncClient", MockAsyncClient)

    with pytest.raises(LoaderContentError, match="Expected HTML content"):
        asyncio.run(
            load_news_article(
                "https://example.com/article",
                loader_name="ExampleLoader",
                validate_url=lambda url: None,
                headers={},
            )
        )
