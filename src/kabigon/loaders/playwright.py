import logging
from typing import Literal

from playwright.async_api import TimeoutError
from playwright.async_api import async_playwright

from kabigon.core.exception import LoaderTimeoutError
from kabigon.core.loader import Loader

from .utils import html_to_markdown

logger = logging.getLogger(__name__)


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

    async def load(self, url: str) -> str:
        logger.debug(f"[PlaywrightLoader] Loading URL: {url} (timeout={self.timeout}, wait_until={self.wait_until})")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.browser_headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto(url, timeout=self.timeout, wait_until=self.wait_until)
                logger.debug("[PlaywrightLoader] Successfully loaded page")
            except TimeoutError as e:
                await browser.close()
                timeout_seconds = (self.timeout or 0) / 1000 if self.timeout else 30
                logger.warning(f"[PlaywrightLoader] Timeout after {timeout_seconds}s: {url}")
                raise LoaderTimeoutError(
                    "PlaywrightLoader",
                    url,
                    timeout_seconds,
                    "The page took too long to load. Try increasing the timeout or using a faster wait_until option."
                ) from e

            content = await page.content()
            await browser.close()

            result = html_to_markdown(content)
            logger.debug(f"[PlaywrightLoader] Successfully extracted content ({len(result)} chars)")
            return result
