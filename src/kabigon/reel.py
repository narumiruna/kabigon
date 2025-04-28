from .errors import NotReelURLError
from .httpx import HttpxLoader
from .loader import Loader
from .ytdlp import YtdlpLoader


def is_reel_url(url: str) -> bool:
    return url.startswith("https://www.instagram.com/reel")


class ReelLoader(Loader):
    def __init__(self) -> None:
        self.httpx_loader = HttpxLoader()
        self.ytdlp_loader = YtdlpLoader()

    def load(self, url: str) -> str:
        if not is_reel_url(url):
            raise NotReelURLError(url)

        audio_content = self.ytdlp_loader.load(url)
        html_content = self.httpx_loader.load(url)

        return f"{audio_content}\n\n{html_content}"

    async def async_load(self, url: str):
        if not is_reel_url(url):
            raise NotReelURLError(url)

        audio_content = await self.ytdlp_loader.async_load(url)
        html_content = await self.httpx_loader.async_load(url)

        return f"{audio_content}\n\n{html_content}"
