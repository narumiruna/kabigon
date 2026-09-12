from __future__ import annotations

import logging

import httpx

from kabigon.core.errors import LoaderContentError
from kabigon.core.loader import Loader
from kabigon.core.resources import HttpClient
from kabigon.core.resources import HttpResponse
from kabigon.core.resources import ResourceProvider
from kabigon.core.retrieval import RetrievedHtml

from .content_guard import ensure_usable_content
from .utils import html_to_markdown

logger = logging.getLogger(__name__)

DEFAULT_HTTPX_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _merge_headers(custom: dict[str, str] | None) -> dict[str, str]:
    headers = dict(DEFAULT_HTTPX_HEADERS)
    if custom:
        headers.update(custom)
    return headers


async def fetch_httpx_html(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    client: HttpClient | None = None,
    loader_name: str = "HttpxLoader",
    request_timeout: float | None = None,
) -> RetrievedHtml:
    async def request(active_client: HttpClient) -> HttpResponse:
        if request_timeout is None:
            response = await active_client.get(url, headers=headers, follow_redirects=True)
        else:
            response = await active_client.get(
                url,
                headers=headers,
                follow_redirects=True,
                timeout=request_timeout,
            )
        response.raise_for_status()
        return response

    try:
        if client is None:
            async with httpx.AsyncClient() as owned_client:
                response = await request(owned_client)
        else:
            response = await request(client)
    except httpx.HTTPError as error:
        raise LoaderContentError(loader_name, url, f"HTTP request failed: {error}") from error
    return RetrievedHtml(response.text, response.headers.get("content-type", ""))


class HttpxLoader(Loader):
    def __init__(
        self,
        headers: dict[str, str] | None = None,
        http_client: HttpClient | None = None,
        resource_provider: ResourceProvider | None = None,
    ) -> None:
        self.headers = _merge_headers(headers)
        self.http_client = http_client
        self.resource_provider = resource_provider

    async def load(self, url: str) -> str:
        logger.info("[HttpxLoader] Processing URL: %s", url)
        client = await self.resource_provider.http_client() if self.resource_provider is not None else self.http_client
        response = await fetch_httpx_html(
            url,
            headers=self.headers,
            client=client,
            loader_name="HttpxLoader",
        )
        result = html_to_markdown(response.content)
        ensure_usable_content(result, loader_name="HttpxLoader", url=url)
        return result


__all__ = ["DEFAULT_HTTPX_HEADERS", "HttpxLoader", "fetch_httpx_html"]
