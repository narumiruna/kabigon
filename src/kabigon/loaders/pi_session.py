from __future__ import annotations

import base64
import binascii
import json
import logging
import re
from collections.abc import Mapping
from html.parser import HTMLParser
from typing import cast
from urllib.parse import urlparse

import httpx

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderTimeoutError
from kabigon.core.loader import Loader
from kabigon.sources.applicability import PiSessionTarget
from kabigon.sources.applicability import parse_pi_session_target

logger = logging.getLogger(__name__)

_GITHUB_GIST_API = "https://api.github.com/gists/{gist_id}"
_GIST_RAW_HOST = "gist.githubusercontent.com"


class _SessionDataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capturing = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script" and dict(attrs).get("id") == "session-data":
            self._capturing = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._capturing:
            self._capturing = False

    def handle_data(self, data: str) -> None:
        if self._capturing:
            self.parts.append(data)


def _mapping(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    return cast(Mapping[str, object], value)


def _objects(value: object) -> list[object] | None:
    if not isinstance(value, list):
        return None
    return cast(list[object], value)


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _label(value: object, fallback: str) -> str:
    text = _text(value).strip().replace("\n", " ")
    return text or fallback


def _content_error(url: str, reason: str) -> LoaderContentError:
    return LoaderContentError(
        "PiSessionLoader",
        url,
        reason,
        "Check that the shared session still exists and contains a valid Pi session export.",
    )


def _decode_session_export(html: str, source_url: str) -> Mapping[str, object]:
    parser = _SessionDataParser()
    parser.feed(html)
    encoded = "".join(parser.parts).strip()
    if not encoded:
        raise _content_error(source_url, 'Missing embedded <script id="session-data"> payload.')

    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
        payload = json.loads(decoded)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _content_error(source_url, f"Invalid embedded session data: {error}") from error

    session = _mapping(payload)
    if session is None:
        raise _content_error(source_url, "Embedded session data is not a JSON object.")
    return session


def _index_entries(
    raw_entries: list[object], source_url: str
) -> tuple[list[Mapping[str, object]], dict[str, Mapping[str, object]]]:
    entries: list[Mapping[str, object]] = []
    by_id: dict[str, Mapping[str, object]] = {}
    for raw_entry in raw_entries:
        entry = _mapping(raw_entry)
        entry_id = _text(entry.get("id")) if entry is not None else ""
        if entry is None or not entry_id:
            raise _content_error(source_url, "Embedded session data contains an invalid entry.")
        if entry_id in by_id:
            raise _content_error(source_url, f"Embedded session data contains duplicate entry ID {entry_id!r}.")
        entries.append(entry)
        by_id[entry_id] = entry
    return entries, by_id


def _entry_parent_id(entry: Mapping[str, object], entry_id: str, source_url: str) -> str | None:
    parent_id = entry.get("parentId")
    if parent_id is None:
        return None
    if isinstance(parent_id, str) and parent_id:
        return parent_id
    raise _content_error(source_url, f"Entry {entry_id!r} has an invalid parent ID.")


def _walk_ancestry(
    by_id: Mapping[str, Mapping[str, object]], leaf_id: str, source_url: str
) -> list[Mapping[str, object]]:
    selected: list[Mapping[str, object]] = []
    visited: set[str] = set()
    current_id: str | None = leaf_id
    while current_id is not None:
        if current_id in visited:
            raise _content_error(source_url, "Embedded session entry ancestry contains a cycle.")
        visited.add(current_id)

        entry = by_id.get(current_id)
        if entry is None:
            raise _content_error(source_url, f"Session parent entry {current_id!r} was not found.")
        selected.append(entry)
        current_id = _entry_parent_id(entry, current_id, source_url)

    selected.reverse()
    return selected


def _selected_entries(
    session: Mapping[str, object],
    requested_leaf_id: str | None,
    source_url: str,
) -> list[Mapping[str, object]]:
    raw_entries = _objects(session.get("entries"))
    if raw_entries is None:
        raise _content_error(source_url, "Embedded session data has no entries list.")

    entries, by_id = _index_entries(raw_entries, source_url)
    if not entries:
        return []

    leaf_id = requested_leaf_id or _text(session.get("leafId")) or _text(entries[-1].get("id"))
    if leaf_id not in by_id:
        raise _content_error(source_url, f"Session leaf {leaf_id!r} was not found.")
    return _walk_ancestry(by_id, leaf_id, source_url)


def _fenced_block(text: str, language: str = "") -> str:
    longest_run = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest_run + 1)
    return f"{fence}{language}\n{text.rstrip()}\n{fence}"


def _entry_metadata(entry: Mapping[str, object], *extra_lines: str) -> list[str]:
    lines = [line for line in extra_lines if line]
    timestamp = _text(entry.get("timestamp"))
    if timestamp:
        lines.append(f"- Timestamp: {timestamp}")
    return lines


def _render_content_block(block: Mapping[str, object]) -> list[str]:
    block_type = _text(block.get("type"))
    if block_type == "text":
        text = _text(block.get("text")).strip()
        return [text] if text else []
    if block_type == "thinking":
        thinking = _text(block.get("thinking")).strip()
        return ["#### Thinking", thinking] if thinking else []
    if block_type == "toolCall":
        name = _label(block.get("name"), "unknown")
        arguments = block.get("arguments")
        arguments_json = json.dumps(arguments if arguments is not None else {}, ensure_ascii=False, indent=2)
        return [f"#### Tool Call: {name}", _fenced_block(arguments_json, "json")]
    if block_type == "image":
        mime_type = _label(block.get("mimeType"), "unknown type")
        return [f"[Image: {mime_type}]"]
    return []


def _render_content_blocks(content: object) -> list[str]:
    if isinstance(content, str):
        return [content.strip()] if content.strip() else []

    rendered: list[str] = []
    for raw_block in _objects(content) or []:
        block = _mapping(raw_block)
        if block is not None:
            rendered.extend(_render_content_block(block))
    return rendered


def _render_message(entry: Mapping[str, object], message: Mapping[str, object]) -> str | None:
    role = _text(message.get("role"))
    if role == "user":
        heading = "### User"
        metadata = _entry_metadata(entry)
        body = _render_content_blocks(message.get("content"))
    elif role == "assistant":
        heading = "### Assistant"
        provider = _text(message.get("provider"))
        model = _text(message.get("model"))
        model_name = "/".join(part for part in (provider, model) if part)
        metadata = _entry_metadata(entry, f"- Model: {model_name}" if model_name else "")
        body = _render_content_blocks(message.get("content"))
        stop_reason = _text(message.get("stopReason"))
        if stop_reason in {"aborted", "error"}:
            detail = _text(message.get("errorMessage"))
            body.append(f"**{stop_reason.title()}:** {detail or 'No details provided.'}")
    elif role == "toolResult":
        tool_name = _label(message.get("toolName"), "unknown")
        heading = f"### Tool Result: {tool_name}"
        status = "error" if message.get("isError") is True else "success"
        metadata = _entry_metadata(entry, f"- Status: {status}")
        body = _render_content_blocks(message.get("content"))
    elif role == "bashExecution":
        heading = "### Bash Execution"
        metadata = _entry_metadata(entry)
        body = []
        command = _text(message.get("command"))
        output = _text(message.get("output"))
        if command:
            body.append(_fenced_block(command, "bash"))
        if output:
            body.append(_fenced_block(output, "text"))
    else:
        heading = f"### {_label(role, 'Message')}"
        metadata = _entry_metadata(entry)
        body = _render_content_blocks(message.get("content"))

    if not metadata and not body:
        return None
    return "\n\n".join([heading, *metadata, *body])


def _render_non_message(entry: Mapping[str, object]) -> str | None:
    entry_type = _text(entry.get("type"))
    if entry_type == "model_change":
        provider = _text(entry.get("provider"))
        model = _text(entry.get("modelId"))
        model_name = "/".join(part for part in (provider, model) if part) or "unknown"
        return "\n\n".join(["### Model Change", *_entry_metadata(entry), model_name])
    if entry_type == "thinking_level_change":
        level = _label(entry.get("thinkingLevel"), "unknown")
        return "\n\n".join(["### Thinking Level Change", *_entry_metadata(entry), level])
    if entry_type == "compaction":
        tokens_before = entry.get("tokensBefore")
        token_line = f"- Tokens before: {tokens_before}" if isinstance(tokens_before, int) else ""
        summary = _text(entry.get("summary")).strip()
        return "\n\n".join(["### Compaction", *_entry_metadata(entry, token_line), summary]).strip()
    if entry_type == "branch_summary":
        summary = _text(entry.get("summary")).strip()
        return "\n\n".join(["### Branch Summary", *_entry_metadata(entry), summary]).strip()
    if entry_type == "custom_message" and entry.get("display") is True:
        custom_type = _label(entry.get("customType"), "Custom Message")
        content = entry.get("content")
        body = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2)
        return "\n\n".join([f"### {custom_type}", *_entry_metadata(entry), body]).strip()
    return None


def _render_header_sections(session: Mapping[str, object], header: Mapping[str, object], source_url: str) -> list[str]:
    session_id = _label(header.get("id"), "unknown")
    header_lines = []
    timestamp = _text(header.get("timestamp"))
    cwd = _text(header.get("cwd"))
    if timestamp:
        header_lines.append(f"- Date: {timestamp}")
    if cwd:
        header_lines.append(f"- Working directory: `{cwd}`")
    header_lines.append(f"- Source: {source_url}")

    sections = [f"# Pi Session {session_id}", "\n".join(header_lines)]
    system_prompt = _text(session.get("systemPrompt")).strip()
    if system_prompt:
        sections.extend(["## System Prompt", system_prompt])
    return sections


def _render_tools(session: Mapping[str, object]) -> str:
    tool_lines: list[str] = []
    for raw_tool in _objects(session.get("tools")) or []:
        tool = _mapping(raw_tool)
        if tool is None:
            continue
        name = _label(tool.get("name"), "unknown")
        description = _text(tool.get("description")).strip()
        tool_lines.append(f"- **{name}** — {description}" if description else f"- **{name}**")
    return "\n".join(tool_lines)


def _render_entries(entries: list[Mapping[str, object]]) -> list[str]:
    rendered_entries: list[str] = []
    for entry in entries:
        if _text(entry.get("type")) == "message":
            message = _mapping(entry.get("message"))
            rendered = _render_message(entry, message) if message is not None else None
        else:
            rendered = _render_non_message(entry)
        if rendered:
            rendered_entries.append(rendered)
    return rendered_entries


def render_pi_session_markdown(
    session: Mapping[str, object],
    *,
    source_url: str,
    leaf_id: str | None = None,
) -> str:
    header = _mapping(session.get("header"))
    if header is None:
        raise _content_error(source_url, "Embedded session data has no header object.")

    sections = _render_header_sections(session, header, source_url)
    tools = _render_tools(session)
    if tools:
        sections.extend(["## Available Tools", tools])

    rendered_entries = _render_entries(_selected_entries(session, leaf_id, source_url))
    if rendered_entries:
        sections.extend(["## Conversation", *rendered_entries])
    return "\n\n".join(section for section in sections if section).strip()


def _gist_file(gist: object, target: PiSessionTarget, source_url: str) -> Mapping[str, object]:
    gist_data = _mapping(gist)
    files = _mapping(gist_data.get("files")) if gist_data is not None else None
    file_data = _mapping(files.get(target.file_name)) if files is not None else None
    if file_data is None:
        raise _content_error(source_url, f"Gist does not contain {target.file_name!r}.")
    return file_data


def _validated_raw_url(value: object, source_url: str) -> str:
    raw_url = _text(value)
    parsed = urlparse(raw_url)
    if parsed.scheme != "https" or parsed.hostname != _GIST_RAW_HOST:
        raise _content_error(source_url, "Gist returned an invalid raw content URL.")
    return raw_url


class PiSessionLoader(Loader):
    """Load a pi.dev shared session export from its backing GitHub Gist."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    async def load(self, url: str) -> str:
        logger.info("[PiSessionLoader] Processing URL: %s", url)
        target = parse_pi_session_target(url)
        api_url = _GITHUB_GIST_API.format(gist_id=target.gist_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(
                    api_url,
                    headers={
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "kabigon (pi.dev shared session loader)",
                    },
                )
                response.raise_for_status()
                file_data = _gist_file(response.json(), target, url)

                content = _text(file_data.get("content"))
                if file_data.get("truncated") is True or not content:
                    raw_url = _validated_raw_url(file_data.get("raw_url"), url)
                    logger.info("[PiSessionLoader] Fetching truncated session export: %s", raw_url)
                    raw_response = await client.get(raw_url)
                    raw_response.raise_for_status()
                    content = raw_response.text
        except httpx.TimeoutException as error:
            raise LoaderTimeoutError(
                "PiSessionLoader",
                url,
                self.timeout,
                "GitHub timed out while retrieving the shared Pi session.",
            ) from error
        except httpx.HTTPError as error:
            raise _content_error(url, f"GitHub request failed: {error}") from error
        except ValueError as error:
            raise _content_error(url, f"GitHub returned invalid Gist metadata: {error}") from error

        session = _decode_session_export(content, url)
        result = render_pi_session_markdown(session, source_url=url, leaf_id=target.leaf_id)
        logger.info("[PiSessionLoader] Extracted Pi session content (%s chars)", len(result))
        return result
