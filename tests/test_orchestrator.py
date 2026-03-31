import pytest

from kabigon.application import service as orchestrator_module
from kabigon.domain.models import ContentType
from kabigon.domain.models import LoaderPlan
from kabigon.domain.models import RetrievalContext
from kabigon.domain.models import RetrievalStrategy


def test_resolve_loader_plan_uses_single_context_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {
        "context": 0,
        "strategy": 0,
        "plan": 0,
    }

    def fake_build_retrieval_context(url: str) -> RetrievalContext:
        calls["context"] += 1
        return RetrievalContext(
            url=url,
            pipeline_name="youtube",
            targeted_loaders=("youtube", "youtube-ytdlp"),
            content_type=ContentType.YOUTUBE_VIDEO,
        )

    def fake_build_strategy_from_context(context: RetrievalContext) -> RetrievalStrategy:
        calls["strategy"] += 1
        return RetrievalStrategy(
            content_type=context.content_type,
            primary_loaders=context.targeted_loaders,
        )

    def fake_build_loader_plan(strategy: RetrievalStrategy, default_fallback: tuple[str, ...]) -> LoaderPlan:
        calls["plan"] += 1
        assert strategy.primary_loaders == ("youtube", "youtube-ytdlp")
        assert "playwright-fast" in default_fallback
        return LoaderPlan(loader_names=("youtube", "youtube-ytdlp", "playwright-fast"))

    monkeypatch.setattr(orchestrator_module, "build_retrieval_context", fake_build_retrieval_context)
    monkeypatch.setattr(orchestrator_module, "build_strategy_from_context", fake_build_strategy_from_context)
    monkeypatch.setattr(orchestrator_module, "build_loader_plan", fake_build_loader_plan)

    plan = orchestrator_module.resolve_loader_plan("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert plan.loader_names == ("youtube", "youtube-ytdlp", "playwright-fast")
    assert calls == {"context": 1, "strategy": 1, "plan": 1}


def test_resolve_targeted_loader_names_from_context() -> None:
    targeted = orchestrator_module.resolve_targeted_loader_names("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert targeted == ["youtube", "youtube-ytdlp"]


def test_public_resolvers_delegate_to_single_resolve(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_resolve(url: str):
        calls["count"] += 1
        return orchestrator_module._Resolution(
            context=RetrievalContext(
                url=url,
                pipeline_name="youtube",
                targeted_loaders=("youtube", "youtube-ytdlp"),
                content_type=ContentType.YOUTUBE_VIDEO,
            ),
            strategy=RetrievalStrategy(
                content_type=ContentType.YOUTUBE_VIDEO,
                primary_loaders=("youtube", "youtube-ytdlp"),
            ),
            plan=LoaderPlan(loader_names=("youtube", "youtube-ytdlp", "playwright-fast")),
        )

    monkeypatch.setattr(orchestrator_module, "_resolve", fake_resolve)

    assert orchestrator_module.resolve_context("u").pipeline_name == "youtube"
    assert orchestrator_module.resolve_strategy("u").primary_loaders == ("youtube", "youtube-ytdlp")
    assert orchestrator_module.resolve_loader_plan("u").loader_names == (
        "youtube",
        "youtube-ytdlp",
        "playwright-fast",
    )
    assert orchestrator_module.resolve_targeted_loader_names("u") == ["youtube", "youtube-ytdlp"]
    assert orchestrator_module.resolve_execution_plan_loader_names("u") == [
        "youtube",
        "youtube-ytdlp",
        "playwright-fast",
    ]

    assert calls["count"] == 5
