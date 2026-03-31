import pytest

from kabigon.application import strategy as strategy_module
from kabigon.application.classification import classify_pipeline_name
from kabigon.application.classification import classify_url
from kabigon.application.planner import build_loader_plan
from kabigon.application.strategy import build_retrieval_context
from kabigon.application.strategy import build_strategy
from kabigon.domain.models import ContentType


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
    calls = {"route": 0}

    def fake_resolve_route(url: str) -> tuple[str | None, tuple[str, ...]]:
        calls["route"] += 1
        return "youtube", ("youtube", "youtube-ytdlp")

    monkeypatch.setattr(strategy_module, "resolve_route", fake_resolve_route)

    strategy = build_strategy("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert strategy.content_type == ContentType.YOUTUBE_VIDEO
    assert strategy.primary_loaders == ("youtube", "youtube-ytdlp")
    assert calls == {"route": 1}


def test_build_loader_plan_deduplicates_primary_and_fallback() -> None:
    strategy = build_strategy("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    plan = build_loader_plan(
        strategy=strategy,
        default_fallback=("youtube", "youtube-ytdlp", "playwright-fast"),
    )
    assert plan.loader_names == ("youtube", "youtube-ytdlp", "playwright-fast")
