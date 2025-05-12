from urllib.parse import urlparse

from aioytt.video_id import ALLOWED_NETLOCS
from aioytt.video_id import ALLOWED_SCHEMES

from .loader import Loader
from .ytdlp import YtdlpLoader


def check_youtube_url(url: str) -> None:
    schema = urlparse(url).scheme
    if schema not in ALLOWED_SCHEMES:
        raise ValueError(f"URL scheme is not allowed: {schema}")

    domain = urlparse(url).netloc
    if domain not in ALLOWED_NETLOCS:
        raise ValueError(f"URL domain is not allowed: {domain}")


class YoutubeYtdlpLoader(Loader):
    def __init__(self) -> None:
        self.ytdlp_loader = YtdlpLoader()

    def load(self, url: str) -> str:
        check_youtube_url(url)
        return self.ytdlp_loader.load(url)
