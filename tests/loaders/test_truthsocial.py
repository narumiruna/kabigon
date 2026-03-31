import pytest

from kabigon.core.exception import LoaderNotApplicableError
from kabigon.loaders.truthsocial import TruthSocialLoader
from kabigon.loaders.truthsocial import check_truthsocial_url


@pytest.mark.parametrize(
    "url",
    [
        "https://truthsocial.com/@realDonaldTrump/posts/123456",
        "https://www.truthsocial.com/@user/posts/789",
    ],
)
def test_check_truthsocial_url(url: str) -> None:
    """Test that valid Truth Social URLs pass validation."""
    check_truthsocial_url(url)  # Should not raise


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "https://twitter.com/user/status/123",
        "https://x.com/user/status/123",
    ],
)
def test_check_truthsocial_url_error(url: str) -> None:
    """Test that non-Truth Social URLs raise LoaderNotApplicableError."""
    with pytest.raises(LoaderNotApplicableError, match="Not a Truth Social URL"):
        check_truthsocial_url(url)


def test_truthsocial_loader_initialization() -> None:
    """Test TruthSocialLoader initialization."""
    loader = TruthSocialLoader()
    assert loader.timeout == 60_000


def test_truthsocial_loader_custom_timeout() -> None:
    """Test TruthSocialLoader with custom timeout."""
    loader = TruthSocialLoader(timeout=30_000)
    assert loader.timeout == 30_000
