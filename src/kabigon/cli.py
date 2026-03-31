from __future__ import annotations

from collections.abc import Callable
from typing import NoReturn

import typer

from kabigon import loaders
from kabigon.api import load_url_sync
from kabigon.core.loader import Loader
from kabigon.loader_registry import get_cli_loader_defs

LoaderFactory = Callable[[], Loader]
LoaderDef = tuple[str, str, LoaderFactory]

LOADER_DEFS: list[LoaderDef] = get_cli_loader_defs()

app = typer.Typer(add_completion=False)


def _loader_registry() -> dict[str, LoaderFactory]:
    return {name: factory for name, _description, factory in LOADER_DEFS}


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


def _load_with_loader_names(names: list[str], url: str) -> str:
    registry = _loader_registry()
    loaders_chain = [registry[name]() for name in names]
    if len(loaders_chain) == 1:
        return loaders_chain[0].load_sync(url)
    return loaders.Compose(loaders_chain).load_sync(url)


def _print_loader_list() -> None:
    for name, description, _factory in LOADER_DEFS:
        typer.echo(f"{name} - {description}")


@app.callback(invoke_without_command=True)
def _main(
    url: str | None = typer.Argument(None, metavar="URL"),
    loader: str | None = typer.Option(None, "--loader", help="Comma-separated loader names"),
    list_: bool = typer.Option(False, "--list", help="List supported loaders"),
) -> None:
    if list_:
        if url is not None or loader is not None:
            _exit_with_error("--list cannot be combined with URL or --loader.")
        _print_loader_list()
        return

    if url is None:
        _exit_with_error("URL is required unless --list is used.")

    assert url is not None

    if loader is None:
        result = load_url_sync(url)
        typer.echo(result)
        return

    names = _parse_loader_names(loader)
    result = _load_with_loader_names(names, url)
    typer.echo(result)


def run(url: str) -> None:
    result = load_url_sync(url)
    typer.echo(result)


def main() -> None:
    app()
