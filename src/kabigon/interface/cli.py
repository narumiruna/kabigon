from __future__ import annotations

from collections.abc import Callable
from typing import NoReturn

import typer

from kabigon.application.service import load_url_sync
from kabigon.domain.loader import Loader
from kabigon.infrastructure.registry import get_cli_loader_defs
from kabigon.loaders.compose import Compose

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


def _print_loader_list() -> None:
    for name, description, _factory in LOADER_DEFS:
        typer.echo(f"{name} - {description}")


def _load_with_loader_names(url: str, loader_names: list[str]) -> str:
    registry = _loader_registry()
    chain = [registry[name]() for name in loader_names]
    if len(chain) == 1:
        return chain[0].load_sync(url)
    return Compose(chain).load_sync(url)


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

    if loader is None:
        typer.echo(load_url_sync(url))
        return

    names = _parse_loader_names(loader)
    typer.echo(_load_with_loader_names(url, names))


def run(url: str) -> None:
    typer.echo(load_url_sync(url))


def main() -> None:
    app()
