from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import tempfile
import threading
from collections.abc import Awaitable
from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import cast

import yt_dlp

from kabigon.core.errors import WhisperNotInstalledError
from kabigon.core.loader import Loader

from .audio import load_audio

logger = logging.getLogger(__name__)
BlockingRunner = Callable[[Callable[[], str]], Awaitable[str]]
ModelProvider = Callable[[str], tuple[Any, threading.Lock]]


def download_audio(url: str, outtmpl: str | None = None) -> None:
    ydl_opts: dict[str, Any] = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
    }
    if outtmpl is not None:
        ydl_opts["outtmpl"] = outtmpl
    ffmpeg_path = os.getenv("FFMPEG_PATH")
    if ffmpeg_path is not None:
        ydl_opts["ffmpeg_location"] = ffmpeg_path
    with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
        ydl.download([url])


class YtdlpLoader(Loader):
    def __init__(
        self,
        model: str = "tiny",
        run_blocking: BlockingRunner | None = None,
        model_provider: ModelProvider | None = None,
    ) -> None:
        self.model_name = model
        self.run_blocking = run_blocking
        self.model_provider = model_provider
        self._model: Any | None = None
        self._model_lock = threading.Lock()

    def _get_model(self) -> tuple[Any, threading.Lock]:
        if self.model_provider is not None:
            return self.model_provider(self.model_name)
        with self._model_lock:
            if self._model is None:
                try:
                    import whisper
                except ImportError as error:
                    raise WhisperNotInstalledError from error
                self._model = whisper.load_model(self.model_name)
        return self._model, self._model_lock

    def load_sync(self, url: str) -> str:
        model, model_lock = self._get_model()
        with tempfile.TemporaryDirectory(prefix="kabigon-audio-") as directory:
            outtmpl = str(Path(directory) / "audio")
            path = str(Path(outtmpl).with_suffix(".mp3"))
            try:
                download_audio(url, outtmpl=outtmpl)
                audio = load_audio(path, ffmpeg_path=os.getenv("FFMPEG_PATH"))
                with model_lock:
                    result: dict[str, Any] = model.transcribe(audio)
            finally:
                with contextlib.suppress(OSError):
                    Path(path).unlink(missing_ok=True)

        text = result.get("text", "")
        if isinstance(text, str):
            return text
        return "\n".join(str(item) for item in text)

    async def load(self, url: str) -> str:
        def operation() -> str:
            return self.load_sync(url)

        if self.run_blocking is not None:
            return await self.run_blocking(operation)
        return await asyncio.to_thread(operation)
