from __future__ import annotations

import asyncio
from typing import Any
from typing import ClassVar

import pytest

from kabigon.core.errors import LoaderContentError
from kabigon.loaders import curl_cffi as curl_cffi_module
from kabigon.loaders.curl_cffi import CurlCffiLoader


class _FakeResponse:
    def __init__(self, content: bytes, headers: dict[str, str] | None = None) -> None:
        self.content = content
        self.headers = headers or {}

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


@pytest.mark.parametrize(
    ("encoding", "content_type", "text"),
    [
        ("big5", "text/html; charset=big5", "繁體中文內容, 這是一段用來測試編碼的新聞文章。"),
        ("shift_jis", "text/html", "日本語の記事です。文字コードの検出を確認します。"),
    ],
    ids=["declared-big5", "detected-shift-jis"],
)
def test_curl_cffi_loader_preserves_response_encoding(
    monkeypatch: pytest.MonkeyPatch, encoding: str, content_type: str, text: str
) -> None:
    html = f"<html><body><p>{text * 20}</p></body></html>".encode(encoding)
    _install_fake_session(monkeypatch, _FakeResponse(html, {"content-type": content_type}))

    result = asyncio.run(CurlCffiLoader().load("https://example.com/article"))

    assert text in result
    assert "�" not in result


def test_curl_cffi_loader_rejects_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class ErrorResponse(_FakeResponse):
        headers: ClassVar[dict[str, str]] = {"content-type": "text/html"}

        def raise_for_status(self) -> None:
            raise RuntimeError("HTTP 503")

    _install_fake_session(monkeypatch, ErrorResponse(b"<p>error</p>"))

    with pytest.raises(LoaderContentError, match="503"):
        asyncio.run(CurlCffiLoader().load("https://example.com/error"))


def test_curl_cffi_loader_rejects_cloudflare_challenge(monkeypatch: pytest.MonkeyPatch) -> None:
    html = b"<html><title>Just a moment...</title><body>Checking your browser</body></html>"
    _install_fake_session(monkeypatch, _FakeResponse(html))

    with pytest.raises(LoaderContentError):
        asyncio.run(CurlCffiLoader().load("https://example.com/blocked"))
