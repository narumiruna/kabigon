from typing import Literal

from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

from .loader import Loader
from .utils import html_to_markdown


class PlaywrightLoader(Loader):
    def __init__(
        self,
        timeout: int = 10_000,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "networkidle",
        browser_headless: bool = False,
    ) -> None:
        self.timeout = timeout
        self.wait_until = wait_until
        self.browser_headless = browser_headless

    def load(self, url: str) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.browser_headless)
            page = browser.new_page()

            page.goto(url, timeout=self.timeout, wait_until=self.wait_until)

            content = page.content()
            browser.close()

            return html_to_markdown(content)

    async def async_load(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.browser_headless)
            page = await browser.new_page()

            await page.goto(url, timeout=self.timeout, wait_until=self.wait_until)

            content = await page.content()
            await browser.close()

            return html_to_markdown(content)
