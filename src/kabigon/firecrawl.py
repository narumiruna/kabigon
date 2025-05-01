import os

from firecrawl import FirecrawlApp

from .loader import Loader


class FirecrawlLoader(Loader):
    def __init__(self, timeout: int | None = None) -> None:
        self.timeout = timeout

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY is not set.")

        self.app = FirecrawlApp(api_key=api_key)

    def load(self, url: str) -> str:
        result = self.app.scrape_url(
            url,
            formats=["markdown"],
            timeout=self.timeout,
        )

        if not result.success:
            raise Exception(f"Failed to load URL: {url}, got: {result.error}")

        return result.markdown

    async def async_load(self, url: str) -> str:
        return self.load(url)
