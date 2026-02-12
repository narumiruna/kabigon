import logging
import os
import uuid
from pathlib import Path

import yt_dlp

from kabigon.core.exception import WhisperNotInstalledError
from kabigon.core.loader import Loader

logger = logging.getLogger(__name__)


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
    if ffmpeg_path is not None:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    logger.info("Downloading audio from URL: %s with options: %s", url, ydl_opts)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


class YtdlpLoader(Loader):
    def __init__(self, model: str = "tiny") -> None:
        try:
            import whisper
        except ImportError as e:
            raise WhisperNotInstalledError from e

        self.model = whisper.load_model(model)
        self.load_audio = whisper.load_audio

    def load_sync(self, url: str) -> str:
        outtmpl = uuid.uuid4().hex[:20]
        path = str(Path(outtmpl).with_suffix(".mp3"))
        download_audio(url, outtmpl=outtmpl)

        try:
            audio = self.load_audio(path)
            logger.info("Transcribing audio file: %s", path)
            result = self.model.transcribe(audio)
        finally:
            # Clean up the audio file
            Path(path).unlink()

        return result.get("text", "")
