import pytest

from kabigon.core.errors import LoaderContentError
from kabigon.loaders.content_guard import ensure_usable_content


@pytest.mark.parametrize("content", ["hi", "Hello world. This is my homepage.", "A useful paragraph. " * 50])
def test_ensure_usable_content_accepts_nonempty_pages(content: str) -> None:
    ensure_usable_content(content, loader_name="X", url="https://example.com")


@pytest.mark.parametrize("content", ["", " \n\t "])
def test_ensure_usable_content_rejects_empty_content(content: str) -> None:
    with pytest.raises(LoaderContentError, match="too short"):
        ensure_usable_content(content, loader_name="X", url="https://example.com")


def test_ensure_usable_content_honors_custom_min_length() -> None:
    ensure_usable_content("hello world", loader_name="X", url="https://example.com", min_length=5)
    with pytest.raises(LoaderContentError, match="too short"):
        ensure_usable_content("hi", loader_name="X", url="https://example.com", min_length=5)


@pytest.mark.parametrize(
    "heading",
    [
        "Just a moment...",
        "Checking your browser",
        "Attention required! | Cloudflare",
        "DDoS protection by Cloudflare",
        "Enable JavaScript and cookies to continue",
    ],
)
@pytest.mark.parametrize("prefix", ["", "# ", "## "])
def test_ensure_usable_content_rejects_challenge_headings(heading: str, prefix: str) -> None:
    payload = f"\n{prefix}{heading}\nPlease wait while we verify your browser."
    with pytest.raises(LoaderContentError, match="block/challenge marker"):
        ensure_usable_content(payload, loader_name="X", url="https://example.com")


@pytest.mark.parametrize(
    "phrase",
    ["access denied", "403 forbidden", "502 bad gateway", "503 service unavailable", "cf-error-details"],
)
def test_ensure_usable_content_accepts_error_documentation(phrase: str) -> None:
    payload = f"# {phrase}\n" + "Verify that your account has the required permissions. " * 20
    ensure_usable_content(payload, loader_name="X", url="https://example.com")


def test_ensure_usable_content_accepts_challenge_phrases_inside_an_article() -> None:
    payload = "# Troubleshooting browser challenges\n\nJust a moment...\nChecking your browser\n"
    ensure_usable_content(payload, loader_name="X", url="https://example.com")
