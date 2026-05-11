import logging

import httpx

from kabigon.core.errors import LoaderContentError
from kabigon.core.loader import Loader

from .utils import html_to_markdown

logger = logging.getLogger(__name__)

DEFAULT_HTTPX_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"),
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _merge_headers(custom: dict[str, str] | None) -> dict[str, str]:
    headers = dict(DEFAULT_HTTPX_HEADERS)
    if custom:
        headers.update(custom)
    return headers


class HttpxLoader(Loader):
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = _merge_headers(headers)

    async def load(self, url: str) -> str:
        logger.info("[HttpxLoader] Processing URL: %s", url)

        try:
            logger.info("[HttpxLoader] Fetching HTML content")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("[HttpxLoader] HTTP error: %s", e)
            raise LoaderContentError(
                "HttpxLoader", url, f"HTTP request failed: {e}", "Check that the URL is valid and accessible."
            ) from e

        result = html_to_markdown(response.content)
        logger.info("[HttpxLoader] Extracted HTML content (%s chars)", len(result))
        return result
