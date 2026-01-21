import os

from firecrawl import FirecrawlApp

from kabigon.core.exception import FirecrawlAPIKeyNotSetError
from kabigon.core.exception import LoaderError
from kabigon.core.loader import Loader


class FirecrawlLoader(Loader):
    def __init__(self, timeout: int | None = None) -> None:
        self.timeout = timeout

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise FirecrawlAPIKeyNotSetError

        self.app = FirecrawlApp(api_key=api_key)

    def load_sync(self, url: str) -> str:
        result = self.app.scrape_url(
            url,
            formats=["markdown"],
            timeout=self.timeout,
        )

        if not result.success:
            raise LoaderError(url)

        return result.markdown
