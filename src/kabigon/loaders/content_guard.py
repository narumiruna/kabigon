"""Shared content validation for HTTP-style loaders.

Several loaders (httpx, curl-cffi, playwright) extract a markdown blob and have
no good way to tell whether what they got is real content or a block page from
a CDN/WAF. Centralizing the heuristic here lets the load chain fall through to
the next loader instead of silently returning a useless "Just a moment..."
challenge page.
"""

from __future__ import annotations

from kabigon.core.errors import LoaderContentError

MIN_CONTENT_LENGTH: int = 1

# Lower-cased challenge heading prefixes. Generic HTTP error phrases also occur
# in documentation; HTTP status validation belongs in the retrieval layer.
BLOCKED_MARKERS: tuple[str, ...] = (
    "just a moment...",
    "checking your browser",
    "attention required! | cloudflare",
    "ddos protection by cloudflare",
    "enable javascript and cookies to continue",
)


def ensure_usable_content(
    content: str,
    *,
    loader_name: str,
    url: str,
    min_length: int = MIN_CONTENT_LENGTH,
) -> None:
    """Validate extracted markdown looks like real content.

    By default, accept any non-empty content unless its first line starts with
    a known challenge heading. Mentions of errors or challenges in an article's body
    are not evidence that the page is blocked.
    """
    stripped_length = len(content.strip())
    if stripped_length < min_length:
        raise LoaderContentError(
            loader_name,
            url,
            f"Extracted content too short ({stripped_length} chars < {min_length})",
            "Page may be JS-heavy or blocking requests; chain will try next loader.",
        )

    heading = next(iter(content.strip().splitlines()), "").strip("#*_ \t").lower()
    if heading.startswith(BLOCKED_MARKERS):
        raise LoaderContentError(
            loader_name,
            url,
            f"Detected block/challenge marker: {heading!r}",
            "The site appears to be blocking automated requests.",
        )


__all__ = ["BLOCKED_MARKERS", "MIN_CONTENT_LENGTH", "ensure_usable_content"]
