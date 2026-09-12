import contextlib
import re

import charset_normalizer
from markdownify import markdownify

_CHARSET_PATTERN = re.compile(r"charset\s*=\s*[\"']?([^;\s\"']+)", re.IGNORECASE)


def normalize_whitespace(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            lines += [stripped]
    return "\n".join(lines)


def decode_html(content: str | bytes, content_type: str = "") -> str:
    if isinstance(content, str):
        return content

    charset = _CHARSET_PATTERN.search(content_type)
    if charset is not None:
        with contextlib.suppress(LookupError, UnicodeDecodeError):
            return content.decode(charset.group(1))

    detected = charset_normalizer.from_bytes(content).best()
    return str(detected) if detected is not None else content.decode(errors="replace")


def html_to_markdown(content: str | bytes) -> str:
    """Convert HTML content to normalized markdown."""
    md = markdownify(decode_html(content), strip=["a", "img"])
    return normalize_whitespace(md)
