import pytest

from kabigon.core.errors import LoaderNotApplicableError
from kabigon.loaders.browser import DEFAULT_BLOCKED_RESOURCE_TYPES
from kabigon.loaders.browser import DEFAULT_BROWSER_USER_AGENT
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


class FakePage:
    def __init__(self) -> None:
        self.selector_timeout = 0.0

    async def wait_for_selector(self, selector: str, state: str, **kwargs) -> None:
        self.selector_timeout = kwargs["timeout"]


def test_truthsocial_loader_uses_browser_retrieval_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    page = FakePage()

    async def fake_fetch_browser_html(url: str, **kwargs) -> str:
        captured["url"] = url
        captured.update(kwargs)
        await kwargs["after_goto"](page)
        return "<html><body><article>truth</article></body></html>"

    monkeypatch.setattr("kabigon.loaders.truthsocial.fetch_browser_html", fake_fetch_browser_html)

    loader = TruthSocialLoader(timeout=10_000)
    result = loader.load_sync("https://truthsocial.com/@realDonaldTrump/posts/123456")

    assert captured["url"] == "https://truthsocial.com/@realDonaldTrump/posts/123456"
    assert captured["loader_name"] == "TruthSocialLoader"
    assert captured["timeout_ms"] == 10_000
    assert captured["wait_until"] == "domcontentloaded"
    assert captured["user_agent"] == DEFAULT_BROWSER_USER_AGENT
    assert captured["block_resource_types"] == DEFAULT_BLOCKED_RESOURCE_TYPES
    assert page.selector_timeout == 5_000
    assert "truth" in result
