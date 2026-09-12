from __future__ import annotations

import json
import re
from collections.abc import Mapping
from html import escape
from html.parser import HTMLParser
from typing import cast

from .utils import normalize_whitespace

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

_JSON_LD_PATTERN = re.compile(
    r"<script[^>]*type=['\"]application/ld\+json['\"][^>]*>(?P<json>.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)


class SubtreeHTMLExtractor(HTMLParser):
    def __init__(self, root_tag: str, ignored_tags: set[str] | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.root_tag = root_tag
        self.ignored_tags = ignored_tags or set()
        self._capturing = False
        self._open_tags: list[str] = []
        # Stack depth of the outermost ignored element; zero means visible.
        self._ignored_depth = 0
        self._out: list[str] = []

    def get_html(self) -> str:
        return "".join(self._out).strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == self.root_tag and not self._capturing:
            self._capturing = True
            self._open_tags.append(tag)
            self._out.append(self.get_starttag_text() or f"<{tag}>")
            return

        if not self._capturing:
            return

        if tag not in _VOID_TAGS:
            self._open_tags.append(tag)
        if self._ignored_depth:
            return
        if tag in self.ignored_tags:
            if tag not in _VOID_TAGS:
                self._ignored_depth = len(self._open_tags)
            return

        self._out.append(self.get_starttag_text() or f"<{tag}>")

    def handle_endtag(self, tag: str) -> None:
        if not self._capturing or tag not in self._open_tags:
            return

        # An ancestor end tag also closes descendants with omitted end tags.
        index = len(self._open_tags) - 1 - self._open_tags[::-1].index(tag)
        if not self._ignored_depth or index < self._ignored_depth - 1:
            self._out.append(f"</{tag}>")
        del self._open_tags[index:]
        if len(self._open_tags) < self._ignored_depth:
            self._ignored_depth = 0
        if not self._open_tags:
            self._capturing = False

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self._capturing:
            return
        if self._ignored_depth or tag in self.ignored_tags:
            return
        self._out.append(self.get_starttag_text() or f"<{tag} />")

    def handle_data(self, data: str) -> None:
        if not self._capturing or self._ignored_depth:
            return
        self._out.append(escape(data, quote=False))


def extract_first_tag_subtree(html: str, tags: tuple[str, ...], ignored_tags: set[str] | None = None) -> str:
    for tag in tags:
        parser = SubtreeHTMLExtractor(tag, ignored_tags=ignored_tags)
        parser.feed(html)
        extracted = parser.get_html()
        if extracted:
            return extracted
    return html


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
