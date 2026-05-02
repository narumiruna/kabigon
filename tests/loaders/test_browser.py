import asyncio

import pytest
from playwright.async_api import TimeoutError

from kabigon.core.errors import LoaderTimeoutError
from kabigon.loaders import browser


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
        self.goto_timeout = 0.0
        self.goto_wait_until = ""

    async def route(self, pattern: str, handler) -> None:
        self.route_pattern = pattern
        self.route_handler = handler

    async def goto(self, url: str, **kwargs) -> None:
        if self.raise_timeout:
            raise TimeoutError("timeout")
        self.goto_timeout = kwargs["timeout"]
        self.goto_wait_until = kwargs.get("wait_until", "")

    async def content(self) -> str:
        return "<html><body>content</body></html>"


class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self.page = page
        self.closed = False

    async def new_page(self) -> FakePage:
        return self.page

    async def close(self) -> None:
        self.closed = True


class FakeBrowser:
    def __init__(self, context: FakeContext) -> None:
        self.context = context
        self.closed = False
        self.user_agent = None

    async def new_context(self, **kwargs) -> FakeContext:
        self.user_agent = kwargs.get("user_agent")
        return self.context

    async def close(self) -> None:
        self.closed = True


class FakeChromium:
    def __init__(self, browser_: FakeBrowser) -> None:
        self.browser = browser_
        self.headless = None

    async def launch(self, headless: bool) -> FakeBrowser:
        self.headless = headless
        return self.browser


class FakePlaywright:
    def __init__(self, chromium: FakeChromium) -> None:
        self.chromium = chromium


class FakePlaywrightContextManager:
    def __init__(self, playwright: FakePlaywright) -> None:
        self.playwright = playwright

    async def __aenter__(self) -> FakePlaywright:
        return self.playwright

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


def _set_fake_playwright(monkeypatch: pytest.MonkeyPatch, page: FakePage) -> tuple[FakeBrowser, FakeChromium]:
    context = FakeContext(page)
    fake_browser = FakeBrowser(context)
    chromium = FakeChromium(fake_browser)
    manager = FakePlaywrightContextManager(FakePlaywright(chromium))
    monkeypatch.setattr(browser, "async_playwright", lambda: manager)
    return fake_browser, chromium


def test_fetch_browser_html_applies_navigation_options_and_closes_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    page = FakePage()
    fake_browser, chromium = _set_fake_playwright(monkeypatch, page)

    html = asyncio.run(
        browser.fetch_browser_html(
            "https://example.com",
            loader_name="TestLoader",
            timeout_ms=10_000,
            timeout_suggestion="try again",
            wait_until="domcontentloaded",
            user_agent="test-agent",
            browser_headless=False,
        )
    )

    assert html == "<html><body>content</body></html>"
    assert chromium.headless is False
    assert fake_browser.user_agent == "test-agent"
    assert page.goto_timeout == 10_000
    assert page.goto_wait_until == "domcontentloaded"
    assert fake_browser.context.closed is True
    assert fake_browser.closed is True


def test_fetch_browser_html_filters_blocked_resources(monkeypatch: pytest.MonkeyPatch) -> None:
    page = FakePage()
    _set_fake_playwright(monkeypatch, page)

    asyncio.run(
        browser.fetch_browser_html(
            "https://example.com",
            loader_name="TestLoader",
            timeout_ms=10_000,
            timeout_suggestion="try again",
            block_resource_types=frozenset({"image"}),
        )
    )

    assert page.route_handler is not None
    image_route = FakeRoute()
    script_route = FakeRoute()
    asyncio.run(page.route_handler(image_route, FakeRequest("image")))
    asyncio.run(page.route_handler(script_route, FakeRequest("script")))
    assert image_route.aborted is True
    assert script_route.continued is True


def test_fetch_browser_html_maps_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_fake_playwright(monkeypatch, FakePage(raise_timeout=True))

    with pytest.raises(LoaderTimeoutError, match=r"timed out after 1\.0s"):
        asyncio.run(
            browser.fetch_browser_html(
                "https://example.com",
                loader_name="TestLoader",
                timeout_ms=1_000,
                timeout_suggestion="try again",
            )
        )
