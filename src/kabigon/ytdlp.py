import functools
import hashlib
import os
import subprocess
import tempfile
from typing import Final

import numpy as np
import timeout_decorator
import whisper
import yt_dlp
from loguru import logger

from .loader import Loader

try:
    import mlx_whisper  # noqa: F401

    _mlx_whisper_installed = True
except ImportError:
    _mlx_whisper_installed = False


DEFAULT_FFMPEG_PATH: Final[str] = "ffmpeg"


def hash_url(url: str) -> str:
    return hashlib.sha512(url.encode("utf-8")).hexdigest()


def get_ffmpeg_path() -> str:
    path = os.getenv("FFMPEG_PATH")
    if not path:
        path = DEFAULT_FFMPEG_PATH
        logger.warning("FFMPEG_PATH not set, using default: {}", DEFAULT_FFMPEG_PATH)

    return path


def download_audio(url: str) -> str:
    ffmpeg_path = get_ffmpeg_path()

    filename = os.path.join(
        tempfile.gettempdir(),
        hash_url(url),
    )

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
        "ffmpeg_location": ffmpeg_path,
        "match_filter": yt_dlp.match_filter_func(["!is_live"]),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return filename + ".mp3"


def load_audio(file: str, sr: int = 16000):
    """
    Open an audio file and read as mono waveform, resampling as necessary

    Parameters
    ----------
    file: str
        The audio file to open

    sr: int
        The sample rate to resample the audio if necessary

    Returns
    -------
    A NumPy array containing the audio waveform, in float32 dtype.
    """
    ffmpeg_path = get_ffmpeg_path()

    # This launches a subprocess to decode audio while down-mixing
    # and resampling as necessary.  Requires the ffmpeg CLI in PATH.
    # fmt: off
    cmd = [
        ffmpeg_path,
        "-nostdin",
        "-threads", "0",
        "-i", file,
        "-f", "s16le",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        "-ar", str(sr),
        "-"
    ]
    # fmt: on
    try:
        out = subprocess.run(cmd, capture_output=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0


@functools.cache
def _load_whisper_model() -> whisper.Whisper:
    return whisper.load_model("tiny")


def _transcribe(audio: np.ndarray) -> dict:
    if _mlx_whisper_installed:
        return mlx_whisper.transcribe(audio, path_or_hf_repo="mlx-community/whisper-tiny")

    model = _load_whisper_model()
    return model.transcribe(audio)


class YtdlpLoader(Loader):
    @timeout_decorator.timeout(300)
    def load(self, url: str) -> str:
        audio_file = download_audio(url)
        audio = load_audio(audio_file)

        # Clean up the audio file
        os.remove(audio_file)

        result = _transcribe(audio)
        return result.get("text", "")
