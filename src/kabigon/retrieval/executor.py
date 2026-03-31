from __future__ import annotations

from kabigon import loaders
from kabigon.core.loader import Loader
from kabigon.core.models import LoaderPlan
from kabigon.loader_registry import get_loader_factory


def instantiate_loaders(loader_names: tuple[str, ...]) -> list[Loader]:
    return [get_loader_factory(name)() for name in loader_names]


def build_loader(plan: LoaderPlan) -> Loader:
    loader_chain = instantiate_loaders(plan.loader_names)
    if len(loader_chain) == 1:
        return loader_chain[0]
    return loaders.Compose(loader_chain)
