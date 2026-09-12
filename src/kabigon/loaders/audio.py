"""Decode audio with a configurable FFmpeg executable for Whisper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


def load_audio(path: str, *, ffmpeg_path: str | None = None) -> NDArray[np.float32]:
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
    result = subprocess.run(command, capture_output=True, check=True)
    return np.frombuffer(result.stdout, dtype="<i2").astype(np.float32) / 32768.0
