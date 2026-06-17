import pytest

from kabigon.core.errors import LoaderNotApplicableError
from kabigon.loaders.youtube import YoutubeLoader
from kabigon.loaders.youtube import parse_video_id
from kabigon.sources.applicability import NoVideoIDFoundError
from kabigon.sources.applicability import UnsupportedURLNetlocError
from kabigon.sources.applicability import UnsupportedURLSchemeError
from kabigon.sources.applicability import VideoIDError

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
        # YouTube Music URLs
        ("https://music.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
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
    with pytest.raises(UnsupportedURLNetlocError, match=r"unsupported URL netloc: example.com"):
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


def test_youtube_loader_converts_source_applicability_to_not_applicable() -> None:
    loader = YoutubeLoader()

    with pytest.raises(LoaderNotApplicableError) as exc_info:
        loader.load_sync("https://example.com/watch?v=dQw4w9WgXcQ")

    error = exc_info.value
    assert error.loader_name == "YoutubeLoader"
    assert error.reason == "unsupported URL netloc: example.com"
