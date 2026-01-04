from .core.loader import Loader
from .youtube import check_youtube_url
from .ytdlp import YtdlpLoader


class YoutubeYtdlpLoader(Loader):
    def __init__(self) -> None:
        self.ytdlp_loader = YtdlpLoader()

    def load_sync(self, url: str) -> str:
        check_youtube_url(url)
        return self.ytdlp_loader.load_sync(url)
