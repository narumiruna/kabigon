import pytest

from kabigon.retrieval import strategy as strategy_module
from kabigon.retrieval.classifier import classify_pipeline_name
from kabigon.retrieval.classifier import classify_url
from kabigon.retrieval.models import ContentType
from kabigon.retrieval.planner import build_loader_plan
from kabigon.retrieval.strategy import build_retrieval_context
from kabigon.retrieval.strategy import build_strategy


def test_classify_url_youtube() -> None:
    content_type = classify_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert content_type == ContentType.YOUTUBE_VIDEO


def test_classify_url_unknown() -> None:
    content_type = classify_url("https://example.com/some-page")
    assert content_type == ContentType.GENERIC_WEB


def test_classify_pipeline_name_unknown_is_generic_web() -> None:
    content_type = classify_pipeline_name(None)
    assert content_type == ContentType.GENERIC_WEB


def test_build_retrieval_context_youtube() -> None:
    context = build_retrieval_context("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert context.pipeline_name == "youtube"
    assert context.targeted_loaders == ("youtube", "youtube-ytdlp")
    assert context.content_type == ContentType.YOUTUBE_VIDEO


def test_build_strategy_youtube_primary_loaders() -> None:
    strategy = build_strategy("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert strategy.content_type == ContentType.YOUTUBE_VIDEO
    assert strategy.primary_loaders == ("youtube", "youtube-ytdlp")


def test_build_strategy_resolves_routing_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"pipeline": 0, "targeted": 0}

    def fake_resolve_pipeline_name(url: str) -> str | None:
        calls["pipeline"] += 1
        return "youtube"

    def fake_resolve_targeted_loader_names(url: str) -> list[str]:
        calls["targeted"] += 1
        return ["youtube", "youtube-ytdlp"]

    monkeypatch.setattr(strategy_module, "resolve_pipeline_name", fake_resolve_pipeline_name)
    monkeypatch.setattr(strategy_module, "resolve_targeted_loader_names", fake_resolve_targeted_loader_names)

    strategy = build_strategy("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert strategy.content_type == ContentType.YOUTUBE_VIDEO
    assert strategy.primary_loaders == ("youtube", "youtube-ytdlp")
    assert calls == {"pipeline": 1, "targeted": 1}


def test_build_loader_plan_deduplicates_primary_and_fallback() -> None:
    strategy = build_strategy("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    plan = build_loader_plan(
        strategy=strategy,
        default_fallback=("youtube", "youtube-ytdlp", "playwright-fast"),
    )
    assert plan.loader_names == ("youtube", "youtube-ytdlp", "playwright-fast")
