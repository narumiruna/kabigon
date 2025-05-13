import hashlib
import os
import tempfile
from pathlib import Path

import yt_dlp
from loguru import logger

from .loader import Loader


def download_audio(url: str, outtmpl: str | None = None) -> None:
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "match_filter": yt_dlp.match_filter_func(["!is_live"]),
    }

    if outtmpl is not None:
        ydl_opts["outtmpl"] = outtmpl

    ffmpeg_path = os.getenv("FFMPEG_PATH")
    if ffmpeg_path is None:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


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
        temp_dir = Path(tempfile.gettempdir())
        outtmpl = hashlib.sha512(url.encode("utf-8")).hexdigest()
        path = (temp_dir / outtmpl).with_suffix(".mp3")

        download_audio(url, outtmpl=outtmpl)
        audio = self.load_audio(path)

        # Clean up the audio file
        os.remove(path)

        logger.info("Transcribing audio file: {}", path)
        result = self.model.transcribe(audio)
        return result.get("text", "")
