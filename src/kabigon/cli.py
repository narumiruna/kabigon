import click
from rich import print

from .compose import Compose
from .pdf import PDFLoader
from .playwright import PlaywrightLoader
from .ptt import PttLoader
from .reel import ReelLoader
from .twitter import TwitterLoader
from .youtube import YoutubeLoader
from .ytdlp import YtdlpLoader


@click.command()
@click.argument("url", type=click.STRING)
def main(url: str) -> None:
    loader = Compose(
        [
            PttLoader(),
            TwitterLoader(),
            YoutubeLoader(),
            ReelLoader(),
            YtdlpLoader(),
            PDFLoader(),
            PlaywrightLoader(),
        ]
    )
    result = loader.load(url)
    print(result)
