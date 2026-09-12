from __future__ import annotations

import os
import subprocess
import sys

import pytest

from kabigon import loader_registry
from kabigon.core.errors import MissingDependencyError


def test_inspection_does_not_import_optional_sdks_in_fresh_process() -> None:
    code = """
import json
import sys
import kabigon
kabigon.available_loaders()
kabigon.explain_plan('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
blocked = ('playwright', 'firecrawl', 'yt_dlp', 'whisper')
print(json.dumps(sorted(name for name in sys.modules if name.split('.')[0] in blocked)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert completed.stdout.strip() == "[]"


def test_documented_direct_loader_import_remains_available() -> None:
    from kabigon.loaders import HttpxLoader

    assert HttpxLoader.__name__ == "HttpxLoader"


def test_requested_factory_normalizes_only_declared_missing_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_firecrawl(name: str):
        if name == "kabigon.loaders.firecrawl":
            raise ModuleNotFoundError("No module named 'firecrawl'", name="firecrawl")
        raise AssertionError(name)

    monkeypatch.setattr(loader_registry.importlib, "import_module", missing_firecrawl)

    with pytest.raises(MissingDependencyError, match="firecrawl-py"):
        loader_registry.get_loader_factory("firecrawl")()


def test_requested_factory_does_not_hide_unrelated_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_import(_name: str):
        raise ModuleNotFoundError("No module named 'broken_nested'", name="broken_nested")

    monkeypatch.setattr(loader_registry.importlib, "import_module", broken_import)

    with pytest.raises(ModuleNotFoundError, match="broken_nested"):
        loader_registry.get_loader_factory("firecrawl")()
