from __future__ import annotations

from collections.abc import Callable

import pytest

from kabigon import cli
from kabigon.core.errors import MissingRequirementError
from kabigon.core.loader import Loader


class DummyLoader(Loader):
    def __init__(self, name: str, result: str = "ok") -> None:
        self.name = name
        self.result = result
        self.calls: list[str] = []

    async def load(self, url: str) -> str:  # pragma: no cover - trivial
        self.calls.append(url)
        return self.result


class DummyLoadChain:
    def load_sync(self) -> str:
        return "ok"


def make_defs(
    *defs: tuple[str, str, Callable[[], Loader], tuple[str, ...]],
) -> list[tuple[str, str, Callable[[], Loader], tuple[str, ...]]]:
    return list(defs)


def test_cli_list_outputs_loaders(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    specs = make_defs(
        ("alpha", "Alpha loader", lambda: DummyLoader("alpha"), ()),
        ("beta", "Beta loader", lambda: DummyLoader("beta"), ()),
    )
    monkeypatch.setattr(cli, "LOADER_DEFS", specs)

    cli.main(["--list"])

    captured = capsys.readouterr()
    assert "alpha - Alpha loader" in captured.out
    assert "beta - Beta loader" in captured.out


def test_cli_loader_selection_uses_load_chain_runtime(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    specs = make_defs(
        ("first", "First loader", lambda: DummyLoader("first"), ()),
        ("second", "Second loader", lambda: DummyLoader("second"), ()),
    )
    monkeypatch.setattr(cli, "LOADER_DEFS", specs)

    def fake_resolve(
        url: str,
        loader_names: list[str],
        get_factory: Callable[[str], Callable[[], Loader]],
        get_requirements: Callable[[str], tuple[str, ...]],
    ):
        assert url == "https://example.com"
        assert loader_names == ["first", "second"]
        assert isinstance(get_factory("first")(), DummyLoader)
        assert get_requirements("first") == ()
        return DummyLoadChain()

    monkeypatch.setattr(cli, "resolve_explicit_load_chain", fake_resolve)

    cli.main(["--loader", "first,second", "https://example.com"])

    assert capsys.readouterr().out.strip() == "ok"


def test_cli_default_pipeline_uses_load_url_sync(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_load(url: str) -> str:
        assert url == "https://example.com"
        return "content"

    monkeypatch.setattr(cli, "load_url_sync", fake_load)

    cli.main(["https://example.com"])

    assert capsys.readouterr().out.strip() == "content"


def test_cli_loader_selection_reports_missing_requirements(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    with pytest.raises(MissingRequirementError, match="FIRECRAWL_API_KEY"):
        cli.main(["--loader", "firecrawl", "https://example.com"])
