import asyncio
import base64
import json
from typing import ClassVar

import pytest

from kabigon.loaders import pi_session
from kabigon.loaders.pi_session import PiSessionLoader
from kabigon.sources.applicability import parse_pi_session_target

SHARED_URL = "https://pi.dev/session/#0230effc86f4a142c885cb59fe9725d5"
RAW_URL = "https://gist.githubusercontent.com/alice/0230effc86f4a142c885cb59fe9725d5/raw/revision/session.html"


def _session_html() -> str:
    data = {
        "header": {
            "type": "session",
            "version": 3,
            "id": "session-123",
            "timestamp": "2026-08-08T06:21:56.606Z",
            "cwd": "/workspace/demo",
        },
        "leafId": "tool-result",
        "systemPrompt": "You are a coding assistant.",
        "tools": [{"name": "read", "description": "Read a file."}],
        "entries": [
            {
                "type": "model_change",
                "id": "model",
                "parentId": None,
                "timestamp": "2026-08-08T06:21:56.670Z",
                "provider": "openai-codex",
                "modelId": "gpt-test",
            },
            {
                "type": "message",
                "id": "user",
                "parentId": "model",
                "timestamp": "2026-08-08T06:21:59.371Z",
                "message": {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Create the loader."},
                        {"type": "image", "mimeType": "image/png", "data": "SECRET_IMAGE_DATA"},
                    ],
                },
            },
            {
                "type": "message",
                "id": "assistant",
                "parentId": "user",
                "timestamp": "2026-08-08T06:22:02.452Z",
                "message": {
                    "role": "assistant",
                    "provider": "openai-codex",
                    "model": "gpt-test",
                    "content": [
                        {"type": "thinking", "thinking": "Inspect the file first."},
                        {"type": "text", "text": "I will inspect it."},
                        {"type": "toolCall", "id": "call-1", "name": "read", "arguments": {"path": "demo.py"}},
                    ],
                },
            },
            {
                "type": "message",
                "id": "tool-result",
                "parentId": "assistant",
                "timestamp": "2026-08-08T06:22:02.455Z",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "call-1",
                    "toolName": "read",
                    "content": [{"type": "text", "text": "print('hello')"}],
                    "isError": False,
                },
            },
            {
                "type": "message",
                "id": "orphan-branch",
                "parentId": "user",
                "timestamp": "2026-08-08T06:23:00.000Z",
                "message": {"role": "assistant", "content": [{"type": "text", "text": "ORPHAN BRANCH"}]},
            },
        ],
    }
    encoded = base64.b64encode(json.dumps(data).encode()).decode()
    return f'<html><body><script id="session-data" type="application/json">{encoded}</script></body></html>'


class FakeResponse:
    def __init__(self, *, payload: object | None = None, text: str = "") -> None:
        self._payload = payload
        self.text = text

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class FakeClient:
    requested_urls: ClassVar[list[str]] = []

    def __init__(self, **_: object) -> None:
        return None

    async def __aenter__(self) -> "FakeClient":
        type(self).requested_urls = []
        return self

    async def __aexit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        return None

    async def get(self, url: str, **_: object) -> FakeResponse:
        type(self).requested_urls.append(url)
        if url == "https://api.github.com/gists/0230effc86f4a142c885cb59fe9725d5":
            return FakeResponse(
                payload={
                    "files": {
                        "session.html": {
                            "truncated": True,
                            "raw_url": RAW_URL,
                            "content": "truncated content must not be parsed",
                        }
                    }
                }
            )
        if url == RAW_URL:
            return FakeResponse(text=_session_html())
        raise AssertionError(f"unexpected URL: {url}")


def test_parse_pi_session_target_supports_deep_link_and_custom_filename() -> None:
    target = parse_pi_session_target(
        "https://pi.dev/session/#abc123/custom%20session.html&leafId=leaf-1&targetId=message-1"
    )

    assert target.gist_id == "abc123"
    assert target.file_name == "custom session.html"
    assert target.leaf_id == "leaf-1"
    assert target.target_id == "message-1"


def test_pi_session_loader_fetches_gist_and_renders_selected_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pi_session.httpx, "AsyncClient", FakeClient)

    result = asyncio.run(PiSessionLoader().load(SHARED_URL))

    assert FakeClient.requested_urls == [
        "https://api.github.com/gists/0230effc86f4a142c885cb59fe9725d5",
        RAW_URL,
    ]
    assert "# Pi Session session-123" in result
    assert "You are a coding assistant." in result
    assert "Create the loader." in result
    assert "[Image: image/png]" in result
    assert "I will inspect it." in result
    assert "#### Thinking" in result
    assert "Inspect the file first." in result
    assert "#### Tool Call: read" in result
    assert '"path": "demo.py"' in result
    assert "### Tool Result: read" in result
    assert "print('hello')" in result
    assert "ORPHAN BRANCH" not in result
    assert "SECRET_IMAGE_DATA" not in result
