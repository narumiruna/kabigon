"""Shared content validation for HTTP-style loaders.

Several loaders (httpx, curl-cffi, playwright) extract a markdown blob and have
no good way to tell whether what they got is real content or a block page from
a CDN/WAF. Centralizing the heuristic here lets the load chain fall through to
the next loader instead of silently returning a useless "Just a moment..."
challenge page.
"""

from __future__ import annotations

from kabigon.core.errors import LoaderContentError

MIN_CONTENT_LENGTH: int = 300

# Lower-cased substrings that strongly indicate a block, challenge, or
# upstream error page rather than real content.
BLOCKED_MARKERS: tuple[str, ...] = (
    "just a moment...",
    "checking your browser",
    "attention required! | cloudflare",
    "ddos protection by cloudflare",
    "enable javascript and cookies to continue",
    "access denied",
    "403 forbidden",
    "502 bad gateway",
    "503 service",
    "cf-error-details",
)


def ensure_usable_content(
    content: str,
    *,
    loader_name: str,
    url: str,
    min_length: int = MIN_CONTENT_LENGTH,
) -> None:
    """Validate extracted markdown looks like real content.

    Raises :class:`LoaderContentError` when the content is too short or matches
    a known block/challenge marker, so the load chain can fall through to the
    next loader.
    """
    stripped_length = len(content.strip())
    if stripped_length < min_length:
        raise LoaderContentError(
            loader_name,
            url,
            f"Extracted content too short ({stripped_length} chars < {min_length})",
            "Page may be JS-heavy or blocking requests; chain will try next loader.",
        )

    lowered = content.lower()
    for marker in BLOCKED_MARKERS:
        if marker in lowered:
            raise LoaderContentError(
                loader_name,
                url,
                f"Detected block/challenge marker: {marker!r}",
                "The site appears to be blocking automated requests.",
            )


__all__ = ["BLOCKED_MARKERS", "MIN_CONTENT_LENGTH", "ensure_usable_content"]
