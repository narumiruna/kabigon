"""Public Python interface for loading URL content."""

from __future__ import annotations

import asyncio

from kabigon.client import KabigonClient
from kabigon.core.results import LoadResult
from kabigon.load_chain import explain_load_chain
from kabigon.loader_registry import list_loader_names


async def load_url_detailed(url: str, *, deadline: float | None = None) -> LoadResult:
    async with KabigonClient(deadline=deadline) as client:
        return await client.load_url_detailed(url)


async def load_url(url: str, *, deadline: float | None = None) -> str:
    return (await load_url_detailed(url, deadline=deadline)).content


def load_url_sync(url: str, *, deadline: float | None = None) -> str:
    return asyncio.run(load_url(url, deadline=deadline))


def available_loaders() -> list[str]:
    return list_loader_names()


def explain_plan(url: str) -> dict[str, object]:
    return explain_load_chain(url).as_dict()


__all__ = ["available_loaders", "explain_plan", "load_url", "load_url_detailed", "load_url_sync"]
