from typing import ClassVar

import pytest

from kabigon.domain.errors import LoaderNotApplicableError
from kabigon.loaders import news_article as news_article_module
from kabigon.loaders.cnn import CNNLoader
from kabigon.loaders.cnn import check_cnn_url


@pytest.mark.parametrize(
    "url",
    [
        "https://edition.cnn.com/2026/03/16/tech/nvidia-jensen-huang-ai-agents",
        "https://www.cnn.com/2026/03/16/tech/example",
        "https://cnn.com/world/live-news/example",
    ],
)
def test_check_cnn_url(url: str) -> None:
    check_cnn_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/news",
        "https://bbc.com/news/world-123",
    ],
)
def test_check_cnn_url_error(url: str) -> None:
    with pytest.raises(LoaderNotApplicableError, match="Not a CNN URL"):
        check_cnn_url(url)


def test_cnn_loader_uses_news_article_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {"@type":"NewsArticle","articleBody":"CNN body paragraph"}
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

    loader = CNNLoader()
    result = loader.load_sync("https://edition.cnn.com/2026/03/16/tech/nvidia-jensen-huang-ai-agents")

    assert result == "CNN body paragraph"
