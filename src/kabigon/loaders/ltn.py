from __future__ import annotations

import logging

from kabigon.core.errors import LoaderContentError
from kabigon.core.loader import Loader
from kabigon.core.resources import Browser
from kabigon.core.resources import CurlSession
from kabigon.core.resources import HttpClient
from kabigon.core.resources import ResourceProvider
from kabigon.sources.applicability import parse_ltn_target

from .html_extractors import SubtreeHTMLExtractor
from .html_extractors import extract_article_body_from_json_ld
from .news_article import DEFAULT_NEWS_ARTICLE_HEADERS
from .news_article import load_news_article
from .utils import html_to_markdown

logger = logging.getLogger(__name__)

_LTN_ARTICLE_CLASSES = {"text", "boxTitle", "boxText"}
_IGNORED_TAGS = {"script", "style", "noscript", "svg"}
_IGNORED_CLASSES = {"adHeight250", "adHeight280", "after_ir", "appE1121", "before_ir", "suggest_m", "suggest_pc"}


class _LTNArticleExtractor(SubtreeHTMLExtractor):
    def __init__(self) -> None:
        super().__init__("div", ignored_tags=_IGNORED_TAGS)

    def _matches_root(self, tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        classes = set((dict(attrs).get("class") or "").split())
        return tag == self.root_tag and classes >= _LTN_ARTICLE_CLASSES

    def _should_ignore_subtree(self, tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        attr_map = dict(attrs)
        classes = set((attr_map.get("class") or "").split())
        element_id = attr_map.get("id") or ""
        return (
            super()._should_ignore_subtree(tag, attrs)
            or element_id.startswith("ad-")
            or bool(classes & _IGNORED_CLASSES)
        )


def extract_ltn_article_html(html: str) -> str:
    parser = _LTNArticleExtractor()
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
