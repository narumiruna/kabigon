import timeout_decorator

from .httpx import HttpxLoader
from .loader import Loader
from .loader import LoaderError
from .ytdlp import YtdlpLoader


def is_reel_url(url: str) -> bool:
    return url.startswith("https://www.instagram.com/reel")


class NotReelURLError(LoaderError):
    def __init__(self, url: str):
        super().__init__(f"URL is not an Instagram Reel: {url}")


class ReelLoader(Loader):
    def __init__(self) -> None:
        self.httpx_loader = HttpxLoader()
        self.ytdlp_loader = YtdlpLoader()

    @timeout_decorator.timeout(300)
    def load(self, url: str) -> str:
        if not is_reel_url(url):
            raise NotReelURLError(url)

        audio_content = self.ytdlp_loader.load(url)
        html_content = self.httpx_loader.load(url)

        return f"{audio_content}\n\n{html_content}"
