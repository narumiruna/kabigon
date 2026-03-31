import pytest

from kabigon.domain.errors import LoaderNotApplicableError
from kabigon.loaders.url_match import ensure_domain_suffix
from kabigon.loaders.url_match import ensure_host_in
from kabigon.loaders.url_match import host_in
from kabigon.loaders.url_match import host_matches_domain_suffix


@pytest.mark.parametrize(
    ("url", "suffix"),
    [
        ("https://bbc.com/news", "bbc.com"),
        ("https://www.bbc.com/news", "bbc.com"),
        ("https://edition.cnn.com/world", "cnn.com"),
        ("https://CNN.com/world", "cnn.com"),
        ("https://example.com/path", ".example.com"),
    ],
)
def test_host_matches_domain_suffix(url: str, suffix: str) -> None:
    assert host_matches_domain_suffix(url, suffix)


@pytest.mark.parametrize(
    ("url", "suffix"),
    [
        ("https://notbbc.com/news", "bbc.com"),
        ("https://example.com/world", "cnn.com"),
        ("https://cnn.news.com/world", "cnn.com"),
    ],
)
def test_host_matches_domain_suffix_false(url: str, suffix: str) -> None:
    assert not host_matches_domain_suffix(url, suffix)


def test_ensure_domain_suffix_accepts_matching_host() -> None:
    ensure_domain_suffix(
        "https://www.bbc.com/news",
        "bbc.com",
        loader_name="BBCLoader",
        source_name="BBC",
    )


def test_ensure_domain_suffix_raises_not_applicable_error() -> None:
    with pytest.raises(LoaderNotApplicableError, match="Not a BBC URL"):
        ensure_domain_suffix(
            "https://example.com/news",
            "bbc.com",
            loader_name="BBCLoader",
            source_name="BBC",
        )


def test_host_in_matches_allowed_hosts() -> None:
    assert host_in("https://x.com/user/status/1", ["twitter.com", "x.com"])


def test_host_in_rejects_non_allowed_hosts() -> None:
    assert not host_in("https://example.com", ["twitter.com", "x.com"])


def test_ensure_host_in_accepts_allowed_host() -> None:
    ensure_host_in(
        "https://x.com/user/status/1",
        ["twitter.com", "x.com"],
        loader_name="TwitterLoader",
        source_name="Twitter/X",
    )


def test_ensure_host_in_raises_not_applicable_error() -> None:
    with pytest.raises(LoaderNotApplicableError, match="Not a Twitter/X URL"):
        ensure_host_in(
            "https://example.com",
            ["twitter.com", "x.com"],
            loader_name="TwitterLoader",
            source_name="Twitter/X",
        )
