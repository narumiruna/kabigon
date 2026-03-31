from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from html.parser import HTMLParser
from typing import cast
from urllib.parse import urlparse

import httpx

from kabigon.core.exception import LoaderContentError
from kabigon.core.exception import LoaderNotApplicableError
from kabigon.core.loader import Loader

from .utils import html_to_markdown
from .utils import normalize_whitespace

logger = logging.getLogger(__name__)

BBC_DOMAIN_SUFFIX = "bbc.com"

_VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

_IGNORED_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
}

_JSON_LD_PATTERN = re.compile(
    r"<script[^>]*type=['\"]application/ld\+json['\"][^>]*>(?P<json>.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)


def check_bbc_url(url: str) -> None:
    host = urlparse(url).netloc.lower()
    if host == BBC_DOMAIN_SUFFIX or host.endswith(f".{BBC_DOMAIN_SUFFIX}"):
        return
    raise LoaderNotApplicableError("BBCLoader", url, "Not a BBC URL. Expected domain ending with bbc.com")


class _SubtreeHTMLExtractor(HTMLParser):
    def __init__(self, root_tag: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root_tag = root_tag
        self._capturing = False
        self._depth = 0
        self._ignored_depth = 0
        self._out: list[str] = []

    def get_html(self) -> str:
        return "".join(self._out).strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == self.root_tag and not self._capturing:
            self._capturing = True
            self._depth = 1
            self._out.append(self.get_starttag_text() or f"<{tag}>")
            return

        if not self._capturing:
            return

        if tag in _IGNORED_TAGS:
            self._ignored_depth += 1
            return

        self._out.append(self.get_starttag_text() or f"<{tag}>")
        if tag not in _VOID_TAGS:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self._capturing:
            return

        if self._ignored_depth:
            if tag in _IGNORED_TAGS:
                self._ignored_depth -= 1
            return

        self._out.append(f"</{tag}>")
        if tag not in _VOID_TAGS:
            self._depth -= 1

        if self._depth <= 0:
            self._capturing = False

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self._capturing:
            return
        if self._ignored_depth or tag in _IGNORED_TAGS:
            return
        self._out.append(self.get_starttag_text() or f"<{tag} />")

    def handle_data(self, data: str) -> None:
        if not self._capturing or self._ignored_depth:
            return
        self._out.append(data)


def _find_article_body(data: object) -> str | None:
    if isinstance(data, Mapping):
        mapping = cast(Mapping[str, object], data)
        article_body = mapping.get("articleBody")
        if isinstance(article_body, str) and article_body.strip():
            return article_body
        for value in mapping.values():
            found = _find_article_body(value)
            if found:
                return found
        return None

    if isinstance(data, list):
        for item in data:
            found = _find_article_body(item)
            if found:
                return found
    return None


def extract_article_body_from_json_ld(html: str) -> str | None:
    for match in _JSON_LD_PATTERN.finditer(html):
        payload = match.group("json").strip()
        if not payload:
            continue
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            continue
        article_body = _find_article_body(parsed)
        if article_body:
            return normalize_whitespace(article_body)
    return None


def extract_bbc_main_html(html: str) -> str:
    for tag in ("article", "main"):
        parser = _SubtreeHTMLExtractor(tag)
        parser.feed(html)
        extracted = parser.get_html()
        if extracted:
            return extracted
    return html


class BBCLoader(Loader):
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers or {
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",  # noqa: E501
        }

    async def load(self, url: str) -> str:
        check_bbc_url(url)
        logger.debug("[BBCLoader] Fetching URL: %s", url)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("[BBCLoader] HTTP error: %s", e)
            raise LoaderContentError("BBCLoader", url, f"HTTP request failed: {e}") from e

        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type:
            raise LoaderContentError("BBCLoader", url, f"Expected HTML content, got: {content_type!r}")

        json_ld_body = extract_article_body_from_json_ld(response.text)
        if json_ld_body:
            logger.debug("[BBCLoader] Extracted articleBody from JSON-LD (%s chars)", len(json_ld_body))
            return json_ld_body

        main_html = extract_bbc_main_html(response.text)
        result = html_to_markdown(main_html)
        logger.debug("[BBCLoader] Extracted article HTML content (%s chars)", len(result))
        return result
