import pytest

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderNotApplicableError
from kabigon.loaders.twitter import TwitterLoader
from kabigon.loaders.twitter import replace_domain
from kabigon.sources.applicability import parse_twitter_target


@pytest.mark.parametrize(
    "url",
    [
        "https://twitter.com/user/status/1",
        "https://x.com/user/status/1",
        "https://fxtwitter.com/user/status/1",
        "https://vxtwitter.com/user/status/1",
        "https://fixvx.com/user/status/1",
        "https://twittpr.com/user/status/1",
        "https://api.fxtwitter.com/user/status/1",
        "https://fixupx.com/user/status/1",
    ],
)
def test_parse_twitter_target_accepts_supported_hosts(url: str) -> None:
    parse_twitter_target(url)


def test_parse_twitter_target_rejects_unknown_host() -> None:
    with pytest.raises(LoaderNotApplicableError):
        parse_twitter_target("https://example.com/user/status/1")


def test_replace_domain_normalizes_to_x() -> None:
    assert replace_domain("https://fxtwitter.com/user/status/1") == "https://x.com/user/status/1"


def test_replace_domain_accepts_custom_domain() -> None:
    assert replace_domain("https://x.com/user/status/1", "twitter.com") == "https://twitter.com/user/status/1"


class FakePermalinks:
    def __init__(self, hrefs: list[str]) -> None:
        self.hrefs = hrefs

    def filter(self, *, has):
        assert has == "time"
        return self

    @property
    def first(self):
        return self

    async def count(self) -> int:
        return min(len(self.hrefs), 1)

    async def get_attribute(self, name: str) -> str:
        assert name == "href"
        return self.hrefs[0]


class FakeArticle:
    def __init__(self, text: str, hrefs: list[str]) -> None:
        self.text = text
        self.hrefs = hrefs

    def locator(self, selector: str) -> FakePermalinks:
        assert selector == 'a[href*="/status/"]'
        return FakePermalinks(self.hrefs)

    async def evaluate(self, expression: str) -> str:
        assert expression == "el => el.outerHTML"
        return f"<article><p>{self.text}</p></article>"


class FakeArticles:
    def __init__(self, articles: list[FakeArticle]) -> None:
        self.articles = articles

    def filter(self, *, has):
        return self

    async def count(self) -> int:
        return len(self.articles)

    def nth(self, index: int) -> FakeArticle:
        return self.articles[index]

    async def all(self) -> list[FakeArticle]:
        return self.articles


class FakePage:
    def __init__(self, articles: list[FakeArticle]) -> None:
        self.articles = FakeArticles(articles)
        self.waited_selectors: list[str] = []

    def locator(self, selector: str):
        return self.articles if selector == "article" else selector

    async def wait_for_selector(self, selector: str, **kwargs) -> None:
        self.waited_selectors.append(selector)

    async def content(self) -> str:
        return "<html><body>Unrelated full page content</body></html>"


def install_page(monkeypatch: pytest.MonkeyPatch, articles: list[FakeArticle]) -> FakePage:
    page = FakePage(articles)

    async def fake_fetch(url: str, **kwargs) -> str:
        await kwargs["after_goto"](page)
        return await kwargs["extract_content"](page)

    monkeypatch.setattr("kabigon.loaders.twitter.fetch_browser_html", fake_fetch)
    return page


@pytest.mark.parametrize("href", ["/bob/status/222", "https://x.com/bob/status/222?ref=share"])
def test_twitter_loader_selects_requested_reply(monkeypatch: pytest.MonkeyPatch, href: str) -> None:
    page = install_page(
        monkeypatch,
        [
            FakeArticle("PARENT TWEET quoting the requested reply", ["/alice/status/111", "/bob/status/222"]),
            FakeArticle("REQUESTED REPLY", [href]),
        ],
    )

    result = TwitterLoader().load_sync("https://x.com/bob/status/222/photo/1")

    assert result == "REQUESTED REPLY"
    assert any("/status/222" in selector for selector in page.waited_selectors)


@pytest.mark.parametrize(
    "articles",
    [[], [FakeArticle("PARENT TWEET", ["/alice/status/111"])], [FakeArticle("Advertisement", [])]],
    ids=["no-articles", "wrong-tweet", "no-permalink"],
)
def test_twitter_loader_rejects_missing_target(monkeypatch: pytest.MonkeyPatch, articles: list[FakeArticle]) -> None:
    install_page(monkeypatch, articles)

    with pytest.raises(LoaderContentError, match="requested tweet"):
        TwitterLoader().load_sync("https://x.com/bob/status/222")


def test_twitter_loader_keeps_non_status_page_support(monkeypatch: pytest.MonkeyPatch) -> None:
    install_page(monkeypatch, [])

    assert TwitterLoader().load_sync("https://x.com/bob") == "Unrelated full page content"
