from __future__ import annotations

from kabigon.infrastructure.registry import list_loader_names

from .load_chain import explain_load_chain
from .load_chain import resolve_load_chain


def load_url_sync(url: str) -> str:
    return resolve_load_chain(url).load_sync()


async def load_url(url: str) -> str:
    return await resolve_load_chain(url).load()


def available_loaders() -> list[str]:
    return list_loader_names()


def explain_plan(url: str) -> dict[str, object]:
    return explain_load_chain(url).as_dict()
