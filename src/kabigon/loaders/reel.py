from kabigon.core.loader import Loader
from kabigon.sources.applicability import parse_reel_target

from .httpx import HttpxLoader
from .ytdlp import YtdlpLoader


def check_reel_url(url: str) -> None:
    parse_reel_target(url)


class ReelLoader(Loader):
    def __init__(self) -> None:
        self.httpx_loader = HttpxLoader()
        self.ytdlp_loader = YtdlpLoader()

    async def load(self, url: str) -> str:
        parse_reel_target(url)

        audio_content = await self.ytdlp_loader.load(url)
        html_content = await self.httpx_loader.load(url)

        return f"{audio_content}\n\n{html_content}"
