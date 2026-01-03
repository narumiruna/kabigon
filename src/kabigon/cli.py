import typer
from rich import print

from .compose import Compose
from .pdf import PDFLoader
from .playwright import PlaywrightLoader
from .ptt import PttLoader
from .reddit import RedditLoader
from .reel import ReelLoader
from .truthsocial import TruthSocialLoader
from .twitter import TwitterLoader
from .youtube import YoutubeLoader
from .youtube_ytdlp import YoutubeYtdlpLoader


def run(url: str) -> None:
    loader = Compose(
        [
            PttLoader(),
            TwitterLoader(),
            TruthSocialLoader(),
            RedditLoader(),
            YoutubeLoader(),
            ReelLoader(),
            YoutubeYtdlpLoader(),
            PDFLoader(),
            PlaywrightLoader(timeout=50_000, wait_until="networkidle"),
            PlaywrightLoader(timeout=10_000),
        ]
    )
    result = loader.load_sync(url)
    print(result)


def main() -> None:
    typer.run(run)
