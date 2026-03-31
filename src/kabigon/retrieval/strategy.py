from __future__ import annotations

from kabigon.core.models import RetrievalContext
from kabigon.core.models import RetrievalStrategy
from kabigon.pipelines import resolve_pipeline_name
from kabigon.pipelines import resolve_targeted_loader_names

from .classifier import classify_pipeline_name


def build_retrieval_context(url: str) -> RetrievalContext:
    pipeline_name = resolve_pipeline_name(url)
    targeted_loaders = tuple(resolve_targeted_loader_names(url))
    content_type = classify_pipeline_name(pipeline_name)

    return RetrievalContext(
        url=url,
        pipeline_name=pipeline_name,
        targeted_loaders=targeted_loaders,
        content_type=content_type,
    )


def build_strategy_from_context(context: RetrievalContext) -> RetrievalStrategy:
    return RetrievalStrategy(
        content_type=context.content_type,
        primary_loaders=context.targeted_loaders,
    )


def build_strategy(url: str) -> RetrievalStrategy:
    context = build_retrieval_context(url)
    return build_strategy_from_context(context)
