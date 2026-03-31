from __future__ import annotations

from kabigon.domain.models import RetrievalContext
from kabigon.domain.models import RetrievalStrategy

from .classification import classify_pipeline_name
from .routing import resolve_route


def build_retrieval_context(url: str) -> RetrievalContext:
    pipeline_name, targeted_loaders = resolve_route(url)
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
