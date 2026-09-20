from __future__ import annotations

from collections.abc import Callable

import pytest

from kabigon import cli
from kabigon.core.errors import MissingRequirementError
from kabigon.core.loader import Loader
from kabigon.loader_registry import LoaderDef


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


def make_defs(*defs: tuple[str, str, tuple[str, ...]]) -> list[LoaderDef]:
    return [
        LoaderDef(
            name,
            description,
            __name__,
            "DummyLoader",
            "generic_web",
            requirements=requirements,
            kwargs=(("name", name),),
        )
        for name, description, requirements in defs
    ]


def test_cli_list_outputs_loaders(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    specs = make_defs(
        ("alpha", "Alpha loader", ()),
        ("beta", "Beta loader", ()),
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
        ("first", "First loader", ()),
        ("second", "Second loader", ()),
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


def test_registry_metadata_controls_cli_visibility(capsys: pytest.CaptureFixture[str]) -> None:
    cli._print_loader_list()
    output = capsys.readouterr().out

    assert "pi-session -" in output
    assert "ltn -" in output
    assert "curl-cffi -" in output
    assert "playwright-networkidle -" not in output
    assert "playwright-fast -" not in output


def test_cli_loader_selection_reports_missing_requirements(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    with pytest.raises(MissingRequirementError, match="FIRECRAWL_API_KEY"):
        cli.main(["--loader", "firecrawl", "https://example.com"])
