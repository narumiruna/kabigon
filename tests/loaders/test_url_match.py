import pytest

from kabigon.domain.errors import LoaderNotApplicableError
from kabigon.loaders.url_match import ensure_domain_suffix
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
