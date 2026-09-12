"""Decode audio with a configurable FFmpeg executable for Whisper."""

from __future__ import annotations

import contextlib
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

DEFAULT_DECODE_TIMEOUT = 120.0


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def load_audio(
    path: str,
    *,
    ffmpeg_path: str | None = None,
    timeout: float = DEFAULT_DECODE_TIMEOUT,
) -> NDArray[np.float32]:
    """Return mono 16 kHz samples without changing PATH or Whisper globals."""
    import numpy as np

    executable = ffmpeg_path or "ffmpeg"
    if ffmpeg_path and Path(ffmpeg_path).is_dir():
        executable = str(Path(ffmpeg_path) / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg"))

    command = [
        executable,
        "-nostdin",
        "-threads",
        "0",
        "-i",
        path,
        "-f",
        "s16le",
        "-ac",
        "1",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except BaseException:
        _stop_process(process)
        raise
    if process.returncode:
        with contextlib.suppress(ProcessLookupError):
            _stop_process(process)
        raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)
    return np.frombuffer(stdout, dtype="<i2").astype(np.float32) / 32768.0
