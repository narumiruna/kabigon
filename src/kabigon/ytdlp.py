import hashlib
import os
import tempfile

import yt_dlp
from loguru import logger

from .loader import Loader


def download_audio(url: str) -> str:
    filename = os.path.join(tempfile.gettempdir(), hashlib.sha512(url.encode("utf-8")).hexdigest())

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": filename,
        "ffmpeg_location": os.getenv("FFMPEG_PATH", "ffmpeg"),
        "match_filter": yt_dlp.match_filter_func(["!is_live"]),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return filename + ".mp3"


class YtdlpLoader(Loader):
    def __init__(self, model: str = "tiny") -> None:
        try:
            import whisper
        except ImportError as e:
            raise ImportError(
                "OpenAI Whisper not installed. Please install it with `pip install openai-whisper`."
            ) from e

        self.model = whisper.load_model(model)
        self.load_audio = whisper.load_audio

    def load(self, url: str) -> str:
        audio_file = download_audio(url)
        audio = self.load_audio(audio_file)

        # Clean up the audio file
        os.remove(audio_file)

        logger.info("Transcribing audio file: {}", audio_file)
        result = self.model.transcribe(audio)
        return result.get("text", "")
