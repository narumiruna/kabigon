from __future__ import annotations

from collections.abc import Awaitable
from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Protocol

if TYPE_CHECKING:
    from curl_cffi.requests import AsyncSession as CurlSession
    from curl_cffi.requests import Response as CurlResponse
    from httpx import AsyncClient as HttpClient
    from httpx import Response as HttpResponse
    from playwright.async_api import Browser
else:
    Browser = object
    CurlResponse = object
    CurlSession = object
    HttpClient = object
    HttpResponse = object


class ResourceProvider(Protocol):
    async def http_client(self) -> HttpClient: ...

    async def curl_session(self) -> CurlSession: ...

    async def browser(self) -> Browser: ...

    async def run_browser[T](self, operation: Callable[[], Awaitable[T]]) -> T: ...


__all__ = ["Browser", "CurlResponse", "CurlSession", "HttpClient", "HttpResponse", "ResourceProvider"]
