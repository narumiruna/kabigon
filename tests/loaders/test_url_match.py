import pytest

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
