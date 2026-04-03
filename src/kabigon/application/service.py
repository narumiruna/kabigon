from __future__ import annotations

from dataclasses import dataclass

from kabigon.domain.loader import Loader
from kabigon.domain.models import LoaderPlan
from kabigon.domain.models import RetrievalContext
from kabigon.domain.models import RetrievalStrategy
from kabigon.infrastructure.registry import list_loader_names

from .executor import build_loader
from .planner import build_loader_plan
from .routing import DEFAULT_FALLBACK_LOADERS
from .routing import resolve_pipeline_requirements
from .strategy import build_retrieval_context
from .strategy import build_strategy_from_context


@dataclass(frozen=True)
class _Resolution:
    context: RetrievalContext
    strategy: RetrievalStrategy
    plan: LoaderPlan


def _resolve(url: str) -> _Resolution:
    context = build_retrieval_context(url)
    strategy = build_strategy_from_context(context)
    plan = build_loader_plan(strategy=strategy, default_fallback=DEFAULT_FALLBACK_LOADERS)
    return _Resolution(context=context, strategy=strategy, plan=plan)


def resolve_context(url: str) -> RetrievalContext:
    return _resolve(url).context


def resolve_strategy(url: str) -> RetrievalStrategy:
    return _resolve(url).strategy


def resolve_loader_plan(url: str) -> LoaderPlan:
    return _resolve(url).plan


def resolve_loader(url: str) -> Loader:
    return build_loader(_resolve(url).plan)


def resolve_execution_plan_loader_names(url: str) -> list[str]:
    return list(_resolve(url).plan.loader_names)


def resolve_targeted_loader_names(url: str) -> list[str]:
    return list(_resolve(url).context.targeted_loaders)


def load_url_sync(url: str) -> str:
    return resolve_loader(url).load_sync(url)


async def load_url(url: str) -> str:
    return await resolve_loader(url).load(url)


def available_loaders() -> list[str]:
    return list_loader_names()


def explain_plan(url: str) -> dict[str, object]:
    result = _resolve(url)
    return {
        "url": url,
        "pipeline": result.context.pipeline_name,
        "content_type": result.context.content_type,
        "targeted_loaders": list(result.context.targeted_loaders),
        "execution_plan": list(result.plan.loader_names),
        "requirements": list(resolve_pipeline_requirements(result.context.pipeline_name)),
    }
