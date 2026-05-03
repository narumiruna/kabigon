import asyncio
import logging
import os
from typing import Any

from firecrawl import FirecrawlApp

from kabigon.core.errors import FirecrawlAPIKeyNotSetError
from kabigon.core.errors import LoaderError
from kabigon.core.loader import Loader

logger = logging.getLogger(__name__)


class FirecrawlLoader(Loader):
    def __init__(self, timeout: int | None = None) -> None:
        self.timeout = timeout

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise FirecrawlAPIKeyNotSetError

        logger.debug("[FirecrawlLoader] Found FIRECRAWL_API_KEY")
        self.app: Any = FirecrawlApp(api_key=api_key)

    def load_sync(self, url: str) -> str:
        logger.info("[FirecrawlLoader] Processing URL: %s", url)
        scrape_kwargs = {
            "formats": ["markdown"],
            "timeout": self.timeout,
        }
        if hasattr(self.app, "scrape_url"):
            logger.info("[FirecrawlLoader] Fetching URL with scrape_url (timeout=%s)", self.timeout)
            result = self.app.scrape_url(url, **scrape_kwargs)
        elif hasattr(self.app, "scrape"):
            logger.info("[FirecrawlLoader] Fetching URL with scrape (timeout=%s)", self.timeout)
            result = self.app.scrape(url, **scrape_kwargs)
        else:
            raise LoaderError(url, ["Firecrawl SDK does not expose scrape methods"])

        success = getattr(result, "success", None)
        if success is False:
            logger.warning("[FirecrawlLoader] Firecrawl scrape returned unsuccessful result")
            raise LoaderError(url, ["Firecrawl scrape returned unsuccessful result"])

        markdown = getattr(result, "markdown", None)
        if markdown is None and isinstance(result, dict):
            markdown = result.get("markdown")
        if not isinstance(markdown, str):
            raise LoaderError(url, ["Firecrawl scrape result did not include markdown"])
        logger.info("[FirecrawlLoader] Extracted markdown content (%s chars)", len(markdown))
        return markdown

    async def load(self, url: str) -> str:
        return await asyncio.to_thread(self.load_sync, url)
