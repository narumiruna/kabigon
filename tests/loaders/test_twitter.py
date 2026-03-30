import pytest

from kabigon.loaders.twitter import TWITTER_DOMAINS
from kabigon.loaders.twitter import check_x_url
from kabigon.loaders.twitter import extract_tweet_path
from kabigon.loaders.twitter import replace_domain


@pytest.mark.parametrize(
    "url",
    [
        "https://x.com/mhdksafa/status/2038190305950781695?s=46",
        "https://x.com/user/status/1234567890",
        "https://twitter.com/user/status/1234567890",
        "https://fxtwitter.com/user/status/1234567890",
    ],
)
def test_check_x_url_valid(url: str) -> None:
    check_x_url(url)


def test_check_x_url_invalid() -> None:
    from kabigon.core.exception import LoaderNotApplicableError

    with pytest.raises(LoaderNotApplicableError):
        check_x_url("https://example.com/user/status/1234567890")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://x.com/mhdksafa/status/2038190305950781695?s=46",
            ("mhdksafa", "2038190305950781695"),
        ),
        (
            "https://x.com/user/status/1234567890",
            ("user", "1234567890"),
        ),
        (
            "https://twitter.com/some_user/status/9876543210",
            ("some_user", "9876543210"),
        ),
        (
            "https://fxtwitter.com/user/status/1111111111",
            ("user", "1111111111"),
        ),
    ],
)
def test_extract_tweet_path(url: str, expected: tuple[str, str]) -> None:
    assert extract_tweet_path(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://x.com/",
        "https://x.com/home",
        "https://x.com/user",
        "https://x.com/user/followers",
    ],
)
def test_extract_tweet_path_non_status_urls(url: str) -> None:
    assert extract_tweet_path(url) is None


def test_extract_tweet_path_strips_query_params() -> None:
    url = "https://x.com/mhdksafa/status/2038190305950781695?s=46"
    result = extract_tweet_path(url)
    assert result is not None
    username, tweet_id = result
    assert username == "mhdksafa"
    assert tweet_id == "2038190305950781695"
    assert "s=46" not in tweet_id


def test_replace_domain() -> None:
    assert replace_domain("https://twitter.com/user/status/1234") == "https://x.com/user/status/1234"
    assert replace_domain("https://fxtwitter.com/user/status/1234") == "https://x.com/user/status/1234"


def test_twitter_domains_contains_expected() -> None:
    required = {"x.com", "twitter.com", "api.fxtwitter.com"}
    assert required.issubset(set(TWITTER_DOMAINS))
