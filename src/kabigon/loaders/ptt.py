import logging

from kabigon.core.loader import Loader
from kabigon.sources.applicability import parse_ptt_target

from .httpx import HttpxLoader

logger = logging.getLogger(__name__)


def check_ptt_url(url: str) -> None:
    parse_ptt_target(url)


class PttLoader(Loader):
    def __init__(self) -> None:
        self.httpx_loader = HttpxLoader(
            headers={
                "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8,en-US;q=0.7,en;q=0.6",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",  # noqa
                "Cookie": "over18=1",
            }
        )

    async def load(self, url: str) -> str:
        logger.info("[PttLoader] Processing URL: %s", url)
        parse_ptt_target(url)

        logger.info("[PttLoader] Fetching PTT HTML content")
        result = await self.httpx_loader.load(url)
        logger.info("[PttLoader] Extracted PTT content (%s chars)", len(result))
        return result
