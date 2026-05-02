from __future__ import annotations

from kabigon.core.loader import Loader
from kabigon.sources.applicability import parse_cnn_target

from .news_article import DEFAULT_NEWS_ARTICLE_HEADERS
from .news_article import load_news_article


def check_cnn_url(url: str) -> None:
    parse_cnn_target(url)


class CNNLoader(Loader):
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers or DEFAULT_NEWS_ARTICLE_HEADERS

    async def load(self, url: str) -> str:
        return await load_news_article(url, loader_name="CNNLoader", validate_url=check_cnn_url, headers=self.headers)
