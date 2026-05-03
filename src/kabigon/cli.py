from __future__ import annotations

import logging
from collections.abc import Callable
from typing import NoReturn

import typer

from kabigon import loader_registry
from kabigon.api import load_url_sync
from kabigon.core.loader import Loader
from kabigon.load_chain import resolve_explicit_load_chain
from kabigon.loader_registry import get_loader_description
from kabigon.loader_registry import get_loader_factory
from kabigon.loader_registry import get_loader_requirements

LoaderFactory = Callable[[], Loader]
LoaderDef = tuple[str, str, LoaderFactory, tuple[str, ...]]

CLI_VISIBLE_LOADERS = (
    loader_registry.PLAYWRIGHT,
    loader_registry.HTTPX,
    loader_registry.BBC,
    loader_registry.CNN,
    loader_registry.FIRECRAWL,
    loader_registry.YOUTUBE,
    loader_registry.YOUTUBE_YTDLP,
    loader_registry.YTDLP,
    loader_registry.TWITTER,
    loader_registry.TRUTHSOCIAL,
    loader_registry.REDDIT,
    loader_registry.PTT,
    loader_registry.REEL,
    loader_registry.GITHUB,
    loader_registry.PDF,
)

LOADER_DEFS: list[LoaderDef] = [
    (name, get_loader_description(name), get_loader_factory(name), get_loader_requirements(name))
    for name in CLI_VISIBLE_LOADERS
]

app = typer.Typer(add_completion=False)
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d - %(message)s"


def _loader_registry() -> dict[str, LoaderFactory]:
    return {name: factory for name, _description, factory, _requirements in LOADER_DEFS}


def _loader_requirements() -> dict[str, tuple[str, ...]]:
    return {name: requirements for name, _description, _factory, requirements in LOADER_DEFS}


def _exit_with_error(message: str) -> NoReturn:
    typer.echo(message)
    raise typer.Exit(code=2)


def _parse_loader_names(raw: str) -> list[str]:
    names = [name.strip() for name in raw.split(",") if name.strip()]
    if not names:
        _exit_with_error("Loader list cannot be empty.")
    registry = _loader_registry()
    unknown = [name for name in names if name not in registry]
    if unknown:
        hint = ", ".join(unknown)
        _exit_with_error(f"Unknown loader(s): {hint}. Use --list to see supported loaders.")
    return names


def _print_loader_list() -> None:
    for name, description, _factory, _requirements in LOADER_DEFS:
        typer.echo(f"{name} - {description}")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format=LOG_FORMAT, level=level)


def _load_with_loader_names(url: str, loader_names: list[str]) -> str:
    registry = _loader_registry()
    requirements = _loader_requirements()
    return resolve_explicit_load_chain(url, loader_names, registry.__getitem__, requirements.__getitem__).load_sync()


@app.callback(invoke_without_command=True)
def _main(
    url: str | None = typer.Argument(None, metavar="URL"),
    loader: str | None = typer.Option(None, "--loader", help="Comma-separated loader names"),
    list_: bool = typer.Option(False, "--list", help="List supported loaders"),
    verbose: bool = typer.Option(False, "--verbose", help="Show debug logging"),
) -> None:
    _configure_logging(verbose)

    if list_:
        if url is not None or loader is not None:
            _exit_with_error("--list cannot be combined with URL or --loader.")
        _print_loader_list()
        return

    if url is None:
        _exit_with_error("URL is required unless --list is used.")

    if loader is None:
        typer.echo(load_url_sync(url))
        return

    names = _parse_loader_names(loader)
    typer.echo(_load_with_loader_names(url, names))


def run(url: str) -> None:
    typer.echo(load_url_sync(url))


def main() -> None:
    app()
