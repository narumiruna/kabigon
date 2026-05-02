import pytest

from kabigon.core.errors import LoaderNotApplicableError
from kabigon.loaders.twitter import check_x_url
from kabigon.loaders.twitter import replace_domain


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
def test_check_x_url_accepts_supported_hosts(url: str) -> None:
    check_x_url(url)


def test_check_x_url_rejects_unknown_host() -> None:
    with pytest.raises(LoaderNotApplicableError):
        check_x_url("https://example.com/user/status/1")


def test_replace_domain_normalizes_to_x() -> None:
    assert replace_domain("https://fxtwitter.com/user/status/1") == "https://x.com/user/status/1"


def test_replace_domain_accepts_custom_domain() -> None:
    assert replace_domain("https://x.com/user/status/1", "twitter.com") == "https://twitter.com/user/status/1"
