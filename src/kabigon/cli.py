import typer
from rich import print

from .compose import Compose
from .pdf import PDFLoader
from .playwright import PlaywrightLoader
from .ptt import PttLoader
from .reel import ReelLoader
from .twitter import TwitterLoader
from .youtube import YoutubeLoader


def run(url: str) -> None:
    loader = Compose(
        [
            PttLoader(),
            TwitterLoader(),
            YoutubeLoader(),
            ReelLoader(),
            PDFLoader(),
            PlaywrightLoader(),
        ]
    )
    result = loader.load(url)
    print(result)


def main() -> None:
    typer.run(run)
