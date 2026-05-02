import logging
from typing import Literal

from kabigon.core.loader import Loader

from .browser import fetch_browser_html
from .utils import html_to_markdown

logger = logging.getLogger(__name__)


class PlaywrightLoader(Loader):
    def __init__(
        self,
        timeout: float | None = 0,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] | None = None,
        browser_headless: bool = True,
    ) -> None:
        self.timeout = timeout
        self.wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] | None = wait_until
        self.browser_headless = browser_headless

    async def load(self, url: str) -> str:
        logger.debug(
            "[PlaywrightLoader] Loading URL: %s (timeout=%s, wait_until=%s)",
            url,
            self.timeout,
            self.wait_until,
        )

        content = await fetch_browser_html(
            url,
            loader_name="PlaywrightLoader",
            timeout_ms=self.timeout,
            timeout_suggestion=(
                "The page took too long to load. Try increasing the timeout or using a faster wait_until option."
            ),
            wait_until=self.wait_until,
            browser_headless=self.browser_headless,
        )
        logger.debug("[PlaywrightLoader] Successfully loaded page")
        result = html_to_markdown(content)
        logger.debug("[PlaywrightLoader] Successfully extracted content (%s chars)", len(result))
        return result
