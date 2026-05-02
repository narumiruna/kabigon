import pytest
from playwright.async_api import TimeoutError

from kabigon.core.errors import LoaderNotApplicableError
from kabigon.core.errors import LoaderTimeoutError
from kabigon.loaders.truthsocial import TruthSocialLoader
from kabigon.loaders.truthsocial import check_truthsocial_url


@pytest.mark.parametrize(
    "url",
    [
        "https://truthsocial.com/@realDonaldTrump/posts/123456",
        "https://www.truthsocial.com/@user/posts/789",
    ],
)
def test_check_truthsocial_url(url: str) -> None:
    """Test that valid Truth Social URLs pass validation."""
    check_truthsocial_url(url)  # Should not raise


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "https://twitter.com/user/status/123",
        "https://x.com/user/status/123",
    ],
)
def test_check_truthsocial_url_error(url: str) -> None:
    """Test that non-Truth Social URLs raise LoaderNotApplicableError."""
    with pytest.raises(LoaderNotApplicableError, match="Not a Truth Social URL"):
        check_truthsocial_url(url)


def test_truthsocial_loader_initialization() -> None:
    """Test TruthSocialLoader initialization."""
    loader = TruthSocialLoader()
    assert loader.timeout == 60_000


def test_truthsocial_loader_custom_timeout() -> None:
    """Test TruthSocialLoader with custom timeout."""
    loader = TruthSocialLoader(timeout=30_000)
    assert loader.timeout == 30_000


class FakeRequest:
    def __init__(self, resource_type: str) -> None:
        self.resource_type = resource_type


class FakeRoute:
    def __init__(self) -> None:
        self.aborted = False
        self.continued = False

    async def abort(self) -> None:
        self.aborted = True

    async def continue_(self) -> None:
        self.continued = True


class FakePage:
    def __init__(self, raise_timeout: bool = False) -> None:
        self.raise_timeout = raise_timeout
        self.route_pattern = ""
        self.route_handler = None
        self.goto_wait_until = ""
        self.goto_timeout = 0.0
        self.selector_timeout = 0.0

    async def route(self, pattern: str, handler) -> None:
        self.route_pattern = pattern
        self.route_handler = handler

    async def goto(self, url: str, **kwargs) -> None:
        if self.raise_timeout:
            raise TimeoutError("timeout")
        self.goto_timeout = kwargs["timeout"]
        self.goto_wait_until = kwargs["wait_until"]

    async def wait_for_selector(self, selector: str, state: str, **kwargs) -> None:
        self.selector_timeout = kwargs["timeout"]

    async def content(self) -> str:
        return "<html><body><article>truth</article></body></html>"


class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self._page = page

    async def new_page(self) -> FakePage:
        return self._page


class FakeBrowser:
    def __init__(self, context: FakeContext) -> None:
        self._context = context

    async def new_context(self, user_agent: str) -> FakeContext:
        return self._context

    async def close(self) -> None:
        return None


class FakeChromium:
    def __init__(self, browser: FakeBrowser) -> None:
        self._browser = browser

    async def launch(self, headless: bool) -> FakeBrowser:
        return self._browser


class FakePlaywright:
    def __init__(self, chromium: FakeChromium) -> None:
        self.chromium = chromium


class FakePlaywrightContextManager:
    def __init__(self, playwright: FakePlaywright) -> None:
        self._playwright = playwright

    async def __aenter__(self) -> FakePlaywright:
        return self._playwright

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


def _set_fake_playwright(monkeypatch: pytest.MonkeyPatch, page: FakePage) -> FakePage:
    context = FakeContext(page)
    browser = FakeBrowser(context)
    chromium = FakeChromium(browser)
    playwright = FakePlaywright(chromium)
    manager = FakePlaywrightContextManager(playwright)
    monkeypatch.setattr("kabigon.loaders.truthsocial.async_playwright", lambda: manager)
    return page


def test_truthsocial_loader_uses_fast_navigation_strategy(monkeypatch: pytest.MonkeyPatch) -> None:
    page = _set_fake_playwright(monkeypatch, FakePage())
    loader = TruthSocialLoader(timeout=10_000)
    result = loader.load_sync("https://truthsocial.com/@realDonaldTrump/posts/123456")

    assert page.route_pattern == "**/*"
    assert page.goto_wait_until == "domcontentloaded"
    assert page.goto_timeout == 10_000
    assert page.selector_timeout == 5_000
    assert "truth" in result


def test_truthsocial_loader_filters_heavy_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    page = _set_fake_playwright(monkeypatch, FakePage())
    loader = TruthSocialLoader(timeout=10_000)
    loader.load_sync("https://truthsocial.com/@realDonaldTrump/posts/123456")

    assert page.route_handler is not None
    image_route = FakeRoute()
    script_route = FakeRoute()
    asyncio.run(page.route_handler(image_route, FakeRequest("image")))
    asyncio.run(page.route_handler(script_route, FakeRequest("script")))
    assert image_route.aborted is True
    assert script_route.continued is True


def test_truthsocial_loader_timeout_maps_to_loader_timeout_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake_playwright(monkeypatch, FakePage(raise_timeout=True))
    loader = TruthSocialLoader(timeout=1_000)
    with pytest.raises(LoaderTimeoutError, match=r"timed out after 1\.0s"):
        loader.load_sync("https://truthsocial.com/@realDonaldTrump/posts/123456")
