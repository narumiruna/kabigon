from __future__ import annotations

from kabigon.core.models import ContentType
from kabigon.pipelines import resolve_pipeline_name

PIPELINE_CONTENT_TYPE: dict[str, ContentType] = {
    "youtube": ContentType.YOUTUBE_VIDEO,
    "twitter": ContentType.SOCIAL_POST,
    "truthsocial": ContentType.SOCIAL_POST,
    "reddit": ContentType.SOCIAL_POST,
    "ptt": ContentType.SOCIAL_POST,
    "reel": ContentType.SOCIAL_POST,
    "bbc": ContentType.NEWS_ARTICLE,
    "cnn": ContentType.NEWS_ARTICLE,
    "pdf": ContentType.DOCUMENT_PDF,
    "github": ContentType.CODE_CONTENT,
}


def classify_pipeline_name(pipeline_name: str | None) -> ContentType:
    if pipeline_name is None:
        return ContentType.GENERIC_WEB
    return PIPELINE_CONTENT_TYPE.get(pipeline_name, ContentType.GENERIC_WEB)


def classify_url(url: str) -> ContentType:
    return classify_pipeline_name(resolve_pipeline_name(url))
