from __future__ import annotations

import asyncio
from typing import Any

import pytest

from kabigon.core.errors import LoaderContentError
from kabigon.loaders import curl_cffi as curl_cffi_module
from kabigon.loaders.curl_cffi import CurlCffiLoader


class _FakeResponse:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def raise_for_status(self) -> None:
        return None


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.last_kwargs: dict[str, Any] | None = None

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get(self, url: str, **kwargs: Any) -> _FakeResponse:
        self.last_kwargs = {"url": url, **kwargs}
        return self._response


def _install_fake_session(monkeypatch: pytest.MonkeyPatch, response: _FakeResponse) -> _FakeSession:
    fake = _FakeSession(response)
    monkeypatch.setattr(
        curl_cffi_module.curl_requests,
        "AsyncSession",
        lambda **_kwargs: fake,
    )
    return fake


def test_curl_cffi_loader_returns_markdown(monkeypatch: pytest.MonkeyPatch) -> None:
    html = b"<html><body>" + (b"<p>real news paragraph</p>" * 50) + b"</body></html>"
    _install_fake_session(monkeypatch, _FakeResponse(html))

    result = asyncio.run(CurlCffiLoader().load("https://example.com/article"))
    assert "real news paragraph" in result


def test_curl_cffi_loader_rejects_cloudflare_challenge(monkeypatch: pytest.MonkeyPatch) -> None:
    html = b"<html><title>Just a moment...</title><body>Checking your browser</body></html>"
    _install_fake_session(monkeypatch, _FakeResponse(html))

    with pytest.raises(LoaderContentError):
        asyncio.run(CurlCffiLoader().load("https://example.com/blocked"))
