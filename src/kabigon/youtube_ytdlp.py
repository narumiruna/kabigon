from urllib.parse import urlparse

from .loader import Loader
from .ytdlp import YtdlpLoader


def check_youtube_url(url: str) -> None:
    if urlparse(url).netloc not in ["youtube.com", "youtu.be"]:
        raise ValueError(f"URL must be from youtube.com or youtu.be, got {url}")


class YoutubeYtdlpLoader(Loader):
    def __init__(self) -> None:
        self.ytdlp_loader = YtdlpLoader()

    def load(self, url: str) -> str:
        check_youtube_url(url)
        return self.ytdlp_loader.load(url)
