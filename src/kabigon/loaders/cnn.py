from __future__ import annotations

import logging

import httpx

from kabigon.application.source_applicability import parse_cnn_target
from kabigon.domain.errors import LoaderContentError
from kabigon.domain.loader import Loader

from .html_extractors import extract_article_body_from_json_ld
from .html_extractors import extract_first_tag_subtree
from .utils import html_to_markdown

logger = logging.getLogger(__name__)

_IGNORED_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
}


def check_cnn_url(url: str) -> None:
    parse_cnn_target(url)


def extract_cnn_main_html(html: str) -> str:
    return extract_first_tag_subtree(html, ("article", "main"), ignored_tags=_IGNORED_TAGS)


class CNNLoader(Loader):
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers or {
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",  # noqa: E501
        }

    async def load(self, url: str) -> str:
        check_cnn_url(url)
        logger.debug("[CNNLoader] Fetching URL: %s", url)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("[CNNLoader] HTTP error: %s", e)
            raise LoaderContentError("CNNLoader", url, f"HTTP request failed: {e}") from e

        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type:
            raise LoaderContentError("CNNLoader", url, f"Expected HTML content, got: {content_type!r}")

        json_ld_body = extract_article_body_from_json_ld(response.text)
        if json_ld_body:
            logger.debug("[CNNLoader] Extracted articleBody from JSON-LD (%s chars)", len(json_ld_body))
            return json_ld_body

        main_html = extract_cnn_main_html(response.text)
        result = html_to_markdown(main_html)
        logger.debug("[CNNLoader] Extracted article HTML content (%s chars)", len(result))
        return result
