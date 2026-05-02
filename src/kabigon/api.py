"""Public Python interface for loading URL content."""

from kabigon.load_chain import explain_load_chain
from kabigon.load_chain import resolve_load_chain
from kabigon.loader_registry import list_loader_names


def load_url_sync(url: str) -> str:
    return resolve_load_chain(url).load_sync()


async def load_url(url: str) -> str:
    return await resolve_load_chain(url).load()


def available_loaders() -> list[str]:
    return list_loader_names()


def explain_plan(url: str) -> dict[str, object]:
    return explain_load_chain(url).as_dict()


__all__ = ["available_loaders", "explain_plan", "load_url", "load_url_sync"]
