import pytest

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderNotApplicableError
from kabigon.core.retrieval import RetrievedHtml
from kabigon.loaders import curl_cffi as curl_module
from kabigon.loaders import news_article as news_article_module
from kabigon.loaders.ltn import LTNLoader
from kabigon.loaders.ltn import extract_ltn_article_html
from kabigon.loaders.utils import html_to_markdown
from kabigon.sources.applicability import parse_ltn_target


@pytest.mark.parametrize(
    "url",
    [
        "https://news.ltn.com.tw/news/life/breakingnews/5432239",
        "https://news.ltn.com.tw/news/politics/breakingnews/1234567",
    ],
)
def test_parse_ltn_target(url: str) -> None:
    parse_ltn_target(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/news",
        "https://www.bbc.com/news/articles/c70k29914q4o",
    ],
)
def test_parse_ltn_target_error(url: str) -> None:
    with pytest.raises(LoaderNotApplicableError, match="Not an LTN URL"):
        parse_ltn_target(url)


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


def test_ltn_article_preserves_escaped_text() -> None:
    html = '<div class="text boxTitle boxText"><pre><code>&lt;widget&gt; &amp;lt;tag&amp;gt;</code></pre></div>'

    extracted = extract_ltn_article_html(html)

    assert html_to_markdown(extracted) == html_to_markdown(html)


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

    async def fake_fetch_html(url: str, *, loader_name: str, headers: dict[str, str]) -> str:
        assert url == "https://news.ltn.com.tw/news/life/breakingnews/5432239"
        assert loader_name == "LTNLoader"
        assert headers
        return html

    monkeypatch.setattr(news_article_module, "fetch_news_article_html", fake_fetch_html)

    loader = LTNLoader()
    result = loader.load_sync("https://news.ltn.com.tw/news/life/breakingnews/5432239")

    assert result == "Clean LTN body paragraph"


def test_ltn_loader_preserves_ltn_extraction_on_curl_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <nav>unrelated page text</nav>
    <div class="text boxTitle boxText"><p>LTN fallback article</p><div id="ad-one">ad</div></div>
    """

    async def fail_httpx(*_args, **_kwargs) -> str:
        raise LoaderContentError("LTNLoader", "https://news.ltn.com.tw/news/life/breakingnews/5432239", "failed")

    async def curl_success(*_args, **_kwargs) -> RetrievedHtml:
        return RetrievedHtml(html, "text/html")

    monkeypatch.setattr(news_article_module, "fetch_news_article_html", fail_httpx)
    monkeypatch.setattr(curl_module, "fetch_curl_html", curl_success)

    result = LTNLoader().load_sync("https://news.ltn.com.tw/news/life/breakingnews/5432239")

    assert result == "LTN fallback article"
