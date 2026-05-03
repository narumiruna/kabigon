from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass

from kabigon import loader_registry
from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderError
from kabigon.core.errors import LoaderNotApplicableError
from kabigon.core.errors import LoaderTimeoutError
from kabigon.core.errors import MissingRequirementError
from kabigon.core.loader import Loader
from kabigon.loader_registry import get_loader_factory
from kabigon.loader_registry import get_loader_requirements
from kabigon.pipelines.catalog import ContentType
from kabigon.pipelines.catalog import FallbackPolicy
from kabigon.pipelines.catalog import match_pipeline

LoaderFactory = Callable[[], Loader]
_EMPTY_EXECUTION_PLAN = "Load chain execution plan cannot be empty."

DEFAULT_FALLBACK_LOADERS = (
    loader_registry.PTT,
    loader_registry.TWITTER,
    loader_registry.TRUTHSOCIAL,
    loader_registry.REDDIT,
    loader_registry.YOUTUBE,
    loader_registry.REEL,
    loader_registry.YOUTUBE_YTDLP,
    loader_registry.PDF,
    loader_registry.GITHUB,
    loader_registry.BBC,
    loader_registry.CNN,
    loader_registry.PLAYWRIGHT_NETWORKIDLE,
    loader_registry.PLAYWRIGHT_FAST,
)

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
    get_factory: Callable[[str], LoaderFactory]
    explanation: LoadChainExplanation

    async def load(self) -> str:
        errors: list[str] = []

        for planned_loader_name in self.explanation.execution_plan:
            loader_name = planned_loader_name
            try:
                loader = self.get_factory(planned_loader_name)()
                loader_name = loader.__class__.__name__
                logger.debug("[%s] Attempting to load URL: %s", loader_name, self.explanation.url)
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


def _merge_unique_requirements(*requirement_groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []

    for requirement in (requirement for group in requirement_groups for requirement in group):
        if requirement in seen:
            continue
        seen.add(requirement)
        ordered.append(requirement)

    return tuple(ordered)


def _no_loader_requirements(_name: str) -> tuple[str, ...]:
    return ()


def _requirements_for_loaders(
    loader_names: tuple[str, ...],
    get_requirements: Callable[[str], tuple[str, ...]],
) -> tuple[str, ...]:
    return _merge_unique_requirements(*(get_requirements(name) for name in loader_names))


def _missing_requirements(requirements: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(name for name in requirements if not os.getenv(name))


def _ensure_requirements(explanation: LoadChainExplanation) -> None:
    if not explanation.missing_requirements:
        return

    raise MissingRequirementError(explanation.missing_requirements)


def explain_load_chain(url: str) -> LoadChainExplanation:
    pipeline = match_pipeline(url)

    pipeline_name: str | None = None
    content_type = ContentType.GENERIC_WEB
    targeted_loaders: tuple[str, ...] = ()
    pipeline_requirements: tuple[str, ...] = ()
    fallback = DEFAULT_FALLBACK_LOADERS

    if pipeline is not None:
        pipeline_name = pipeline.name
        content_type = pipeline.content_type
        targeted_loaders = pipeline.targeted_loaders
        pipeline_requirements = pipeline.requirements
        if pipeline.fallback_policy == FallbackPolicy.NO_FALLBACK:
            fallback = ()

    execution_plan = _merge_unique_loaders(targeted_loaders, fallback)
    requirements = _merge_unique_requirements(
        pipeline_requirements,
        _requirements_for_loaders(execution_plan, get_loader_requirements),
    )
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
    return LoadChain(get_factory=get_loader_factory, explanation=explanation)


def resolve_explicit_load_chain(
    url: str,
    loader_names: Sequence[str],
    get_factory: Callable[[str], LoaderFactory] = get_loader_factory,
    get_requirements: Callable[[str], tuple[str, ...]] | None = None,
) -> LoadChain:
    execution_plan = tuple(loader_names)
    requirements_lookup = (
        (get_loader_requirements if get_factory is get_loader_factory else _no_loader_requirements)
        if get_requirements is None
        else get_requirements
    )
    requirements = _requirements_for_loaders(execution_plan, requirements_lookup)
    explanation = LoadChainExplanation(
        url=url,
        pipeline=None,
        content_type=ContentType.GENERIC_WEB,
        targeted_loaders=(),
        execution_plan=execution_plan,
        requirements=requirements,
        missing_requirements=_missing_requirements(requirements),
    )
    if not execution_plan:
        raise ValueError(_EMPTY_EXECUTION_PLAN)
    _ensure_requirements(explanation)
    return LoadChain(get_factory=get_factory, explanation=explanation)


__all__ = [
    "DEFAULT_FALLBACK_LOADERS",
    "LoadChain",
    "LoadChainExplanation",
    "explain_load_chain",
    "resolve_explicit_load_chain",
    "resolve_load_chain",
]
