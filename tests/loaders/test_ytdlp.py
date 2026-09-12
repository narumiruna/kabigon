import asyncio
import os
import subprocess
import threading
import time
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest

from kabigon.client import KabigonClient
from kabigon.loaders import audio as audio_module
from kabigon.loaders import ytdlp
from kabigon.loaders.ytdlp import YtdlpLoader
from kabigon.loaders.ytdlp import download_audio


def test_ytdlp_constructor_does_not_initialize_whisper(monkeypatch: pytest.MonkeyPatch) -> None:
    import whisper

    monkeypatch.setattr(whisper, "load_model", lambda _name: pytest.fail("constructor must stay lazy"))

    YtdlpLoader()


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

    class FakeProcess:
        returncode = 0

        def communicate(self, timeout: float):
            assert timeout == 120.0
            return b"\x00\x00\x00\x40", b""

    def fake_popen(command, **kwargs):
        commands.append(command)
        assert command[0] == executable
        assert "-nostdin" in command
        assert command[command.index("-ar") + 1] == "16000"
        assert command[command.index("-ac") + 1] == "1"
        assert command[command.index("-f") + 1] == "s16le"
        assert kwargs == {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    original_whisper_run = whisper.audio.run
    environment = dict(os.environ)
    model, downloads = transcription

    assert YtdlpLoader().load_sync("https://example.com/video") == "transcript"

    assert len(commands) == 1
    audio = model.transcribe.call_args.args[0]
    assert audio.dtype == np.float32
    np.testing.assert_array_equal(audio, np.array([0.0, 0.5], dtype=np.float32))
    assert downloads and all(not path.exists() for path in downloads)
    assert dict(os.environ) == environment
    assert whisper.audio.run is original_whisper_run


def test_client_reuses_and_serializes_whisper_model(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import whisper

    loads = 0
    active = 0
    max_active = 0
    guard = threading.Lock()

    class Model:
        def transcribe(self, _audio):
            nonlocal active, max_active
            with guard:
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.02)
            with guard:
                active -= 1
            return {"text": "shared"}

    def load_model(_name: str) -> Model:
        nonlocal loads
        loads += 1
        return Model()

    def fake_download(_url: str, outtmpl: str) -> None:
        Path(outtmpl).with_suffix(".mp3").write_bytes(b"audio")

    monkeypatch.setattr(whisper, "load_model", load_model)
    monkeypatch.setattr(ytdlp, "download_audio", fake_download)
    monkeypatch.setattr(ytdlp, "load_audio", lambda *_args, **_kwargs: np.array([0], dtype=np.float32))
    monkeypatch.setattr(ytdlp.tempfile, "tempdir", str(tmp_path))

    async def scenario() -> None:
        async with KabigonClient(worker_limit=2) as client:
            first = YtdlpLoader(run_blocking=client.run_blocking, model_provider=client.whisper_model)
            second = YtdlpLoader(run_blocking=client.run_blocking, model_provider=client.whisper_model)
            assert await asyncio.gather(first.load("https://example.com/1"), second.load("https://example.com/2")) == [
                "shared",
                "shared",
            ]

    asyncio.run(scenario())
    assert loads == 1
    assert max_active == 1


def test_download_failure_removes_all_temporary_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import whisper

    model = Mock()
    monkeypatch.setattr(whisper, "load_model", lambda _name: model)
    monkeypatch.setattr(ytdlp.tempfile, "tempdir", str(tmp_path))

    def fail_download(_url: str, outtmpl: str) -> None:
        Path(outtmpl).with_suffix(".part").write_bytes(b"partial")
        raise RuntimeError("download failed")

    monkeypatch.setattr(ytdlp, "download_audio", fail_download)

    with pytest.raises(RuntimeError, match="download failed"):
        YtdlpLoader().load_sync("https://example.com/video")

    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("error", [subprocess.TimeoutExpired("ffmpeg", 1), KeyboardInterrupt()])
def test_audio_decode_terminates_subprocess_on_timeout_or_cancellation(
    monkeypatch: pytest.MonkeyPatch, error: BaseException
) -> None:
    process = Mock()
    process.communicate.side_effect = error
    monkeypatch.setattr(subprocess, "Popen", lambda *_args, **_kwargs: process)

    with pytest.raises(type(error)):
        audio_module.load_audio("audio.mp3", timeout=1)

    process.terminate.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)


@pytest.mark.parametrize("error_type", [FileNotFoundError, subprocess.CalledProcessError])
def test_transcription_cleans_up_when_decoding_fails(
    monkeypatch: pytest.MonkeyPatch, transcription, error_type: type[Exception]
) -> None:
    def fail_decode(command, **_kwargs):
        if error_type is FileNotFoundError:
            raise FileNotFoundError(command[0])

        class FailedProcess:
            returncode = 1

            def communicate(self, timeout: float):
                return b"", b"invalid audio"

            def terminate(self) -> None:
                return None

            def wait(self, timeout: float | None = None) -> None:
                return None

        return FailedProcess()

    monkeypatch.setattr(subprocess, "Popen", fail_decode)
    model, downloads = transcription

    with pytest.raises(error_type):
        YtdlpLoader().load_sync("https://example.com/video")

    model.transcribe.assert_not_called()
    assert downloads and all(not path.exists() for path in downloads)
