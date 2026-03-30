import pytest

from kabigon.core.exception import LoaderNotApplicableError
from kabigon.loaders.twitter import check_x_url
from kabigon.loaders.twitter import normalize_twitter_url
from kabigon.loaders.twitter import sanitize_twitter_markdown


@pytest.mark.parametrize(
    "url",
    [
        "https://x.com/mhdksafa/status/2038190305950781695?s=46",
        "https://twitter.com/user/status/123?t=abc&s=20",
        "https://fxtwitter.com/user/status/123",
    ],
)
def test_normalize_twitter_url(url: str) -> None:
    normalized = normalize_twitter_url(url)
    assert normalized.startswith("https://x.com/")
    assert "?" not in normalized


@pytest.mark.parametrize(
    "url",
    [
        "https://x.com/user/status/123",
        "https://twitter.com/user/status/123",
        "https://www.x.com/user/status/123",
    ],
)
def test_check_x_url_accepts_supported_domains(url: str) -> None:
    check_x_url(url)


def test_check_x_url_rejects_unsupported_domain() -> None:
    with pytest.raises(LoaderNotApplicableError):
        check_x_url("https://example.com/user/status/123")


def test_sanitize_twitter_markdown_removes_noise_lines() -> None:
    content = "Mohamad Safa\nPCF_LABEL_NONE\nI don't think people understand"
    assert sanitize_twitter_markdown(content) == "Mohamad Safa\nI don't think people understand"
