"""HTTP loader that uses ``curl_cffi`` to impersonate a real browser.

``httpx`` cannot fake the TLS/HTTP2 fingerprint that modern bot-protection
services (Cloudflare, Akamai, …) check. ``curl_cffi`` wraps libcurl-impersonate
and sends a request that looks like Chrome down to the JA3/Akamai fingerprint,
which is often enough to bypass simple WAF rules without spinning up a full
browser.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import cast

from curl_cffi import requests as curl_requests

if TYPE_CHECKING:
    from curl_cffi.requests.impersonate import BrowserTypeLiteral

from kabigon.core.errors import LoaderContentError
from kabigon.core.loader import Loader

from .content_guard import ensure_usable_content
from .utils import html_to_markdown

logger = logging.getLogger(__name__)

DEFAULT_IMPERSONATE: str = "chrome"
DEFAULT_TIMEOUT: float = 20.0


class CurlCffiLoader(Loader):
    """Fetch HTML via curl_cffi with a real browser TLS fingerprint."""

    def __init__(
        self,
        impersonate: str = DEFAULT_IMPERSONATE,
        timeout: float = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.impersonate = impersonate
        self.timeout = timeout
        # curl_cffi sets browser-like headers automatically when ``impersonate``
        # is used. Custom headers, if provided, are layered on top.
        self.headers = headers

    async def load(self, url: str) -> str:
        logger.info("[CurlCffiLoader] Processing URL: %s (impersonate=%s)", url, self.impersonate)

        try:
            async with curl_requests.AsyncSession(
                impersonate=cast("BrowserTypeLiteral", self.impersonate),
            ) as session:
                response = await session.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
                response.raise_for_status()
        except Exception as e:
            logger.warning("[CurlCffiLoader] HTTP error: %s", e)
            raise LoaderContentError(
                "CurlCffiLoader",
                url,
                f"HTTP request failed: {e}",
                "Check that the URL is valid and reachable.",
            ) from e

        result = html_to_markdown(response.content)
        logger.info("[CurlCffiLoader] Extracted HTML content (%s chars)", len(result))
        ensure_usable_content(result, loader_name="CurlCffiLoader", url=url)
        return result
