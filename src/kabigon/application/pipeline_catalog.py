from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from .source_applicability import is_bbc_url
from .source_applicability import is_cnn_url
from .source_applicability import is_github_url
from .source_applicability import is_openai_web_url
from .source_applicability import is_pdf_target
from .source_applicability import is_ptt_url
from .source_applicability import is_reddit_url
from .source_applicability import is_reel_url
from .source_applicability import is_truthsocial_url
from .source_applicability import is_twitter_url
from .source_applicability import is_youtube_video_url

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
            name="ptt",
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=("ptt",),
        ),
        matches=_is_ptt_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="twitter",
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=("twitter",),
        ),
        matches=_is_twitter_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="truthsocial",
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=("truthsocial",),
        ),
        matches=_is_truthsocial_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="reddit",
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=("reddit",),
        ),
        matches=_is_reddit_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="youtube",
            content_type=ContentType.YOUTUBE_VIDEO,
            targeted_loaders=("youtube", "youtube-ytdlp"),
        ),
        matches=_is_youtube_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="reel",
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=("reel",),
        ),
        matches=_is_reel_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="github",
            content_type=ContentType.CODE_CONTENT,
            targeted_loaders=("github",),
        ),
        matches=_is_github_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="bbc",
            content_type=ContentType.NEWS_ARTICLE,
            targeted_loaders=("bbc",),
        ),
        matches=_is_bbc_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="cnn",
            content_type=ContentType.NEWS_ARTICLE,
            targeted_loaders=("cnn",),
        ),
        matches=_is_cnn_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="openai_web",
            content_type=ContentType.GENERIC_WEB,
            targeted_loaders=("firecrawl",),
            requirements=("FIRECRAWL_API_KEY",),
            fallback_policy=FallbackPolicy.NO_FALLBACK,
        ),
        matches=_is_openai_web_url,
    ),
    _PipelineEntry(
        pipeline=Pipeline(
            name="pdf",
            content_type=ContentType.DOCUMENT_PDF,
            targeted_loaders=("pdf",),
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
