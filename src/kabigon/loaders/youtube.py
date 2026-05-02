import asyncio
import logging

from youtube_transcript_api import YouTubeTranscriptApi

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderNotApplicableError
from kabigon.core.loader import Loader
from kabigon.sources.applicability import NoVideoIDFoundError
from kabigon.sources.applicability import UnsupportedURLNetlocError
from kabigon.sources.applicability import UnsupportedURLSchemeError
from kabigon.sources.applicability import VideoIDError
from kabigon.sources.applicability import parse_youtube_video_target

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGES = [
    # 中文
    "zh-TW",
    "zh-Hant",
    "zh",
    "zh-Hans",
    # 日韓英
    "ja",
    "ko",
    "en",
    # 歐洲主要語言
    "fr",  # French
    "de",  # German
    "es",  # Spanish
    "it",  # Italian
    "pt",  # Portuguese
    "pt-BR",  # Portuguese (Brazil)
    "nl",  # Dutch
    "sv",  # Swedish
    "pl",  # Polish
    # 東南亞
    "th",  # Thai
    "vi",  # Vietnamese
    "id",  # Indonesian
    "ms",  # Malay
    "fil",  # Filipino / Tagalog
    # 其他常見
    "ru",  # Russian
    "ar",  # Arabic
    "hi",  # Hindi
]


def parse_video_id(url: str) -> str:
    """Parse and extract the video ID from a YouTube URL.

    Supports various YouTube URL formats including:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - https://music.youtube.com/watch?v=VIDEO_ID
    - https://www.youtube-nocookie.com/watch?v=VIDEO_ID
    - https://vid.plus/VIDEO_ID

    Args:
        url: YouTube video URL.

    Returns:
        11-character video ID.

    Raises:
        UnsupportedURLSchemeError: If URL scheme is not http or https.
        UnsupportedURLNetlocError: If URL domain is not a supported YouTube domain.
        NoVideoIDFoundError: If no video ID parameter found in the URL.
        VideoIDError: If extracted video ID is not exactly 11 characters.

    Example:
        >>> parse_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        >>> parse_video_id("https://youtu.be/dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
    """
    return parse_youtube_video_target(url).video_id


def check_youtube_url(url: str) -> None:
    """Validate that the given URL is a supported YouTube URL.

    This delegates to ``parse_video_id`` to ensure that URL validation
    (including scheme and netloc checks) is implemented in a single place.
    Any validation failures are surfaced as ``ValueError`` to maintain
    the previous public interface of this function.

    Args:
        url: YouTube video URL to validate.

    Raises:
        ValueError: If URL is invalid or not a supported YouTube URL.
    """
    try:
        # We only care about validation here; the caller does not need the ID.
        parse_video_id(url)
    except (UnsupportedURLSchemeError, UnsupportedURLNetlocError, NoVideoIDFoundError, VideoIDError) as exc:
        raise ValueError(str(exc)) from exc


class YoutubeLoader(Loader):
    def __init__(self, languages: list[str] | None = None) -> None:
        self.languages = languages or DEFAULT_LANGUAGES

    def load_sync(self, url: str) -> str:
        logger.debug("[YoutubeLoader] Processing URL: %s", url)

        try:
            video_id = parse_video_id(url)
        except (UnsupportedURLSchemeError, UnsupportedURLNetlocError, NoVideoIDFoundError, VideoIDError) as e:
            logger.debug("[YoutubeLoader] URL validation failed: %s", e)
            raise LoaderNotApplicableError("YoutubeLoader", url, str(e)) from e

        logger.debug("[YoutubeLoader] Extracted video ID: %s", video_id)

        try:
            fetched = YouTubeTranscriptApi().fetch(video_id, self.languages)
        except Exception as e:
            logger.warning("[YoutubeLoader] Failed to fetch transcript for %s: %s", video_id, e)
            raise LoaderContentError(
                "YoutubeLoader",
                url,
                f"Failed to fetch transcript: {e}",
                "The video may not have captions available, or captions may be disabled.",
            ) from e

        lines = []
        for snippet in fetched.snippets:
            text = str(snippet.text).strip()
            if text:
                lines.append(text)

        result = "\n".join(lines)
        if not result:
            logger.warning("[YoutubeLoader] Empty transcript for %s", video_id)
            raise LoaderContentError(
                "YoutubeLoader", url, "Transcript is empty", "The video may not have any captions."
            )

        logger.debug("[YoutubeLoader] Successfully extracted %s transcript lines", len(lines))
        return result

    async def load(self, url: str) -> str:
        return await asyncio.to_thread(self.load_sync, url)
