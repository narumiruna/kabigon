from __future__ import annotations

from dataclasses import dataclass

from .pipeline_catalog import ContentType
from .pipeline_catalog import FallbackPolicy
from .pipeline_catalog import match_pipeline


@dataclass(frozen=True)
class RetrievalContext:
    url: str
    pipeline_name: str | None
    targeted_loaders: tuple[str, ...]
    content_type: ContentType
    requirements: tuple[str, ...] = ()
    fallback_policy: FallbackPolicy = FallbackPolicy.REMAINING_DEFAULT


@dataclass(frozen=True)
class LoaderPlan:
    loader_names: tuple[str, ...]


DEFAULT_FALLBACK_LOADERS: tuple[str, ...] = (
    "ptt",
    "twitter",
    "truthsocial",
    "reddit",
    "youtube",
    "reel",
    "youtube-ytdlp",
    "pdf",
    "github",
    "bbc",
    "cnn",
    "playwright-networkidle",
    "playwright-fast",
)


def build_retrieval_context(url: str) -> RetrievalContext:
    pipeline = match_pipeline(url)
    if pipeline is None:
        return RetrievalContext(
            url=url,
            pipeline_name=None,
            targeted_loaders=(),
            content_type=ContentType.GENERIC_WEB,
        )

    return RetrievalContext(
        url=url,
        pipeline_name=pipeline.name,
        targeted_loaders=pipeline.targeted_loaders,
        content_type=pipeline.content_type,
        requirements=pipeline.requirements,
        fallback_policy=pipeline.fallback_policy,
    )


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


def build_loader_plan(
    context: RetrievalContext,
    default_fallback: tuple[str, ...] = DEFAULT_FALLBACK_LOADERS,
) -> LoaderPlan:
    fallback = default_fallback
    if context.fallback_policy == FallbackPolicy.NO_FALLBACK:
        fallback = ()

    return LoaderPlan(
        loader_names=_merge_unique_loaders(
            primary=context.targeted_loaders,
            fallback=fallback,
        )
    )


__all__ = [
    "DEFAULT_FALLBACK_LOADERS",
    "LoaderPlan",
    "RetrievalContext",
    "build_loader_plan",
    "build_retrieval_context",
]
