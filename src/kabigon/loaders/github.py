from __future__ import annotations

from urllib.parse import urlparse

import httpx

from kabigon.core.errors import InvalidURLError
from kabigon.core.loader import Loader
from kabigon.sources.applicability import RAW_GITHUB_HOST
from kabigon.sources.applicability import parse_github_raw_content_target
from kabigon.sources.applicability import parse_github_target

from .html_extractors import extract_first_tag_subtree
from .utils import html_to_markdown

_IGNORED_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "nav",
    "header",
    "footer",
}


def check_github_url(url: str) -> None:
    parse_github_target(url)


def to_raw_github_url(url: str) -> str:
    """Convert a GitHub blob URL to a raw.githubusercontent.com URL.

    Supports:
      - https://github.com/<owner>/<repo>/blob/<ref>/<path>
      - https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>
    """
    return parse_github_raw_content_target(url).raw_url or url


def extract_main_html(html: str) -> str:
    """Extract GitHub's primary content area without site-specific selectors."""
    return extract_first_tag_subtree(html, ("main", "article"), ignored_tags=_IGNORED_TAGS)


class GitHubLoader(Loader):
    async def load(self, url: str) -> str:
        check_github_url(url)
        parsed = urlparse(url)

        if parsed.netloc == RAW_GITHUB_HOST or "/blob/" in parsed.path:
            raw_url = to_raw_github_url(url)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    raw_url,
                    follow_redirects=True,
                    headers={"Accept": "text/plain, text/markdown;q=0.9, */*;q=0.1"},
                )
                response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text" not in content_type and "json" not in content_type and "xml" not in content_type:
                raise InvalidURLError(url, f"GitHub text content-type (got {content_type!r})")

            return response.text

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                follow_redirects=True,
                headers={
                    "Accept": "text/html,application/xhtml+xml",
                    "User-Agent": "kabigon (httpx)",
                },
            )
            response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type:
            raise InvalidURLError(url, f"GitHub HTML content-type (got {content_type!r})")

        main_html = extract_main_html(response.text)
        return html_to_markdown(main_html)
