import pytest

from kabigon.core.errors import LoaderContentError
from kabigon.loaders.content_guard import BLOCKED_MARKERS
from kabigon.loaders.content_guard import MIN_CONTENT_LENGTH
from kabigon.loaders.content_guard import ensure_usable_content


def _long_text(n: int = MIN_CONTENT_LENGTH + 50) -> str:
    return "lorem ipsum dolor sit amet " * (n // 27 + 1)


def test_ensure_usable_content_passes_for_real_content() -> None:
    ensure_usable_content(_long_text(), loader_name="X", url="https://example.com")


def test_ensure_usable_content_rejects_short_content() -> None:
    with pytest.raises(LoaderContentError, match="too short"):
        ensure_usable_content("hi", loader_name="X", url="https://example.com")


def test_ensure_usable_content_honors_custom_min_length() -> None:
    ensure_usable_content("hello world", loader_name="X", url="https://example.com", min_length=5)


@pytest.mark.parametrize("marker", BLOCKED_MARKERS)
def test_ensure_usable_content_rejects_known_block_markers(marker: str) -> None:
    payload = _long_text() + "\n" + marker.upper()
    with pytest.raises(LoaderContentError, match="block/challenge marker"):
        ensure_usable_content(payload, loader_name="X", url="https://example.com")


def test_cloudflare_just_a_moment_is_rejected() -> None:
    # Realistic snippet returned by curl/httpx against a CF-protected site.
    payload = "Just a moment...\nEnable JavaScript and cookies to continue\n" * 20
    with pytest.raises(LoaderContentError):
        ensure_usable_content(payload, loader_name="X", url="https://example.com")
