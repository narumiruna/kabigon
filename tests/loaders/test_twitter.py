import pytest

from kabigon.core.errors import LoaderNotApplicableError
from kabigon.loaders.twitter import replace_domain
from kabigon.sources.applicability import parse_twitter_target


@pytest.mark.parametrize(
    "url",
    [
        "https://twitter.com/user/status/1",
        "https://x.com/user/status/1",
        "https://fxtwitter.com/user/status/1",
        "https://vxtwitter.com/user/status/1",
        "https://fixvx.com/user/status/1",
        "https://twittpr.com/user/status/1",
        "https://api.fxtwitter.com/user/status/1",
        "https://fixupx.com/user/status/1",
    ],
)
def test_parse_twitter_target_accepts_supported_hosts(url: str) -> None:
    parse_twitter_target(url)


def test_parse_twitter_target_rejects_unknown_host() -> None:
    with pytest.raises(LoaderNotApplicableError):
        parse_twitter_target("https://example.com/user/status/1")


def test_replace_domain_normalizes_to_x() -> None:
    assert replace_domain("https://fxtwitter.com/user/status/1") == "https://x.com/user/status/1"


def test_replace_domain_accepts_custom_domain() -> None:
    assert replace_domain("https://x.com/user/status/1", "twitter.com") == "https://twitter.com/user/status/1"
