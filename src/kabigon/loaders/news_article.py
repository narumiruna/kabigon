from __future__ import annotations

import logging
from collections.abc import Callable

import httpx

from kabigon.core.errors import LoaderContentError

from .html_extractors import extract_article_body_from_json_ld
from .html_extractors import extract_first_tag_subtree
from .utils import html_to_markdown

logger = logging.getLogger(__name__)

DEFAULT_NEWS_ARTICLE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ),
}

_IGNORED_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
}


def extract_news_article_main_html(html: str) -> str:
    return extract_first_tag_subtree(html, ("article", "main"), ignored_tags=_IGNORED_TAGS)


async def load_news_article(
    url: str,
    *,
    loader_name: str,
    validate_url: Callable[[str], object],
    headers: dict[str, str],
) -> str:
    validate_url(url)
    logger.debug("[%s] Fetching URL: %s", loader_name, url)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("[%s] HTTP error: %s", loader_name, e)
        raise LoaderContentError(loader_name, url, f"HTTP request failed: {e}") from e

    content_type = response.headers.get("content-type", "").lower()
    if "html" not in content_type:
        raise LoaderContentError(loader_name, url, f"Expected HTML content, got: {content_type!r}")

    json_ld_body = extract_article_body_from_json_ld(response.text)
    if json_ld_body:
        logger.debug("[%s] Extracted articleBody from JSON-LD (%s chars)", loader_name, len(json_ld_body))
        return json_ld_body

    main_html = extract_news_article_main_html(response.text)
    result = html_to_markdown(main_html)
    logger.debug("[%s] Extracted article HTML content (%s chars)", loader_name, len(result))
    return result
