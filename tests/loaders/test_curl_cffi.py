from __future__ import annotations

import asyncio
from typing import Any

import pytest

from kabigon.core.errors import LoaderContentError
from kabigon.core.loader import Loader
from kabigon.load_chain import resolve_explicit_load_chain
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


@pytest.mark.parametrize(
    "body",
    [
        b"<p>real news paragraph</p>" * 50,
        b"<p>real news paragraph</p>",
        b"<h1>Troubleshooting access denied errors</h1>" + b"<p>real news paragraph</p>" * 50,
    ],
    ids=["long-page", "short-page", "error-documentation"],
)
def test_curl_cffi_loader_returns_markdown(monkeypatch: pytest.MonkeyPatch, body: bytes) -> None:
    html = b"<html><body>" + body + b"</body></html>"
    _install_fake_session(monkeypatch, _FakeResponse(html))

    result = asyncio.run(CurlCffiLoader().load("https://example.com/article"))
    assert "real news paragraph" in result


def test_curl_cffi_loader_falls_back_after_http_200_access_denied(monkeypatch: pytest.MonkeyPatch) -> None:
    html = (
        b"<html><body><h1>Access Denied</h1>"
        b'<p>You don\'t have permission to access "https://example.com/" on this server.</p>'
        b"<p>Reference #18.abcdef</p></body></html>"
    )
    _install_fake_session(monkeypatch, _FakeResponse(html))

    with pytest.raises(LoaderContentError, match="block/challenge marker"):
        CurlCffiLoader().load_sync("https://example.com/blocked")

    class FallbackLoader(Loader):
        async def load(self, url: str) -> str:
            return "Article from fallback"

    chain = resolve_explicit_load_chain(
        "https://example.com/blocked",
        ("curl-cffi", "fallback"),
        {"curl-cffi": CurlCffiLoader, "fallback": FallbackLoader}.__getitem__,
    )

    assert chain.load_sync() == "Article from fallback"


def test_curl_cffi_loader_rejects_cloudflare_challenge(monkeypatch: pytest.MonkeyPatch) -> None:
    html = b"<html><title>Just a moment...</title><body>Checking your browser</body></html>"
    _install_fake_session(monkeypatch, _FakeResponse(html))

    with pytest.raises(LoaderContentError):
        asyncio.run(CurlCffiLoader().load("https://example.com/blocked"))
