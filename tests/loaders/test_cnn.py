import pytest

from kabigon.core.exception import LoaderNotApplicableError
from kabigon.loaders import cnn as cnn_module
from kabigon.loaders.cnn import CNNLoader
from kabigon.loaders.cnn import check_cnn_url
from kabigon.loaders.cnn import extract_article_body_from_json_ld
from kabigon.loaders.cnn import extract_cnn_main_html


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


def test_extract_cnn_main_html_prefers_article() -> None:
    html = """
    <html>
      <body>
        <header>Nav</header>
        <article><h1>Title</h1><p>Body</p></article>
        <footer>Footer</footer>
      </body>
    </html>
    """
    extracted = extract_cnn_main_html(html)
    assert "<article>" in extracted
    assert "Body" in extracted
    assert "Nav" not in extracted


def test_cnn_loader_prefers_json_ld_body(monkeypatch: pytest.MonkeyPatch) -> None:
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
        status_code = 200
        text = html
        headers = {"content-type": "text/html; charset=utf-8"}

        def raise_for_status(self) -> None:
            return

    class MockAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url: str, headers: dict[str, str], follow_redirects: bool):
            return MockResponse()

    monkeypatch.setattr(cnn_module.httpx, "AsyncClient", MockAsyncClient)

    loader = CNNLoader()
    result = loader.load_sync("https://edition.cnn.com/2026/03/16/tech/nvidia-jensen-huang-ai-agents")
    assert result == "CNN body paragraph"
