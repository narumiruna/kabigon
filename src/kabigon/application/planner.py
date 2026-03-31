from __future__ import annotations

from kabigon.domain.models import LoaderPlan
from kabigon.domain.models import RetrievalStrategy


def _merge_unique_loaders(primary: tuple[str, ...], fallback: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []

    for loader_name in primary:
        if loader_name in seen:
            continue
        seen.add(loader_name)
        ordered.append(loader_name)

    for loader_name in fallback:
        if loader_name in seen:
            continue
        seen.add(loader_name)
        ordered.append(loader_name)

    return tuple(ordered)


def build_loader_plan(strategy: RetrievalStrategy, default_fallback: tuple[str, ...]) -> LoaderPlan:
    return LoaderPlan(
        loader_names=_merge_unique_loaders(
            primary=strategy.primary_loaders,
            fallback=default_fallback,
        )
    )
