import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from kabigon.loaders import ytdlp
from kabigon.loaders.ytdlp import YtdlpLoader
from kabigon.loaders.ytdlp import download_audio


def test_download_audio_disables_playlist_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    options: dict[str, object] = {}
    downloaded: list[str] = []

    class FakeYdl:
        def __init__(self, opts) -> None:
            options.update(opts)

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def download(self, urls) -> None:
            downloaded.extend(urls)

    monkeypatch.setattr(ytdlp.yt_dlp, "YoutubeDL", FakeYdl)
    monkeypatch.setenv("FFMPEG_PATH", "/custom/ffmpeg")
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLexample"

    download_audio(url, outtmpl="one-audio-file")

    assert options["noplaylist"] is True
    assert options["outtmpl"] == "one-audio-file"
    assert options["ffmpeg_location"] == "/custom/ffmpeg"
    assert downloaded == [url]


@pytest.fixture
def transcription(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    import whisper

    model = Mock()
    model.transcribe.return_value = {"text": "transcript"}
    monkeypatch.setattr(whisper, "load_model", lambda name: model)
    monkeypatch.chdir(tmp_path)
    downloads: list[Path] = []

    def fake_download(url: str, outtmpl: str) -> None:
        path = Path(outtmpl).with_suffix(".mp3")
        path.write_bytes(b"downloaded audio")
        downloads.append(path)

    monkeypatch.setattr(ytdlp, "download_audio", fake_download)
    return model, downloads


@pytest.mark.parametrize("location", ["default", "executable", "directory"])
def test_transcription_honors_ffmpeg_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, transcription, location: str
) -> None:
    import whisper.audio

    if location == "default":
        monkeypatch.delenv("FFMPEG_PATH", raising=False)
        executable = "ffmpeg"
    elif location == "executable":
        executable = str(tmp_path / "custom ffmpeg")
        monkeypatch.setenv("FFMPEG_PATH", executable)
    else:
        directory = tmp_path / "custom bin"
        directory.mkdir()
        executable = str(directory / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg"))
        monkeypatch.setenv("FFMPEG_PATH", str(directory))

    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        assert command[0] == executable
        assert "-nostdin" in command
        assert command[command.index("-ar") + 1] == "16000"
        assert command[command.index("-ac") + 1] == "1"
        assert command[command.index("-f") + 1] == "s16le"
        assert kwargs == {"capture_output": True, "check": True}
        return SimpleNamespace(stdout=b"\x00\x00\x00\x40", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(whisper.audio, "run", fake_run)
    environment = dict(os.environ)
    model, downloads = transcription

    assert YtdlpLoader().load_sync("https://example.com/video") == "transcript"

    assert len(commands) == 1
    audio = model.transcribe.call_args.args[0]
    assert audio.dtype == np.float32
    np.testing.assert_array_equal(audio, np.array([0.0, 0.5], dtype=np.float32))
    assert downloads and all(not path.exists() for path in downloads)
    assert dict(os.environ) == environment
    assert whisper.audio.run is fake_run


@pytest.mark.parametrize("error_type", [FileNotFoundError, subprocess.CalledProcessError])
def test_transcription_cleans_up_when_decoding_fails(
    monkeypatch: pytest.MonkeyPatch, transcription, error_type: type[Exception]
) -> None:
    import whisper.audio

    def fail_decode(command, **kwargs):
        if error_type is subprocess.CalledProcessError:
            raise subprocess.CalledProcessError(1, command, stderr=b"invalid audio")
        raise FileNotFoundError(command[0])

    monkeypatch.setattr(subprocess, "run", fail_decode)
    monkeypatch.setattr(whisper.audio, "run", fail_decode)
    model, downloads = transcription

    with pytest.raises(error_type):
        YtdlpLoader().load_sync("https://example.com/video")

    model.transcribe.assert_not_called()
    assert downloads and all(not path.exists() for path in downloads)
