from kabigon.core.exception import InvalidURLError
from kabigon.core.loader import Loader

from .httpx import HttpxLoader
from .ytdlp import YtdlpLoader


def check_reel_url(url: str) -> None:
    if not url.startswith("https://www.instagram.com/reel"):
        raise InvalidURLError(url, "Instagram Reel")


class ReelLoader(Loader):
    def __init__(self) -> None:
        self.httpx_loader = HttpxLoader()
        self.ytdlp_loader = YtdlpLoader()

    async def load(self, url: str) -> str:
        check_reel_url(url)

        audio_content = await self.ytdlp_loader.load(url)
        html_content = await self.httpx_loader.load(url)

        return f"{audio_content}\n\n{html_content}"
