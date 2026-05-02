import pytest

import kabigon
from kabigon.application.planning import DEFAULT_FALLBACK_LOADERS
from kabigon.application.service import resolve_execution_plan_loader_names
from kabigon.application.service import resolve_targeted_loader_names


def test_load_url_function_exists() -> None:
    """Test that load_url_sync function exists and is callable."""
    assert hasattr(kabigon.api, "load_url_sync")
    assert callable(kabigon.api.load_url_sync)


def test_load_url_async_function_exists() -> None:
    """Test that load_url (async) function exists and is callable."""
    assert hasattr(kabigon.api, "load_url")
    assert callable(kabigon.api.load_url)


def test_resolve_targeted_loader_names_for_url_youtube_url() -> None:
    targeted = resolve_targeted_loader_names("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert targeted == ["youtube", "youtube-ytdlp"]


def test_build_execution_plan_for_url_youtube_is_targeted_then_fallback() -> None:
    execution_plan = resolve_execution_plan_loader_names("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert execution_plan[:2] == ["youtube", "youtube-ytdlp"]
    assert "playwright-networkidle" in execution_plan
    assert "playwright-fast" in execution_plan
    assert len(execution_plan) == len(set(execution_plan))


def test_build_execution_plan_for_url_unknown_uses_default_order() -> None:
    execution_plan = resolve_execution_plan_loader_names("https://example.com/hello")
    assert execution_plan == list(DEFAULT_FALLBACK_LOADERS)


def test_targeted_loaders_are_prefix_of_execution_plan() -> None:
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    targeted = resolve_targeted_loader_names(url)
    execution_plan = resolve_execution_plan_loader_names(url)
    assert execution_plan[: len(targeted)] == targeted


def test_build_execution_plan_for_openai_web_is_targeted_then_fallback() -> None:
    execution_plan = resolve_execution_plan_loader_names("https://openai.com/pricing")
    assert execution_plan == ["firecrawl"]


def test_explain_plan_includes_openai_web_requirements() -> None:
    plan = kabigon.explain_plan("https://openai.com/pricing")

    assert plan["pipeline"] == "openai_web"
    assert plan["targeted_loaders"] == ["firecrawl"]
    assert plan["requirements"] == ["FIRECRAWL_API_KEY"]


def test_load_url_invalid_url() -> None:
    """Test that load_url raises exception for invalid URLs."""
    # Invalid URL should fail in all loaders and raise an exception
    with pytest.raises(Exception):  # noqa: B017
        kabigon.load_url_sync("not-a-valid-url")
