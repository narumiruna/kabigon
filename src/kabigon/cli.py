import click
from rich import print

from .pipeline import PipelineLoader


@click.command()
@click.argument("url", type=click.STRING)
def main(url: str) -> None:
    loader = PipelineLoader().load(url)
    print(loader)
