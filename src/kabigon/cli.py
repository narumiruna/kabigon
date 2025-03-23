import click
from rich import print

from .compose import Compose
from .httpx import HttpxLoader
from .pdf import PDFLoader
from .playwright import PlaywrightLoader
from .reel import ReelLoader
from .youtube import YoutubeLoader
from .ytdlp import YtdlpLoader


@click.command()
@click.argument("url", type=click.STRING)
def main(url: str) -> None:
    loader = Compose(
        [
            YoutubeLoader(),
            ReelLoader(),
            YtdlpLoader(),
            PDFLoader(),
            HttpxLoader(),
            PlaywrightLoader(),
        ]
    )
    result = loader.load(url)
    print(result)
