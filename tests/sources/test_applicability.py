import pytest

from kabigon.core.errors import InvalidURLError
from kabigon.core.errors import LoaderNotApplicableError
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
from kabigon.sources.applicability import parse_github_raw_content_target
from kabigon.sources.applicability import parse_twitter_target
from kabigon.sources.applicability import parse_youtube_video_target
from kabigon.sources.applicability import require_loader_applicability


@pytest.mark.parametrize(
    ("url", "is_applicable"),
    [
        ("https://www.ptt.cc/bbs/Gossiping/M.1746078381.A.FFC.html", is_ptt_url),
        ("https://x.com/howie_serious/status/1917768568135115147", is_twitter_url),
        ("https://truthsocial.com/@realDonaldTrump/posts/115830428767897167", is_truthsocial_url),
        ("https://www.reddit.com/r/python/comments/abc/example/", is_reddit_url),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", is_youtube_video_url),
        ("https://www.instagram.com/reel/CuA0XYZ1234/", is_reel_url),
        ("https://github.com/anthropics/claude-code/blob/main/README.md", is_github_url),
        ("https://www.bbc.com/news/articles/c70k29914q4o", is_bbc_url),
        ("https://edition.cnn.com/2026/03/16/tech/example", is_cnn_url),
        ("https://news.ltn.com.tw/news/life/breakingnews/5432239", is_ltn_url),
        ("https://openai.com/pricing", is_openai_web_url),
        ("/tmp/demo.pdf", is_pdf_target),
        ("https://arxiv.org/pdf/2603.20617", is_pdf_target),
    ],
)
def test_source_applicability_accepts_supported_targets(url, is_applicable) -> None:
    assert is_applicable(url)


@pytest.mark.parametrize(
    "is_applicable",
    [
        is_ptt_url,
        is_twitter_url,
        is_truthsocial_url,
        is_reddit_url,
        is_youtube_video_url,
        is_reel_url,
        is_github_url,
        is_bbc_url,
        is_cnn_url,
        is_ltn_url,
        is_openai_web_url,
        is_pdf_target,
    ],
)
def test_source_applicability_rejects_unknown_targets(is_applicable) -> None:
    assert not is_applicable("https://example.com/not-supported")


def test_youtube_applicability_rejects_playlist() -> None:
    assert not is_youtube_video_url("https://www.youtube.com/playlist?list=PL123")


def test_youtube_target_exposes_video_id() -> None:
    target = parse_youtube_video_target("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert target.video_id == "dQw4w9WgXcQ"


def test_github_raw_content_target_normalizes_blob_url() -> None:
    target = parse_github_raw_content_target("https://github.com/anthropics/claude-code/blob/main/README.md")

    assert target.raw_url == "https://raw.githubusercontent.com/anthropics/claude-code/main/README.md"


def test_github_raw_content_target_rejects_repo_page() -> None:
    with pytest.raises(InvalidURLError):
        parse_github_raw_content_target("https://github.com/anthropics/claude-code")


def test_twitter_target_normalizes_to_x_domain() -> None:
    target = parse_twitter_target("https://fxtwitter.com/user/status/1")

    assert target.normalized_url == "https://x.com/user/status/1"


def test_pdf_target_requires_pdf_suffix() -> None:
    assert not is_pdf_target("not-a-valid-url")


def test_loader_applicability_converts_source_parse_failure() -> None:
    with pytest.raises(LoaderNotApplicableError) as exc_info:
        require_loader_applicability(
            "YoutubeLoader", "https://example.com/watch?v=dQw4w9WgXcQ", parse_youtube_video_target
        )

    error = exc_info.value
    assert error.loader_name == "YoutubeLoader"
    assert error.url == "https://example.com/watch?v=dQw4w9WgXcQ"
    assert error.reason == "unsupported URL netloc: example.com"


def test_loader_applicability_preserves_loader_not_applicable_error() -> None:
    with pytest.raises(LoaderNotApplicableError) as exc_info:
        require_loader_applicability("TwitterLoader", "https://example.com/status/1", parse_twitter_target)

    error = exc_info.value
    assert error.loader_name == "TwitterLoader"
    assert error.url == "https://example.com/status/1"
    assert error.reason == "URL is not a Twitter/X URL"
