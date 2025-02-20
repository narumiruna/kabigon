import click
from rich import print

from .compose import Compose
from .httpx import HttpxLoader
from .pdf import PDFLoader
from .reel import ReelLoader
from .singlefile import SinglefileLoader
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
            SinglefileLoader(),
        ]
    )
    result = loader.load(url)
    print(result)
