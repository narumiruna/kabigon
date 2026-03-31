import logging

from kabigon.domain.loader import Loader

from .httpx import HttpxLoader
from .url_match import ensure_host_in

logger = logging.getLogger(__name__)


def check_ptt_url(url: str) -> None:
    ensure_host_in(url, ["www.ptt.cc"], loader_name="PttLoader", source_name="PTT")


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
        logger.debug("[PttLoader] Processing URL: %s", url)
        check_ptt_url(url)

        result = await self.httpx_loader.load(url)
        logger.debug("[PttLoader] Successfully loaded content (%s chars)", len(result))
        return result
