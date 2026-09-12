from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import cast

from curl_cffi import requests as curl_requests

from kabigon.core.errors import LoaderContentError
from kabigon.core.loader import Loader
from kabigon.core.resources import CurlResponse
from kabigon.core.resources import CurlSession
from kabigon.core.resources import ResourceProvider
from kabigon.core.retrieval import RetrievedHtml

from .content_guard import ensure_usable_content
from .utils import decode_html
from .utils import html_to_markdown

if TYPE_CHECKING:
    from curl_cffi.requests.impersonate import BrowserTypeLiteral

logger = logging.getLogger(__name__)
DEFAULT_IMPERSONATE = "chrome"
DEFAULT_TIMEOUT = 20.0


async def fetch_curl_html(
    url: str,
    *,
    impersonate: str = DEFAULT_IMPERSONATE,
    request_timeout: float = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
    session: CurlSession | None = None,
    loader_name: str = "CurlCffiLoader",
) -> RetrievedHtml:
    async def request(active_session: CurlSession) -> CurlResponse:
        response = await active_session.get(url, headers=headers, timeout=request_timeout, allow_redirects=True)
        response.raise_for_status()
        return response

    try:
        if session is None:
            async with curl_requests.AsyncSession(impersonate=cast("BrowserTypeLiteral", impersonate)) as owned_session:
                response = await request(owned_session)
        else:
            response = await request(session)
    except Exception as error:
        raise LoaderContentError(loader_name, url, f"HTTP request failed: {error}") from error
    content_type = getattr(response, "headers", {}).get("content-type", "")
    return RetrievedHtml(decode_html(response.content, content_type), content_type)


class CurlCffiLoader(Loader):
    def __init__(
        self,
        impersonate: str = DEFAULT_IMPERSONATE,
        timeout: float = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
        curl_session: CurlSession | None = None,
        resource_provider: ResourceProvider | None = None,
    ) -> None:
        self.impersonate = impersonate
        self.timeout = timeout
        self.headers = headers
        self.curl_session = curl_session
        self.resource_provider = resource_provider

    async def load(self, url: str) -> str:
        session = (
            await self.resource_provider.curl_session() if self.resource_provider is not None else self.curl_session
        )
        response = await fetch_curl_html(
            url,
            impersonate=self.impersonate,
            request_timeout=self.timeout,
            headers=self.headers,
            session=session,
            loader_name="CurlCffiLoader",
        )
        result = html_to_markdown(response.content)
        ensure_usable_content(result, loader_name="CurlCffiLoader", url=url)
        return result


__all__ = ["CurlCffiLoader", "fetch_curl_html"]
