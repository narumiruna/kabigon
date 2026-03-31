from __future__ import annotations

from dataclasses import dataclass

from kabigon.core.loader import Loader
from kabigon.core.models import LoaderPlan
from kabigon.core.models import RetrievalContext
from kabigon.core.models import RetrievalStrategy
from kabigon.pipelines import DEFAULT_FALLBACK_LOADERS

from .executor import build_loader
from .planner import build_loader_plan
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


def resolve_targeted_loader_names(url: str) -> list[str]:
    return list(_resolve(url).context.targeted_loaders)


def resolve_execution_plan_loader_names(url: str) -> list[str]:
    return list(_resolve(url).plan.loader_names)
