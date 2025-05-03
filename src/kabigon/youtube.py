import aioytt
import aioytt.video_id
from youtube_transcript_api import YouTubeTranscriptApi

from .loader import Loader

DEFAULT_LANGUAGES = ["zh-TW", "zh-Hant", "zh", "zh-Hans", "ja", "en", "ko"]


class YoutubeLoader(Loader):
    def __init__(self, languages: list[str] | None = None) -> None:
        self.languages = languages or DEFAULT_LANGUAGES

    def load(self, url: str) -> str:
        video_id = aioytt.video_id.parse_video_id(url)

        transcript_pieces: list[dict[str, str | float]] = YouTubeTranscriptApi().get_transcript(
            video_id, self.languages
        )

        lines = []
        for transcript_piece in transcript_pieces:
            text = str(transcript_piece.get("text", "")).strip()
            if text:
                lines.append(text)
        return "\n".join(lines)

    async def async_load(self, url: str) -> str:
        transcript = await aioytt.get_transcript_from_url(url)
        lines = []
        for piece in transcript:
            text = piece.text.strip()
            if text:
                lines.append(text)
        return "\n".join(lines)
