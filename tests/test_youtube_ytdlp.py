import pytest

from kabigon.youtube_ytdlp import check_youtube_url


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=abc123",
        "https://youtube.com/watch?v=abc123",
        "https://youtu.be/abc123",
    ],
)
def test_check_youtube_url(url: str) -> None:
    check_youtube_url(url)


@pytest.mark.parametrize("url", ["https://example.com"])
def test_check_youtube_url_error(url: str) -> None:
    with pytest.raises(ValueError):
        check_youtube_url(url)
