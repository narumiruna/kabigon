import logging

import httpx

from kabigon.core.exception import LoaderContentError
from kabigon.core.loader import Loader

from .utils import html_to_markdown

logger = logging.getLogger(__name__)


class HttpxLoader(Loader):
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers

    async def load(self, url: str) -> str:
        logger.debug("[HttpxLoader] Fetching URL: %s", url)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("[HttpxLoader] HTTP error: %s", e)
            raise LoaderContentError(
                "HttpxLoader", url, f"HTTP request failed: {e}", "Check that the URL is valid and accessible."
            ) from e

        result = html_to_markdown(response.content)
        logger.debug("[HttpxLoader] Successfully converted to markdown (%s chars)", len(result))
        return result
