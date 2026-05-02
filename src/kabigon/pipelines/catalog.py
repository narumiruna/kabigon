from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import kabigon.loader_registry as loader_names
from kabigon.sources.applicability import is_bbc_url
from kabigon.sources.applicability import is_cnn_url
from kabigon.sources.applicability import is_github_url
from kabigon.sources.applicability import is_openai_web_url
from kabigon.sources.applicability import is_pdf_target
from kabigon.sources.applicability import is_ptt_url
from kabigon.sources.applicability import is_reddit_url
from kabigon.sources.applicability import is_reel_url
from kabigon.sources.applicability import is_truthsocial_url
from kabigon.sources.applicability import is_twitter_url
from kabigon.sources.applicability import is_youtube_video_url

Matcher = Callable[[str], bool]


class ContentType(StrEnum):
    YOUTUBE_VIDEO = "youtube_video"
    SOCIAL_POST = "social_post"
    NEWS_ARTICLE = "news_article"
    DOCUMENT_PDF = "document_pdf"
    CODE_CONTENT = "code_content"
    GENERIC_WEB = "generic_web"


class FallbackPolicy(StrEnum):
    REMAINING_DEFAULT = "remaining_default"
    NO_FALLBACK = "no_fallback"


@dataclass(frozen=True)
class Pipeline:
    name: str
    content_type: ContentType
    targeted_loaders: tuple[str, ...]
    requirements: tuple[str, ...] = ()
    fallback_policy: FallbackPolicy = FallbackPolicy.REMAINING_DEFAULT


@dataclass(frozen=True)
class _PipelineEntry:
    pipeline: Pipeline
    matches: Matcher


def _is_ptt_url(url: str) -> bool:
    return is_ptt_url(url)


def _is_twitter_url(url: str) -> bool:
    return is_twitter_url(url)


def _is_truthsocial_url(url: str) -> bool:
    return is_truthsocial_url(url)


def _is_reddit_url(url: str) -> bool:
    return is_reddit_url(url)


def _is_youtube_url(url: str) -> bool:
    return is_youtube_video_url(url)


def _is_reel_url(url: str) -> bool:
    return is_reel_url(url)


def _is_github_url(url: str) -> bool:
    return is_github_url(url)


def _is_bbc_url(url: str) -> bool:
    return is_bbc_url(url)


def _is_cnn_url(url: str) -> bool:
    return is_cnn_url(url)


def _is_openai_web_url(url: str) -> bool:
    return is_openai_web_url(url)


def _is_pdf_url(url: str) -> bool:
    return is_pdf_target(url)


_PIPELINE_ENTRIES: tuple[_PipelineEntry, ...] = (
    _PipelineEntry(
        pipeline=Pipeline(
            name=loader_names.PTT,
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=(loader_names.PTT,),
        ),
        matches=_is_ptt_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name=loader_names.TWITTER,
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=(loader_names.TWITTER,),
        ),
        matches=_is_twitter_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name=loader_names.TRUTHSOCIAL,
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=(loader_names.TRUTHSOCIAL,),
        ),
        matches=_is_truthsocial_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name=loader_names.REDDIT,
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=(loader_names.REDDIT,),
        ),
        matches=_is_reddit_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name=loader_names.YOUTUBE,
            content_type=ContentType.YOUTUBE_VIDEO,
            targeted_loaders=(loader_names.YOUTUBE, loader_names.YOUTUBE_YTDLP),
        ),
        matches=_is_youtube_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name=loader_names.REEL,
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=(loader_names.REEL,),
        ),
        matches=_is_reel_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name=loader_names.GITHUB,
            content_type=ContentType.CODE_CONTENT,
            targeted_loaders=(loader_names.GITHUB,),
        ),
        matches=_is_github_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name=loader_names.BBC,
            content_type=ContentType.NEWS_ARTICLE,
            targeted_loaders=(loader_names.BBC,),
        ),
        matches=_is_bbc_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name=loader_names.CNN,
            content_type=ContentType.NEWS_ARTICLE,
            targeted_loaders=(loader_names.CNN,),
        ),
        matches=_is_cnn_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="openai_web",
            content_type=ContentType.GENERIC_WEB,
            targeted_loaders=(loader_names.FIRECRAWL,),
            requirements=("FIRECRAWL_API_KEY",),
            fallback_policy=FallbackPolicy.NO_FALLBACK,
        ),
        matches=_is_openai_web_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name=loader_names.PDF,
            content_type=ContentType.DOCUMENT_PDF,
            targeted_loaders=(loader_names.PDF,),
        ),
        matches=_is_pdf_url,
    ),
)


def match_pipeline(url: str) -> Pipeline | None:
    for entry in _PIPELINE_ENTRIES:
        if entry.matches(url):
            return entry.pipeline
    return None


def list_pipelines() -> tuple[Pipeline, ...]:
    return tuple(entry.pipeline for entry in _PIPELINE_ENTRIES)


__all__ = ["ContentType", "FallbackPolicy", "Pipeline", "list_pipelines", "match_pipeline"]
