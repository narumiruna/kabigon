from __future__ import annotations

from collections.abc import Callable

import pytest
from typer.testing import CliRunner

from kabigon import cli
from kabigon.core.loader import Loader


class DummyLoader(Loader):
    def __init__(self, name: str, result: str = "ok") -> None:
        self.name = name
        self.result = result
        self.calls: list[str] = []

    async def load(self, url: str) -> str:  # pragma: no cover - trivial
        self.calls.append(url)
        return self.result


def make_specs(*specs: tuple[str, str, Callable[[], Loader]]) -> list[cli.LoaderSpec]:
    return [cli.LoaderSpec(name=name, description=desc, factory=factory) for name, desc, factory in specs]


def test_cli_list_outputs_loaders(monkeypatch: pytest.MonkeyPatch) -> None:
    specs = make_specs(
        ("alpha", "Alpha loader", lambda: DummyLoader("alpha")),
        ("beta", "Beta loader", lambda: DummyLoader("beta")),
    )
    monkeypatch.setattr(cli, "LOADER_SPECS", specs)

    runner = CliRunner()
    result = runner.invoke(cli.app, ["--list"])

    assert result.exit_code == 0
    assert "alpha - Alpha loader" in result.stdout
    assert "beta - Beta loader" in result.stdout


def test_cli_loader_compose_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class FirstLoader(Loader):
        async def load(self, url: str) -> str:
            calls.append("first")
            return ""

    class SecondLoader(Loader):
        async def load(self, url: str) -> str:
            calls.append("second")
            return "ok"

    specs = make_specs(
        ("first", "First loader", lambda: FirstLoader()),
        ("second", "Second loader", lambda: SecondLoader()),
    )
    monkeypatch.setattr(cli, "LOADER_SPECS", specs)

    runner = CliRunner()
    result = runner.invoke(cli.app, ["--loader", "first,second", "https://example.com"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "ok"
    assert calls == ["first", "second"]


def test_cli_default_pipeline_uses_load_url_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_load(url: str) -> str:
        assert url == "https://example.com"
        return "content"

    monkeypatch.setattr(cli, "load_url_sync", fake_load)

    runner = CliRunner()
    result = runner.invoke(cli.app, ["https://example.com"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "content"
