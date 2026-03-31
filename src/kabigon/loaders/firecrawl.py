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
        result = self.app.scrape_url(
            url,
            formats=["markdown"],
            timeout=self.timeout,
        )

        if not result.success:
            raise LoaderError(url)

        return result.markdown
