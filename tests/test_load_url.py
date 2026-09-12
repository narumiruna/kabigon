import asyncio

import pytest

import kabigon
from kabigon.load_chain import DEFAULT_FALLBACK_LOADERS
from kabigon.load_chain import explain_load_chain


def test_load_url_function_exists() -> None:
    """Test that load_url_sync function exists and is callable."""
    assert hasattr(kabigon.api, "load_url_sync")
    assert callable(kabigon.api.load_url_sync)


def test_load_url_async_function_exists() -> None:
    """Test that load_url (async) function exists and is callable."""
    assert hasattr(kabigon.api, "load_url")
    assert callable(kabigon.api.load_url)


def test_resolve_load_chain_for_youtube_explains_targeted_loaders() -> None:
    explanation = explain_load_chain("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert explanation.targeted_loaders == ("youtube", "youtube-ytdlp")


def test_build_execution_plan_for_url_youtube_is_source_strict() -> None:
    execution_plan = explain_load_chain("https://www.youtube.com/watch?v=dQw4w9WgXcQ").execution_plan

    assert execution_plan == ("youtube", "youtube-ytdlp")


def test_build_execution_plan_for_youtube_playlist_uses_default_order() -> None:
    execution_plan = explain_load_chain("https://www.youtube.com/playlist?list=PL123").execution_plan

    assert execution_plan == DEFAULT_FALLBACK_LOADERS


def test_build_execution_plan_for_url_unknown_uses_default_order() -> None:
    execution_plan = explain_load_chain("https://example.com/hello").execution_plan
    assert execution_plan == DEFAULT_FALLBACK_LOADERS


def test_build_execution_plan_for_non_pdf_file_uses_default_order() -> None:
    execution_plan = explain_load_chain("not-a-valid-url").execution_plan
    assert execution_plan == DEFAULT_FALLBACK_LOADERS


def test_targeted_loaders_are_prefix_of_execution_plan() -> None:
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    explanation = explain_load_chain(url)
    targeted = explanation.targeted_loaders
    execution_plan = explanation.execution_plan
    assert execution_plan[: len(targeted)] == targeted


def test_build_execution_plan_for_openai_web_uses_targeted_only() -> None:
    execution_plan = explain_load_chain("https://openai.com/pricing").execution_plan
    assert execution_plan == ("firecrawl",)


def test_explain_plan_includes_openai_web_requirements() -> None:
    plan = kabigon.explain_plan("https://openai.com/pricing")

    assert plan["pipeline"] == "openai_web"
    assert plan["targeted_loaders"] == ["firecrawl"]
    assert plan["requirements"] == ["FIRECRAWL_API_KEY"]
    assert "missing_requirements" in plan
    assert set(plan) >= {"eligible_loaders", "unavailable_loaders"}


def test_detailed_api_is_exported_and_text_api_projects_content(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def load_url_detailed(self, url: str):
            assert url == "https://example.com"
            return kabigon.LoadResult("body", "httpx", "generic_web", False, ())

    monkeypatch.setattr(kabigon.api, "KabigonClient", lambda **_kwargs: FakeClient())

    detailed = asyncio.run(kabigon.load_url_detailed("https://example.com"))
    text = asyncio.run(kabigon.load_url("https://example.com"))

    assert detailed.content == text == "body"
    assert detailed.loader_id == "httpx"


def test_repeated_sync_calls_use_independent_short_lived_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    created = 0
    closed = 0

    class FakeClient:
        def __init__(self, **_kwargs) -> None:
            nonlocal created
            created += 1

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            nonlocal closed
            closed += 1

        async def load_url_detailed(self, url: str):
            return kabigon.LoadResult(url, "httpx", "generic_web", False, ())

    monkeypatch.setattr(kabigon.api, "KabigonClient", FakeClient)

    assert kabigon.load_url_sync("https://example.com/1") == "https://example.com/1"
    assert kabigon.load_url_sync("https://example.com/2") == "https://example.com/2"
    assert created == closed == 2


def test_one_shot_async_cancellation_closes_client(monkeypatch: pytest.MonkeyPatch) -> None:
    closed = asyncio.Event()

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            closed.set()

        async def load_url_detailed(self, _url: str):
            await asyncio.Event().wait()

    monkeypatch.setattr(kabigon.api, "KabigonClient", lambda **_kwargs: FakeClient())

    async def scenario() -> None:
        task = asyncio.create_task(kabigon.load_url("https://example.com"))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert closed.is_set()

    asyncio.run(scenario())


def test_load_url_invalid_url() -> None:
    """Test that load_url raises exception for invalid URLs."""
    # Invalid URL should fail in all loaders and raise an exception
    with pytest.raises(Exception):  # noqa: B017
        kabigon.load_url_sync("not-a-valid-url")
