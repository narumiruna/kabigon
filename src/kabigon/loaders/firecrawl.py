import os

from firecrawl import FirecrawlApp

from kabigon.core.exception import ConfigurationError
from kabigon.core.exception import LoaderError
from kabigon.core.loader import Loader


class FirecrawlLoader(Loader):
    def __init__(self, timeout: int | None = None) -> None:
        self.timeout = timeout

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ConfigurationError("FIRECRAWL_API_KEY is not set.")  # noqa: TRY003

        self.app = FirecrawlApp(api_key=api_key)

    def load_sync(self, url: str) -> str:
        result = self.app.scrape_url(  # ty:ignore[possibly-missing-attribute]
            url,
            formats=["markdown"],
            timeout=self.timeout,
        )

        if not result.success:
            raise LoaderError(url)

        return result.markdown
