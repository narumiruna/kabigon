import pytest

from kabigon.application.pipeline_catalog import ContentType
from kabigon.application.pipeline_catalog import FallbackPolicy
from kabigon.application.pipeline_catalog import match_pipeline


def test_match_pipeline_youtube() -> None:
    pipeline = match_pipeline("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert pipeline is not None
    assert pipeline.name == "youtube"
    assert pipeline.content_type == ContentType.YOUTUBE_VIDEO
    assert pipeline.targeted_loaders == ("youtube", "youtube-ytdlp")


def test_match_pipeline_youtube_playlist_is_not_video_pipeline() -> None:
    assert match_pipeline("https://www.youtube.com/playlist?list=PL123") is None


def test_match_pipeline_reddit() -> None:
    pipeline = match_pipeline("https://www.reddit.com/r/python/comments/abc/example/")

    assert pipeline is not None
    assert pipeline.name == "reddit"
    assert pipeline.content_type == ContentType.SOCIAL_POST
    assert pipeline.targeted_loaders == ("reddit",)


def test_match_pipeline_unknown_returns_none() -> None:
    assert match_pipeline("https://example.com/path") is None


def test_match_pipeline_non_http_pdf_path() -> None:
    pipeline = match_pipeline("/tmp/demo.pdf")

    assert pipeline is not None
    assert pipeline.name == "pdf"
    assert pipeline.content_type == ContentType.DOCUMENT_PDF
    assert pipeline.targeted_loaders == ("pdf",)


def test_match_pipeline_non_http_non_pdf_path_returns_none() -> None:
    assert match_pipeline("not-a-valid-url") is None


def test_match_pipeline_github_pdf_prefers_github() -> None:
    pipeline = match_pipeline("https://github.com/a/b/blob/main/demo.pdf")

    assert pipeline is not None
    assert pipeline.name == "github"


def test_match_pipeline_raw_github() -> None:
    pipeline = match_pipeline("https://raw.githubusercontent.com/a/b/main/README.md")

    assert pipeline is not None
    assert pipeline.name == "github"


@pytest.mark.parametrize(
    "url",
    [
        "https://openai.com/pricing",
        "https://platform.openai.com/docs/pricing",
        "https://help.openai.com/en/articles/20001106-codex-rate-card",
    ],
)
def test_match_pipeline_openai_web(url: str) -> None:
    pipeline = match_pipeline(url)

    assert pipeline is not None
    assert pipeline.name == "openai_web"
    assert pipeline.content_type == ContentType.GENERIC_WEB
    assert pipeline.targeted_loaders == ("firecrawl",)
    assert pipeline.requirements == ("FIRECRAWL_API_KEY",)
    assert pipeline.fallback_policy == FallbackPolicy.NO_FALLBACK


def test_match_pipeline_developers_openai_is_not_openai_web() -> None:
    assert match_pipeline("https://developers.openai.com/codex/pricing") is None
