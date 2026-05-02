from __future__ import annotations

import os
from dataclasses import dataclass

from kabigon.domain.errors import MissingRequirementError
from kabigon.domain.loader import Loader
from kabigon.infrastructure.registry import get_loader_factory
from kabigon.loaders.compose import Compose

from .loader_names import DEFAULT_FALLBACK_LOADERS
from .pipeline_catalog import ContentType
from .pipeline_catalog import FallbackPolicy
from .pipeline_catalog import match_pipeline


@dataclass(frozen=True)
class LoadChainExplanation:
    url: str
    pipeline: str | None
    content_type: ContentType
    targeted_loaders: tuple[str, ...]
    execution_plan: tuple[str, ...]
    requirements: tuple[str, ...] = ()
    missing_requirements: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "url": self.url,
            "pipeline": self.pipeline,
            "content_type": self.content_type,
            "targeted_loaders": list(self.targeted_loaders),
            "execution_plan": list(self.execution_plan),
            "requirements": list(self.requirements),
            "missing_requirements": list(self.missing_requirements),
        }


@dataclass(frozen=True)
class LoadChain:
    loader: Loader
    explanation: LoadChainExplanation


def _merge_unique_loaders(primary: tuple[str, ...], fallback: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []

    for loader_name in (*primary, *fallback):
        if loader_name in seen:
            continue
        seen.add(loader_name)
        ordered.append(loader_name)

    return tuple(ordered)


def _missing_requirements(requirements: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(name for name in requirements if not os.getenv(name))


def _ensure_requirements(explanation: LoadChainExplanation) -> None:
    if not explanation.missing_requirements:
        return

    raise MissingRequirementError(explanation.missing_requirements)


def _build_loader(loader_names: tuple[str, ...]) -> Loader:
    loaders = [get_loader_factory(name)() for name in loader_names]
    if len(loaders) == 1:
        return loaders[0]
    return Compose(loaders)


def explain_load_chain(url: str) -> LoadChainExplanation:
    pipeline = match_pipeline(url)

    pipeline_name: str | None = None
    content_type = ContentType.GENERIC_WEB
    targeted_loaders: tuple[str, ...] = ()
    requirements: tuple[str, ...] = ()
    fallback = DEFAULT_FALLBACK_LOADERS

    if pipeline is not None:
        pipeline_name = pipeline.name
        content_type = pipeline.content_type
        targeted_loaders = pipeline.targeted_loaders
        requirements = pipeline.requirements
        if pipeline.fallback_policy == FallbackPolicy.NO_FALLBACK:
            fallback = ()

    execution_plan = _merge_unique_loaders(targeted_loaders, fallback)
    return LoadChainExplanation(
        url=url,
        pipeline=pipeline_name,
        content_type=content_type,
        targeted_loaders=targeted_loaders,
        execution_plan=execution_plan,
        requirements=requirements,
        missing_requirements=_missing_requirements(requirements),
    )


def resolve_load_chain(url: str) -> LoadChain:
    explanation = explain_load_chain(url)
    _ensure_requirements(explanation)
    return LoadChain(loader=_build_loader(explanation.execution_plan), explanation=explanation)


__all__ = ["DEFAULT_FALLBACK_LOADERS", "LoadChain", "LoadChainExplanation", "explain_load_chain", "resolve_load_chain"]
