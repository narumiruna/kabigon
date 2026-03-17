import pytest
from typing import ClassVar

from kabigon.core.exception import LoaderNotApplicableError
from kabigon.loaders import bbc as bbc_module
from kabigon.loaders.bbc import BBCLoader
from kabigon.loaders.bbc import check_bbc_url
from kabigon.loaders.bbc import extract_article_body_from_json_ld
from kabigon.loaders.bbc import extract_bbc_main_html


@pytest.mark.parametrize(
    "url",
    [
        "https://www.bbc.com/news/articles/c70k29914q4o",
        "https://bbc.com/news/world-123",
        "https://www.bbc.com/sport/football/articles/example",
    ],
)
def test_check_bbc_url(url: str) -> None:
    check_bbc_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/news",
        "https://edition.cnn.com/2026/03/16/tech/example",
    ],
)
def test_check_bbc_url_error(url: str) -> None:
    with pytest.raises(LoaderNotApplicableError, match="Not a BBC URL"):
        check_bbc_url(url)


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


def test_extract_bbc_main_html_prefers_article() -> None:
    html = """
    <html>
      <body>
        <header>Nav</header>
        <article><h1>Title</h1><p>Body</p></article>
        <footer>Footer</footer>
      </body>
    </html>
    """
    extracted = extract_bbc_main_html(html)
    assert "<article>" in extracted
    assert "Body" in extracted
    assert "Nav" not in extracted


def test_bbc_loader_prefers_json_ld_body(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {"@type":"NewsArticle","articleBody":"BBC body paragraph"}
        </script>
      </head>
      <body>
        <article><p>fallback html</p></article>
      </body>
    </html>
    """

    class MockResponse:
        status_code = 200
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

    monkeypatch.setattr(bbc_module.httpx, "AsyncClient", MockAsyncClient)

    loader = BBCLoader()
    result = loader.load_sync("https://www.bbc.com/news/articles/c70k29914q4o")
    assert result == "BBC body paragraph"
