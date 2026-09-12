from __future__ import annotations

from kabigon.core.loader import Loader
from kabigon.core.resources import Browser
from kabigon.core.resources import CurlSession
from kabigon.core.resources import HttpClient
from kabigon.core.resources import ResourceProvider
from kabigon.sources.applicability import parse_bbc_target

from .news_article import DEFAULT_NEWS_ARTICLE_HEADERS
from .news_article import load_news_article


class BBCLoader(Loader):
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
            loader_name="BBCLoader",
            registry_id="bbc",
            validate_url=parse_bbc_target,
            headers=self.headers,
            http_client=self.http_client,
            curl_session=self.curl_session,
            browser=self.browser,
            resource_provider=self.resource_provider,
        )
