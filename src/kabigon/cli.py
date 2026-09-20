from __future__ import annotations

import argparse
import logging
from collections.abc import Callable
from collections.abc import Sequence
from typing import cast

from kabigon.api import load_url_sync
from kabigon.core.loader import Loader
from kabigon.load_chain import resolve_explicit_load_chain
from kabigon.loader_registry import LoaderDef
from kabigon.loader_registry import list_loader_defs

LoaderFactory = Callable[[], Loader]
LOADER_DEFS: list[LoaderDef] = list(list_loader_defs(cli_visible=True))
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d - %(message)s"


def _loader_registry() -> dict[str, LoaderFactory]:
    return {definition.name: definition.factory for definition in LOADER_DEFS}


def _loader_requirements() -> dict[str, tuple[str, ...]]:
    return {definition.name: definition.requirements for definition in LOADER_DEFS}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kabigon")
    parser.add_argument("url", nargs="?", metavar="URL")
    parser.add_argument("--loader", help="Comma-separated loader names")
    parser.add_argument("--list", action="store_true", dest="list_", help="List supported loaders")
    parser.add_argument("--verbose", action="store_true", help="Show debug logging")
    return parser


def _parse_loader_names(raw: str, parser: argparse.ArgumentParser) -> list[str]:
    names = [name.strip() for name in raw.split(",") if name.strip()]
    if not names:
        parser.error("Loader list cannot be empty.")
    registry = _loader_registry()
    unknown = [name for name in names if name not in registry]
    if unknown:
        parser.error(f"Unknown loader(s): {', '.join(unknown)}. Use --list to see supported loaders.")
    return names


def _print_loader_list() -> None:
    for definition in LOADER_DEFS:
        print(f"{definition.name} - {definition.description}")


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG if verbose else logging.INFO)


def _load_with_loader_names(url: str, loader_names: list[str]) -> str:
    registry = _loader_registry()
    requirements = _loader_requirements()
    return resolve_explicit_load_chain(url, loader_names, registry.__getitem__, requirements.__getitem__).load_sync()


def run(url: str) -> None:
    print(load_url_sync(url))


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    url = cast("str | None", args.url)
    loader = cast("str | None", args.loader)
    list_ = cast("bool", args.list_)
    verbose = cast("bool", args.verbose)
    _configure_logging(verbose)

    if list_:
        if url is not None or loader is not None:
            parser.error("--list cannot be combined with URL or --loader.")
        _print_loader_list()
        return
    if url is None:
        parser.error("URL is required unless --list is used.")
    if loader is None:
        print(load_url_sync(url))
        return
    names = _parse_loader_names(loader, parser)
    print(_load_with_loader_names(url, names))
