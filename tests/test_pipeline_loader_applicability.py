import pytest

from kabigon.application.pipeline_catalog import match_pipeline
from kabigon.domain.errors import InvalidURLError
from kabigon.domain.errors import LoaderNotApplicableError
from kabigon.loaders.bbc import check_bbc_url
from kabigon.loaders.cnn import check_cnn_url
from kabigon.loaders.github import check_github_url
from kabigon.loaders.ptt import check_ptt_url
from kabigon.loaders.reddit import check_reddit_url
from kabigon.loaders.reel import check_reel_url
from kabigon.loaders.truthsocial import check_truthsocial_url
from kabigon.loaders.twitter import check_x_url
from kabigon.loaders.youtube import check_youtube_url

PIPELINE_APPLICABILITY_CASES = [
    ("ptt", "https://www.ptt.cc/bbs/Gossiping/M.1746078381.A.FFC.html", check_ptt_url),
    ("twitter", "https://x.com/howie_serious/status/1917768568135115147", check_x_url),
    ("truthsocial", "https://truthsocial.com/@realDonaldTrump/posts/115830428767897167", check_truthsocial_url),
    ("reddit", "https://www.reddit.com/r/python/comments/abc/example/", check_reddit_url),
    ("youtube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", check_youtube_url),
    ("reel", "https://www.instagram.com/reel/CuA0XYZ1234/", check_reel_url),
    ("github", "https://github.com/anthropics/claude-code/blob/main/README.md", check_github_url),
    ("bbc", "https://www.bbc.com/news/articles/c70k29914q4o", check_bbc_url),
    ("cnn", "https://edition.cnn.com/2026/03/16/tech/example", check_cnn_url),
]


@pytest.mark.parametrize(("pipeline_name", "url", "check_loader_url"), PIPELINE_APPLICABILITY_CASES)
def test_pipeline_catalog_match_agrees_with_loader_applicability(pipeline_name, url, check_loader_url) -> None:
    pipeline = match_pipeline(url)

    assert pipeline is not None
    assert pipeline.name == pipeline_name
    check_loader_url(url)


@pytest.mark.parametrize(("pipeline_name", "url", "check_loader_url"), PIPELINE_APPLICABILITY_CASES)
def test_loader_applicability_examples_match_pipeline_catalog(pipeline_name, url, check_loader_url) -> None:
    with pytest.raises((InvalidURLError, LoaderNotApplicableError, ValueError)):
        check_loader_url("https://example.com/not-supported")

    pipeline = match_pipeline(url)
    assert pipeline is not None
    assert pipeline.name == pipeline_name
