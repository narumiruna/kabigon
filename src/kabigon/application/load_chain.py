from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass

from kabigon.domain.errors import LoaderContentError
from kabigon.domain.errors import LoaderError
from kabigon.domain.errors import LoaderNotApplicableError
from kabigon.domain.errors import LoaderTimeoutError
from kabigon.domain.errors import MissingRequirementError
from kabigon.domain.loader import Loader
from kabigon.infrastructure.registry import get_loader_factory

from .loader_names import DEFAULT_FALLBACK_LOADERS
from .pipeline_catalog import ContentType
from .pipeline_catalog import FallbackPolicy
from .pipeline_catalog import match_pipeline

LoaderFactory = Callable[[], Loader]
_EMPTY_EXECUTION_PLAN = "Load chain execution plan cannot be empty."

logger = logging.getLogger(__name__)


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
    loaders: tuple[Loader, ...]
    explanation: LoadChainExplanation

    async def load(self) -> str:
        errors: list[str] = []

        for loader in self.loaders:
            loader_name = loader.__class__.__name__
            logger.debug("[%s] Attempting to load URL: %s", loader_name, self.explanation.url)

            try:
                result = await loader.load(self.explanation.url)
            except LoaderNotApplicableError as e:
                logger.debug("[%s] Not applicable: %s", loader_name, e.reason)
                errors.append(f"{loader_name}: Not applicable ({e.reason})")
                continue
            except LoaderTimeoutError as e:
                logger.warning("[%s] Timeout after %ss: %s", loader_name, e.timeout, e.url)
                errors.append(f"{loader_name}: Timeout after {e.timeout}s")
                continue
            except LoaderContentError as e:
                logger.warning("[%s] Content extraction failed: %s", loader_name, e.reason)
                errors.append(f"{loader_name}: Content extraction failed - {e.reason}")
                continue
            except Exception as e:  # noqa: BLE001
                logger.info("[%s] Failed with error: %s: %s", loader_name, type(e).__name__, e)
                errors.append(f"{loader_name}: {type(e).__name__}: {e!s}")
                continue

            if not result:
                logger.info("[%s] Got empty result", loader_name)
                errors.append(f"{loader_name}: Empty result")
                continue

            logger.info("[%s] Successfully loaded URL: %s", loader_name, self.explanation.url)
            return result

        if errors:
            error_details = "\n  - ".join(errors)
            logger.error("Failed to load URL: %s\n\nAttempted loaders:\n  - %s", self.explanation.url, error_details)
        else:
            logger.error("Failed to load URL: %s", self.explanation.url)

        raise LoaderError(self.explanation.url, details=errors)

    def load_sync(self) -> str:
        return asyncio.run(self.load())


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


def _build_loaders(
    loader_names: tuple[str, ...],
    get_factory: Callable[[str], LoaderFactory] = get_loader_factory,
) -> tuple[Loader, ...]:
    if not loader_names:
        raise ValueError(_EMPTY_EXECUTION_PLAN)

    return tuple(get_factory(name)() for name in loader_names)


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
    return LoadChain(loaders=_build_loaders(explanation.execution_plan), explanation=explanation)


def resolve_explicit_load_chain(
    url: str,
    loader_names: Sequence[str],
    get_factory: Callable[[str], LoaderFactory] = get_loader_factory,
) -> LoadChain:
    execution_plan = tuple(loader_names)
    explanation = LoadChainExplanation(
        url=url,
        pipeline=None,
        content_type=ContentType.GENERIC_WEB,
        targeted_loaders=(),
        execution_plan=execution_plan,
    )
    return LoadChain(loaders=_build_loaders(execution_plan, get_factory), explanation=explanation)


__all__ = [
    "DEFAULT_FALLBACK_LOADERS",
    "LoadChain",
    "LoadChainExplanation",
    "explain_load_chain",
    "resolve_explicit_load_chain",
    "resolve_load_chain",
]
