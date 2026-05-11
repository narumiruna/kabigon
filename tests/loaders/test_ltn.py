from typing import ClassVar

import pytest

from kabigon.core.errors import LoaderNotApplicableError
from kabigon.loaders import ltn as ltn_module
from kabigon.loaders.ltn import LTNLoader
from kabigon.loaders.ltn import check_ltn_url
from kabigon.loaders.ltn import extract_ltn_article_html


@pytest.mark.parametrize(
    "url",
    [
        "https://news.ltn.com.tw/news/life/breakingnews/5432239",
        "https://news.ltn.com.tw/news/politics/breakingnews/1234567",
    ],
)
def test_check_ltn_url(url: str) -> None:
    check_ltn_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/news",
        "https://www.bbc.com/news/articles/c70k29914q4o",
    ],
)
def test_check_ltn_url_error(url: str) -> None:
    with pytest.raises(LoaderNotApplicableError, match="Not an LTN URL"):
        check_ltn_url(url)


def test_extract_ltn_article_html_targets_article_body_container() -> None:
    html = """
    <html>
      <body>
        <nav>Navigation</nav>
        <div class="text boxTitle boxText" data-desc="內容頁">
          <script>displayDFP('ad')</script>
          <div class="photo boxTitle"><p>Caption</p></div>
          <p>First paragraph</p>
          <p class="before_ir">請繼續往下閱讀...</p>
          <div id="ad-PCIR1"><p>Ad content</p></div>
          <p>Second paragraph</p>
          <p class="appE1121">Download the app</p>
        </div>
        <aside>Related links</aside>
      </body>
    </html>
    """

    extracted = extract_ltn_article_html(html)

    assert "First paragraph" in extracted
    assert "Second paragraph" in extracted
    assert "Caption" in extracted
    assert "displayDFP" not in extracted
    assert "請繼續往下閱讀" not in extracted
    assert "Ad content" not in extracted
    assert "Download the app" not in extracted
    assert "Navigation" not in extracted
    assert "Related links" not in extracted


def test_ltn_loader_uses_ltn_article_container(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {"@type":"NewsArticle","articleBody":"Noisy JSON-LD body 請繼續往下閱讀... displayDFP('ad')"}
        </script>
      </head>
      <body>
        <div class="text boxTitle boxText" data-desc="內容頁">
          <p>Clean LTN body paragraph</p>
        </div>
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

    monkeypatch.setattr(ltn_module.httpx, "AsyncClient", MockAsyncClient)

    loader = LTNLoader()
    result = loader.load_sync("https://news.ltn.com.tw/news/life/breakingnews/5432239")

    assert result == "Clean LTN body paragraph"
