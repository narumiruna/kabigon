import pytest

import kabigon
from kabigon import loaders
from kabigon.loader_registry import DEFAULT_PIPELINE_STEP_NAMES


def test_load_url_function_exists() -> None:
    """Test that load_url_sync function exists and is callable."""
    assert hasattr(kabigon.api, "load_url_sync")
    assert callable(kabigon.api.load_url_sync)


def test_load_url_async_function_exists() -> None:
    """Test that load_url (async) function exists and is callable."""
    assert hasattr(kabigon.api, "load_url")
    assert callable(kabigon.api.load_url)


def test_get_default_loader() -> None:
    """Test that _get_default_loader returns a Compose instance."""
    loader = kabigon.api._get_default_loader()
    assert isinstance(loader, loaders.Compose)
    assert len(loader.loaders) == 13  # Should have all default loaders


def test_build_pipeline_ids_youtube_url_is_targeted_then_fallback() -> None:
    pipeline_ids = kabigon.api._build_pipeline_ids("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert pipeline_ids[:2] == ["youtube", "youtube-ytdlp"]
    assert "playwright-networkidle" in pipeline_ids
    assert "playwright-fast" in pipeline_ids
    assert len(pipeline_ids) == len(set(pipeline_ids))


def test_build_pipeline_ids_unknown_url_uses_default_order() -> None:
    pipeline_ids = kabigon.api._build_pipeline_ids("https://example.com/hello")
    assert pipeline_ids == DEFAULT_PIPELINE_STEP_NAMES


def test_load_url_invalid_url() -> None:
    """Test that load_url raises exception for invalid URLs."""
    # Invalid URL should fail in all loaders and raise an exception
    with pytest.raises(Exception):  # noqa: B017
        kabigon.load_url_sync("not-a-valid-url")
