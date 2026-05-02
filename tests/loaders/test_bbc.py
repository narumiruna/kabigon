from typing import ClassVar

import pytest

from kabigon.core.errors import LoaderNotApplicableError
from kabigon.loaders import news_article as news_article_module
from kabigon.loaders.bbc import BBCLoader
from kabigon.loaders.bbc import check_bbc_url


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


def test_bbc_loader_uses_news_article_loading(monkeypatch: pytest.MonkeyPatch) -> None:
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

    loader = BBCLoader()
    result = loader.load_sync("https://www.bbc.com/news/articles/c70k29914q4o")

    assert result == "BBC body paragraph"
