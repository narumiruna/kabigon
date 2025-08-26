from typing import Literal

from loguru import logger

from .loader import Loader
from .utils import html_to_markdown


class PlaywrightLoader(Loader):
    def __init__(
        self,
        timeout: float | None = 0,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] | None = None,
        browser_headless: bool = False,
    ) -> None:
        self.timeout = timeout
        self.wait_until = wait_until
        self.browser_headless = browser_headless

    def load(self, url: str) -> str:
        try:
            from playwright.sync_api import TimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise ImportError(
                "Playwright is not installed."
                "Please install it with `pip install playwright` and run `playwright install`."
            ) from e

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.browser_headless)
            context = browser.new_context()
            page = context.new_page()

            try:
                page.goto(url, timeout=self.timeout, wait_until=self.wait_until)
            except TimeoutError as e:
                logger.warning("TimeoutError: {}, (url: {}, timeout: {})", e, url, self.timeout)

            content = page.content()
            browser.close()

            return html_to_markdown(content)

    async def async_load(self, url: str) -> str:
        try:
            from playwright.async_api import TimeoutError
            from playwright.async_api import async_playwright
        except ImportError as e:
            raise ImportError(
                "Playwright is not installed."
                "Please install it with `pip install playwright` and run `playwright install`."
            ) from e

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.browser_headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto(url, timeout=self.timeout, wait_until=self.wait_until)
            except TimeoutError as e:
                logger.warning("TimeoutError: {}, (url: {}, timeout: {})", e, url, self.timeout)

            content = await page.content()
            await browser.close()

            return html_to_markdown(content)
