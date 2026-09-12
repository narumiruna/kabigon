from __future__ import annotations

import logging
from collections.abc import Set as AbstractSet
from html import escape
from html.parser import HTMLParser

from kabigon.core.errors import LoaderContentError
from kabigon.core.loader import Loader
from kabigon.core.resources import Browser
from kabigon.core.resources import CurlSession
from kabigon.core.resources import HttpClient
from kabigon.core.resources import ResourceProvider
from kabigon.sources.applicability import parse_ltn_target

from .html_extractors import extract_article_body_from_json_ld
from .news_article import DEFAULT_NEWS_ARTICLE_HEADERS
from .news_article import load_news_article
from .utils import html_to_markdown

logger = logging.getLogger(__name__)

_LTN_ARTICLE_CLASSES = {"text", "boxTitle", "boxText"}
_IGNORED_TAGS = {"script", "style", "noscript", "svg"}
_IGNORED_CLASSES = {"adHeight250", "adHeight280", "after_ir", "appE1121", "before_ir", "suggest_m", "suggest_pc"}
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


class _FirstDivWithClassesExtractor(HTMLParser):
    def __init__(self, required_classes: set[str], ignored_tags: set[str] | None = None) -> None:
        super().__init__(convert_charrefs=True)
        self.required_classes = required_classes
        self.ignored_tags = ignored_tags or set()
        self._capturing = False
        self._depth = 0
        self._ignored_depth = 0
        self._out: list[str] = []

    def get_html(self) -> str:
        return "".join(self._out).strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        classes = set((attr_map.get("class") or "").split())

        if tag == "div" and not self._capturing and self.required_classes <= classes:
            self._capturing = True
            self._depth = 1
            self._out.append(self.get_starttag_text() or "<div>")
            return

        if not self._capturing:
            return

        if self._ignored_depth:
            if tag not in _VOID_TAGS:
                self._ignored_depth += 1
            return

        if self._should_ignore_subtree(tag, attr_map, classes):
            if tag not in _VOID_TAGS:
                self._ignored_depth = 1
            return

        self._out.append(self.get_starttag_text() or f"<{tag}>")
        if tag not in _VOID_TAGS:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self._capturing:
            return

        if self._ignored_depth:
            if tag not in _VOID_TAGS:
                self._ignored_depth -= 1
            return

        self._out.append(f"</{tag}>")
        if tag not in _VOID_TAGS:
            self._depth -= 1

        if self._depth <= 0:
            self._capturing = False

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        classes = set((attr_map.get("class") or "").split())
        if not self._capturing or self._ignored_depth or self._should_ignore_subtree(tag, attr_map, classes):
            return
        self._out.append(self.get_starttag_text() or f"<{tag} />")

    def _should_ignore_subtree(self, tag: str, attrs: dict[str, str | None], classes: AbstractSet[str]) -> bool:
        element_id = attrs.get("id") or ""
        return tag in self.ignored_tags or element_id.startswith("ad-") or bool(classes & _IGNORED_CLASSES)

    def handle_data(self, data: str) -> None:
        if not self._capturing or self._ignored_depth:
            return
        self._out.append(escape(data, quote=False))


def extract_ltn_article_html(html: str) -> str:
    parser = _FirstDivWithClassesExtractor(_LTN_ARTICLE_CLASSES, ignored_tags=_IGNORED_TAGS)
    parser.feed(html)
    return parser.get_html()


def extract_ltn_article_text(html: str, url: str, loader_name: str) -> str:
    article_html = extract_ltn_article_html(html)
    if article_html:
        return html_to_markdown(article_html)
    json_ld_body = extract_article_body_from_json_ld(html)
    if json_ld_body:
        return json_ld_body
    raise LoaderContentError(loader_name, url, "Could not find LTN article body")


class LTNLoader(Loader):
    def __init__(
        self,
        headers: dict[str, str] | None = None,
        http_client: HttpClient | None = None,
        curl_session: CurlSession | None = None,
        browser: Browser | None = None,
        resource_provider: ResourceProvider | None = None,
    ) -> None:
        self.headers = headers or DEFAULT_NEWS_ARTICLE_HEADERS
        self.http_client = http_client
        self.curl_session = curl_session
        self.browser = browser
        self.resource_provider = resource_provider

    async def load(self, url: str) -> str:
        return await load_news_article(
            url,
            loader_name="LTNLoader",
            registry_id="ltn",
            validate_url=parse_ltn_target,
            headers=self.headers,
            extractor=extract_ltn_article_text,
            http_client=self.http_client,
            curl_session=self.curl_session,
            browser=self.browser,
            resource_provider=self.resource_provider,
        )
