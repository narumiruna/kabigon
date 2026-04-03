from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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
class RetrievalContext:
    url: str
    pipeline_name: str | None
    targeted_loaders: tuple[str, ...]
    content_type: ContentType


@dataclass(frozen=True)
class RetrievalStrategy:
    content_type: ContentType
    primary_loaders: tuple[str, ...]
    fallback_policy: FallbackPolicy = FallbackPolicy.REMAINING_DEFAULT


@dataclass(frozen=True)
class LoaderPlan:
    loader_names: tuple[str, ...]
