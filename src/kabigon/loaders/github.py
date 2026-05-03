from __future__ import annotations

import logging
from urllib.parse import urlparse

import httpx

from kabigon.core.errors import InvalidURLError
from kabigon.core.loader import Loader
from kabigon.sources.applicability import RAW_GITHUB_HOST
from kabigon.sources.applicability import parse_github_raw_content_target
from kabigon.sources.applicability import parse_github_target
from kabigon.sources.applicability import require_loader_applicability

from .html_extractors import extract_first_tag_subtree
from .utils import html_to_markdown

logger = logging.getLogger(__name__)

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
        logger.info("[GitHubLoader] Processing URL: %s", url)
        require_loader_applicability("GitHubLoader", url, parse_github_target)
        parsed = urlparse(url)

        if parsed.netloc == RAW_GITHUB_HOST or "/blob/" in parsed.path:
            raw_url = to_raw_github_url(url)
            logger.info("[GitHubLoader] Fetching raw GitHub content: %s", raw_url)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    raw_url,
                    follow_redirects=True,
                    headers={"Accept": "text/plain, text/markdown;q=0.9, */*;q=0.1"},
                )
                response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            logger.debug("[GitHubLoader] Raw content-type: %s", content_type)
            if "text" not in content_type and "json" not in content_type and "xml" not in content_type:
                raise InvalidURLError(url, f"GitHub text content-type (got {content_type!r})")

            logger.info("[GitHubLoader] Loaded raw GitHub content (%s chars)", len(response.text))
            return response.text

        logger.info("[GitHubLoader] Fetching GitHub HTML page")
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
        logger.debug("[GitHubLoader] HTML content-type: %s", content_type)
        if "html" not in content_type:
            raise InvalidURLError(url, f"GitHub HTML content-type (got {content_type!r})")

        main_html = extract_main_html(response.text)
        result = html_to_markdown(main_html)
        logger.info("[GitHubLoader] Extracted GitHub HTML content (%s chars)", len(result))
        return result
