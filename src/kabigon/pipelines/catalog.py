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
from kabigon.sources.applicability import is_pi_session_url
from kabigon.sources.applicability import is_ptt_url
from kabigon.sources.applicability import is_reddit_url
from kabigon.sources.applicability import is_reel_url
from kabigon.sources.applicability import is_truthsocial_url
from kabigon.sources.applicability import is_twitter_status_url
from kabigon.sources.applicability import is_youtube_video_url

Matcher = Callable[[str], bool]


class ContentType(StrEnum):
    YOUTUBE_VIDEO = "youtube_video"
    SOCIAL_POST = "social_post"
    NEWS_ARTICLE = "news_article"
    DOCUMENT_PDF = "document_pdf"
    AI_SESSION = "ai_session"
    CODE_CONTENT = "code_content"
    GENERIC_WEB = "generic_web"


class ContentContract(StrEnum):
    SOURCE_REQUIRED = "source_required"
    GENERIC_HTML = "generic_html"


class FallbackPolicy(StrEnum):
    REMAINING_DEFAULT = "remaining_default"
    NO_FALLBACK = "no_fallback"


GENERIC_HTML_LOADERS = (
    loader_names.CURL_CFFI,
    loader_names.PLAYWRIGHT_NETWORKIDLE,
    loader_names.PLAYWRIGHT_FAST,
    loader_names.HTTPX,
)


@dataclass(frozen=True)
class Pipeline:
    name: str
    content_type: ContentType
    targeted_loaders: tuple[str, ...]
    fallback_policy: FallbackPolicy = FallbackPolicy.NO_FALLBACK
    content_contract: ContentContract = ContentContract.SOURCE_REQUIRED
    fallback_loaders: tuple[str, ...] = ()


@dataclass(frozen=True)
class PipelinePlan:
    pipeline_name: str | None
    content_type: ContentType
    targeted_loaders: tuple[str, ...]
    fallback_loaders: tuple[str, ...]
    execution_plan: tuple[str, ...]
    content_contract: ContentContract


_PIPELINE_ENTRIES: tuple[tuple[Pipeline, Matcher], ...] = (
    (Pipeline(loader_names.PTT, ContentType.SOCIAL_POST, (loader_names.PTT,)), is_ptt_url),
    (Pipeline(loader_names.TWITTER, ContentType.SOCIAL_POST, (loader_names.TWITTER,)), is_twitter_status_url),
    (Pipeline(loader_names.TRUTHSOCIAL, ContentType.SOCIAL_POST, (loader_names.TRUTHSOCIAL,)), is_truthsocial_url),
    (Pipeline(loader_names.REDDIT, ContentType.SOCIAL_POST, (loader_names.REDDIT,)), is_reddit_url),
    (
        Pipeline(
            loader_names.YOUTUBE,
            ContentType.YOUTUBE_VIDEO,
            (loader_names.YOUTUBE, loader_names.YOUTUBE_YTDLP),
        ),
        is_youtube_video_url,
    ),
    (Pipeline(loader_names.REEL, ContentType.SOCIAL_POST, (loader_names.REEL,)), is_reel_url),
    (Pipeline(loader_names.PI_SESSION, ContentType.AI_SESSION, (loader_names.PI_SESSION,)), is_pi_session_url),
    (Pipeline(loader_names.GITHUB, ContentType.CODE_CONTENT, (loader_names.GITHUB,)), is_github_url),
    (Pipeline(loader_names.BBC, ContentType.NEWS_ARTICLE, (loader_names.BBC,)), is_bbc_url),
    (Pipeline(loader_names.CNN, ContentType.NEWS_ARTICLE, (loader_names.CNN,)), is_cnn_url),
    (Pipeline(loader_names.LTN, ContentType.NEWS_ARTICLE, (loader_names.LTN,)), is_ltn_url),
    (
        Pipeline(
            "openai_web",
            ContentType.GENERIC_WEB,
            (loader_names.FIRECRAWL,),
            content_contract=ContentContract.GENERIC_HTML,
        ),
        is_openai_web_url,
    ),
    (Pipeline(loader_names.PDF, ContentType.DOCUMENT_PDF, (loader_names.PDF,)), is_pdf_target),
)


def match_pipeline(url: str) -> Pipeline | None:
    for pipeline, matches in _PIPELINE_ENTRIES:
        if matches(url):
            return pipeline
    return None


def plan_for_url(url: str) -> PipelinePlan:
    pipeline = match_pipeline(url)
    if pipeline is None:
        return PipelinePlan(
            pipeline_name=None,
            content_type=ContentType.GENERIC_WEB,
            targeted_loaders=(),
            fallback_loaders=GENERIC_HTML_LOADERS,
            execution_plan=GENERIC_HTML_LOADERS,
            content_contract=ContentContract.GENERIC_HTML,
        )

    execution_plan = tuple(dict.fromkeys((*pipeline.targeted_loaders, *pipeline.fallback_loaders)))
    return PipelinePlan(
        pipeline_name=pipeline.name,
        content_type=pipeline.content_type,
        targeted_loaders=pipeline.targeted_loaders,
        fallback_loaders=pipeline.fallback_loaders,
        execution_plan=execution_plan,
        content_contract=pipeline.content_contract,
    )


def list_pipelines() -> tuple[Pipeline, ...]:
    return tuple(pipeline for pipeline, _matches in _PIPELINE_ENTRIES)


__all__ = [
    "GENERIC_HTML_LOADERS",
    "ContentContract",
    "ContentType",
    "FallbackPolicy",
    "Pipeline",
    "PipelinePlan",
    "list_pipelines",
    "match_pipeline",
    "plan_for_url",
]
