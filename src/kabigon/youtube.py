from urllib.parse import parse_qs
from urllib.parse import urlparse

import timeout_decorator
from youtube_transcript_api import YouTubeTranscriptApi

from .loader import Loader
from .loader import LoaderError

DEFAULT_LANGUAGES = ["zh-TW", "zh-Hant", "zh", "zh-Hans", "ja", "en", "ko"]
ALLOWED_SCHEMES = {
    "http",
    "https",
}
ALLOWED_NETLOCS = {
    "youtu.be",
    "m.youtube.com",
    "youtube.com",
    "www.youtube.com",
    "www.youtube-nocookie.com",
    "vid.plus",
}


class UnsupportedURLSchemeError(LoaderError):
    def __init__(self, scheme: str) -> None:
        super().__init__(f"unsupported URL scheme: {scheme}")


class UnsupportedURLNetlocError(LoaderError):
    def __init__(self, netloc: str) -> None:
        super().__init__(f"unsupported URL netloc: {netloc}")


class VideoIDError(LoaderError):
    def __init__(self, video_id: str) -> None:
        super().__init__(f"invalid video ID: {video_id}")


class NoVideoIDFoundError(LoaderError):
    def __init__(self, url: str) -> None:
        super().__init__(f"no video found in URL: {url}")


def parse_video_id(url: str) -> str:
    """Parse a YouTube URL and return the video ID if valid, otherwise None."""
    parsed_url = urlparse(url)

    if parsed_url.scheme not in ALLOWED_SCHEMES:
        raise UnsupportedURLSchemeError(parsed_url.scheme)

    if parsed_url.netloc not in ALLOWED_NETLOCS:
        raise UnsupportedURLNetlocError(parsed_url.netloc)

    path = parsed_url.path

    if path.endswith("/watch"):
        query = parsed_url.query
        parsed_query = parse_qs(query)
        if "v" in parsed_query:
            ids = parsed_query["v"]
            video_id = ids if isinstance(ids, str) else ids[0]
        else:
            raise NoVideoIDFoundError(url)
    else:
        path = parsed_url.path.lstrip("/")
        video_id = path.split("/")[-1]

    if len(video_id) != 11:  # Video IDs are 11 characters long
        raise VideoIDError(video_id)

    return video_id


class YoutubeLoader(Loader):
    def __init__(self, languages: list[str] | None = None) -> None:
        self.languages = languages or DEFAULT_LANGUAGES

    @timeout_decorator.timeout(20)
    def load(self, url: str) -> str:
        video_id = parse_video_id(url)

        transcript_pieces: list[dict[str, str | float]] = YouTubeTranscriptApi().get_transcript(
            video_id, self.languages
        )

        lines = []
        for transcript_piece in transcript_pieces:
            text = str(transcript_piece.get("text", "")).strip()
            if text:
                lines.append(text)
        return "\n".join(lines)
