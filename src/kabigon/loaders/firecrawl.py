import asyncio
import os
from typing import Any

from firecrawl import FirecrawlApp

from kabigon.domain.errors import FirecrawlAPIKeyNotSetError
from kabigon.domain.errors import LoaderError
from kabigon.domain.loader import Loader


class FirecrawlLoader(Loader):
    def __init__(self, timeout: int | None = None) -> None:
        self.timeout = timeout

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise FirecrawlAPIKeyNotSetError

        self.app: Any = FirecrawlApp(api_key=api_key)

    def load_sync(self, url: str) -> str:
        scrape_kwargs = {
            "formats": ["markdown"],
            "timeout": self.timeout,
        }
        if hasattr(self.app, "scrape_url"):
            result = self.app.scrape_url(url, **scrape_kwargs)
        elif hasattr(self.app, "scrape"):
            result = self.app.scrape(url, **scrape_kwargs)
        else:
            raise LoaderError(url, ["Firecrawl SDK does not expose scrape methods"])

        success = getattr(result, "success", None)
        if success is False:
            raise LoaderError(url, ["Firecrawl scrape returned unsuccessful result"])

        markdown = getattr(result, "markdown", None)
        if markdown is None and isinstance(result, dict):
            markdown = result.get("markdown")
        if not isinstance(markdown, str):
            raise LoaderError(url, ["Firecrawl scrape result did not include markdown"])
        return markdown

    async def load(self, url: str) -> str:
        return await asyncio.to_thread(self.load_sync, url)
