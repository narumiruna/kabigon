import pytest

from kabigon.youtube import NoVideoIDFoundError
from kabigon.youtube import UnsupportedURLNetlocError
from kabigon.youtube import UnsupportedURLSchemeError
from kabigon.youtube import VideoIDError
from kabigon.youtube import check_youtube_url
from kabigon.youtube import parse_video_id


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
    ],
)
def test_check_youtube_url(url: str) -> None:
    check_youtube_url(url)


@pytest.mark.parametrize("url", ["https://example.com"])
def test_check_youtube_url_error(url: str) -> None:
    with pytest.raises(ValueError):
        check_youtube_url(url)


# Tests for parse_video_id function


@pytest.mark.parametrize(
    ("url", "expected_video_id"),
    [
        # Standard youtube.com URLs
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("http://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        # youtu.be short URLs
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("http://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        # Mobile URLs
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        # No-cookie URLs
        ("https://www.youtube-nocookie.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        # vid.plus URLs
        ("https://vid.plus/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ],
)
def test_parse_video_id_success(url: str, expected_video_id: str) -> None:
    """Test that parse_video_id correctly extracts video IDs from various URL formats."""
    video_id = parse_video_id(url)
    assert video_id == expected_video_id


def test_parse_video_id_unsupported_scheme() -> None:
    """Test that UnsupportedURLSchemeError is raised for non-http(s) schemes."""
    with pytest.raises(UnsupportedURLSchemeError, match="unsupported URL scheme: ftp"):
        parse_video_id("ftp://www.youtube.com/watch?v=dQw4w9WgXcQ")


def test_parse_video_id_unsupported_netloc() -> None:
    """Test that UnsupportedURLNetlocError is raised for unsupported domains."""
    with pytest.raises(UnsupportedURLNetlocError, match="unsupported URL netloc: example.com"):
        parse_video_id("https://example.com/watch?v=dQw4w9WgXcQ")


def test_parse_video_id_missing_video_id() -> None:
    """Test that NoVideoIDFoundError is raised when video ID parameter is missing."""
    with pytest.raises(NoVideoIDFoundError, match="no video found in URL"):
        parse_video_id("https://www.youtube.com/watch")


def test_parse_video_id_invalid_length() -> None:
    """Test that VideoIDError is raised for video IDs that are not 11 characters."""
    # Too short
    with pytest.raises(VideoIDError, match="invalid video ID: abc"):
        parse_video_id("https://www.youtube.com/watch?v=abc")

    # Too long
    with pytest.raises(VideoIDError, match="invalid video ID: dQw4w9WgXcQ123"):
        parse_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ123")


def test_parse_video_id_youtu_be_with_path() -> None:
    """Test that youtu.be URLs with additional path segments work correctly."""
    video_id = parse_video_id("https://youtu.be/dQw4w9WgXcQ")
    assert video_id == "dQw4w9WgXcQ"


def test_parse_video_id_vid_plus() -> None:
    """Test that vid.plus URLs work correctly."""
    video_id = parse_video_id("https://vid.plus/dQw4w9WgXcQ")
    assert video_id == "dQw4w9WgXcQ"


# Tests for exception classes


def test_unsupported_url_scheme_error_message() -> None:
    """Test UnsupportedURLSchemeError exception message format."""
    exc = UnsupportedURLSchemeError("ftp")
    assert str(exc) == "unsupported URL scheme: ftp"


def test_unsupported_url_netloc_error_message() -> None:
    """Test UnsupportedURLNetlocError exception message format."""
    exc = UnsupportedURLNetlocError("example.com")
    assert str(exc) == "unsupported URL netloc: example.com"


def test_video_id_error_message() -> None:
    """Test VideoIDError exception message format."""
    exc = VideoIDError("abc")
    assert str(exc) == "invalid video ID: abc"


def test_no_video_id_found_error_message() -> None:
    """Test NoVideoIDFoundError exception message format."""
    exc = NoVideoIDFoundError("https://www.youtube.com/watch")
    assert str(exc) == "no video found in URL: https://www.youtube.com/watch"


# Test check_youtube_url with various error scenarios


def test_check_youtube_url_converts_scheme_error_to_value_error() -> None:
    """Test that check_youtube_url converts UnsupportedURLSchemeError to ValueError."""
    with pytest.raises(ValueError, match="unsupported URL scheme"):
        check_youtube_url("ftp://www.youtube.com/watch?v=dQw4w9WgXcQ")


def test_check_youtube_url_converts_netloc_error_to_value_error() -> None:
    """Test that check_youtube_url converts UnsupportedURLNetlocError to ValueError."""
    with pytest.raises(ValueError, match="unsupported URL netloc"):
        check_youtube_url("https://example.com/watch?v=dQw4w9WgXcQ")


def test_check_youtube_url_converts_no_video_id_error_to_value_error() -> None:
    """Test that check_youtube_url converts NoVideoIDFoundError to ValueError."""
    with pytest.raises(ValueError, match="no video found in URL"):
        check_youtube_url("https://www.youtube.com/watch")


def test_check_youtube_url_converts_video_id_error_to_value_error() -> None:
    """Test that check_youtube_url converts VideoIDError to ValueError."""
    with pytest.raises(ValueError, match="invalid video ID"):
        check_youtube_url("https://www.youtube.com/watch?v=abc")
