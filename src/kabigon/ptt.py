from urllib.parse import urlparse

from .errors import NotTwitterURLError
from .httpx import HttpxLoader
from .loader import Loader


def is_ptt_url(url: str) -> bool:
    return urlparse(url).netloc == "www.ptt.cc"


class PttLoader(Loader):
    def __init__(self) -> None:
        self.httpx_loader = HttpxLoader(
            headers={
                "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8,en-US;q=0.7,en;q=0.6",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",  # noqa
                "Cookie": "over18=1",
            }
        )

    def load(self, url: str) -> str:
        if not is_ptt_url(url):
            raise NotTwitterURLError(url)

        return self.httpx_loader.load(url)

    async def async_load(self, url: str):
        if not is_ptt_url(url):
            raise NotTwitterURLError(url)

        return await self.httpx_loader.async_load(url)
