import pytest

from kabigon.pipelines.catalog import ContentType
from kabigon.pipelines.catalog import FallbackPolicy
from kabigon.pipelines.catalog import match_pipeline


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


def test_match_pipeline_ptt() -> None:
    pipeline = match_pipeline("https://www.ptt.cc/bbs/Gossiping/M.1746078381.A.FFC.html")

    assert pipeline is not None
    assert pipeline.name == "ptt"


@pytest.mark.parametrize(
    "url",
    [
        "https://truthsocial.com/@realDonaldTrump/posts/123456",
        "https://www.truthsocial.com/@user/posts/789",
    ],
)
def test_match_pipeline_truthsocial_hosts(url: str) -> None:
    pipeline = match_pipeline(url)

    assert pipeline is not None
    assert pipeline.name == "truthsocial"


@pytest.mark.parametrize(
    "url",
    [
        "https://x.com/user/status/1",
        "https://fixupx.com/user/status/1",
    ],
)
def test_match_pipeline_twitter_hosts(url: str) -> None:
    pipeline = match_pipeline(url)

    assert pipeline is not None
    assert pipeline.name == "twitter"


def test_match_pipeline_unknown_returns_none() -> None:
    assert match_pipeline("https://example.com/path") is None


def test_match_pipeline_non_http_pdf_path() -> None:
    pipeline = match_pipeline("/tmp/demo.pdf")

    assert pipeline is not None
    assert pipeline.name == "pdf"
    assert pipeline.content_type == ContentType.DOCUMENT_PDF
    assert pipeline.targeted_loaders == ("pdf",)


def test_match_pipeline_arxiv_pdf_endpoint() -> None:
    pipeline = match_pipeline("https://arxiv.org/pdf/2603.20617")

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
    ("url", "pipeline_name"),
    [
        ("https://www.instagram.com/reel/CuA0XYZ1234/", "reel"),
        ("https://www.bbc.com/news/articles/c70k29914q4o", "bbc"),
        ("https://edition.cnn.com/2026/03/16/tech/example", "cnn"),
    ],
)
def test_match_pipeline_remaining_source_applicability(url: str, pipeline_name: str) -> None:
    pipeline = match_pipeline(url)

    assert pipeline is not None
    assert pipeline.name == pipeline_name


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
    assert pipeline.fallback_policy == FallbackPolicy.NO_FALLBACK


def test_match_pipeline_developers_openai_is_not_openai_web() -> None:
    assert match_pipeline("https://developers.openai.com/codex/pricing") is None
