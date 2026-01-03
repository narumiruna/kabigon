import typer
from rich import print

from .api import load_url_sync


def run(url: str) -> None:
    result = load_url_sync(url)
    print(result)


def main() -> None:
    typer.run(run)
