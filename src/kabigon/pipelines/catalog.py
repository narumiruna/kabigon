from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import kabigon.loader_registry as loader_names
from kabigon.sources.applicability import is_bbc_url
from kabigon.sources.applicability import is_cnn_url
from kabigon.sources.applicability import is_github_url
from kabigon.sources.applicability import is_ltn_url
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
    fallback_policy: FallbackPolicy = FallbackPolicy.REMAINING_DEFAULT


_PIPELINE_ENTRIES: tuple[tuple[Pipeline, Matcher], ...] = (
    (
        Pipeline(
            name=loader_names.PTT,
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=(loader_names.PTT,),
        ),
        is_ptt_url,
    ),
    (
        Pipeline(
            name=loader_names.TWITTER,
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=(loader_names.TWITTER,),
        ),
        is_twitter_url,
    ),
    (
        Pipeline(
            name=loader_names.TRUTHSOCIAL,
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=(loader_names.TRUTHSOCIAL,),
        ),
        is_truthsocial_url,
    ),
    (
        Pipeline(
            name=loader_names.REDDIT,
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=(loader_names.REDDIT,),
        ),
        is_reddit_url,
    ),
    (
        Pipeline(
            name=loader_names.YOUTUBE,
            content_type=ContentType.YOUTUBE_VIDEO,
            targeted_loaders=(loader_names.YOUTUBE, loader_names.YOUTUBE_YTDLP),
        ),
        is_youtube_video_url,
    ),
    (
        Pipeline(
            name=loader_names.REEL,
            content_type=ContentType.SOCIAL_POST,
            targeted_loaders=(loader_names.REEL,),
        ),
        is_reel_url,
    ),
    (
        Pipeline(
            name=loader_names.GITHUB,
            content_type=ContentType.CODE_CONTENT,
            targeted_loaders=(loader_names.GITHUB,),
        ),
        is_github_url,
    ),
    (
        Pipeline(
            name=loader_names.BBC,
            content_type=ContentType.NEWS_ARTICLE,
            targeted_loaders=(loader_names.BBC,),
        ),
        is_bbc_url,
    ),
    (
        Pipeline(
            name=loader_names.CNN,
            content_type=ContentType.NEWS_ARTICLE,
            targeted_loaders=(loader_names.CNN,),
        ),
        is_cnn_url,
    ),
    (
        Pipeline(
            name=loader_names.LTN,
            content_type=ContentType.NEWS_ARTICLE,
            targeted_loaders=(loader_names.LTN,),
        ),
        is_ltn_url,
    ),
    (
        Pipeline(
            name="openai_web",
            content_type=ContentType.GENERIC_WEB,
            targeted_loaders=(loader_names.FIRECRAWL,),
            fallback_policy=FallbackPolicy.NO_FALLBACK,
        ),
        is_openai_web_url,
    ),
    (
        Pipeline(
            name=loader_names.PDF,
            content_type=ContentType.DOCUMENT_PDF,
            targeted_loaders=(loader_names.PDF,),
        ),
        is_pdf_target,
    ),
)


def match_pipeline(url: str) -> Pipeline | None:
    for pipeline, matches in _PIPELINE_ENTRIES:
        if matches(url):
            return pipeline
    return None


def list_pipelines() -> tuple[Pipeline, ...]:
    return tuple(pipeline for pipeline, _matches in _PIPELINE_ENTRIES)


__all__ = ["ContentType", "FallbackPolicy", "Pipeline", "list_pipelines", "match_pipeline"]
