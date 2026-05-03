import asyncio
import contextlib
import logging
import os
import uuid
from pathlib import Path
from typing import Any
from typing import cast

import yt_dlp

from kabigon.core.errors import WhisperNotInstalledError
from kabigon.core.loader import Loader

logger = logging.getLogger(__name__)


def download_audio(url: str, outtmpl: str | None = None) -> None:
    ydl_opts: dict[str, Any] = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    if outtmpl is not None:
        ydl_opts["outtmpl"] = outtmpl

    ffmpeg_path = os.getenv("FFMPEG_PATH")
    if ffmpeg_path is not None:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    logger.info("[YtdlpLoader] Downloading audio from URL: %s", url)
    logger.debug("[YtdlpLoader] yt-dlp options: %s", ydl_opts)
    with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
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
        logger.info("[YtdlpLoader] Processing URL: %s", url)
        outtmpl = uuid.uuid4().hex[:20]
        path = str(Path(outtmpl).with_suffix(".mp3"))
        download_audio(url, outtmpl=outtmpl)
        result: dict[str, Any] = {"text": ""}

        try:
            audio = self.load_audio(path)
            logger.info("[YtdlpLoader] Transcribing audio file")
            logger.debug("[YtdlpLoader] Audio file path: %s", path)
            result = self.model.transcribe(audio)
        finally:
            # Clean up the audio file
            with contextlib.suppress(OSError):
                Path(path).unlink(missing_ok=True)

        text = result.get("text", "")
        if isinstance(text, str):
            logger.info("[YtdlpLoader] Extracted transcript content (%s chars)", len(text))
            return text
        joined_text = "\n".join(str(item) for item in text)
        logger.info("[YtdlpLoader] Extracted transcript content (%s chars)", len(joined_text))
        return joined_text

    async def load(self, url: str) -> str:
        return await asyncio.to_thread(self.load_sync, url)
