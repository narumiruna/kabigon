from __future__ import annotations

import asyncio
import io
from typing import Any

import httpx
import pytest
from curl_cffi import requests as curl_requests

from kabigon.loaders import pdf as pdf_module
from kabigon.loaders.pdf import PDFLoader


class _FailingHttpxClient:
    async def __aenter__(self) -> _FailingHttpxClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get(self, *_args: object, **_kwargs: object) -> None:
        raise httpx.ConnectError("TLS certificate verification failed")


class _CurlResponse:
    def __init__(self) -> None:
        self.content = b"%PDF-test-content"
        self.headers = {"content-type": "application/pdf"}

    def raise_for_status(self) -> None:
        return None


class _CurlSession:
    def __init__(self) -> None:
        self.last_request: dict[str, Any] | None = None

    async def __aenter__(self) -> _CurlSession:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get(self, url: str, **kwargs: Any) -> _CurlResponse:
        self.last_request = {"url": url, **kwargs}
        return _CurlResponse()


def test_remote_pdf_falls_back_to_curl_cffi_after_httpx_transport_error(monkeypatch: pytest.MonkeyPatch) -> None:
    curl_session = _CurlSession()
    monkeypatch.setattr(pdf_module.httpx, "AsyncClient", lambda: _FailingHttpxClient())
    monkeypatch.setattr(curl_requests, "AsyncSession", lambda **_kwargs: curl_session)
    monkeypatch.setattr(
        pdf_module,
        "read_pdf_content",
        lambda source: "fallback PDF text" if isinstance(source, io.BytesIO) else "unexpected source",
    )

    url = "https://example.com/document.pdf"
    result = asyncio.run(PDFLoader().load(url))

    assert result == "fallback PDF text"
    assert curl_session.last_request == {
        "url": url,
        "headers": pdf_module.DEFAULT_HEADERS,
        "timeout": pdf_module.DEFAULT_TIMEOUT,
        "allow_redirects": True,
    }
