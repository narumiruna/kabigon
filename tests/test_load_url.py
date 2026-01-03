import pytest

import kabigon


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
    assert isinstance(loader, kabigon.Compose)
    assert len(loader.loaders) == 10  # Should have all default loaders


def test_load_url_invalid_url() -> None:
    """Test that load_url raises exception for invalid URLs."""
    # Invalid URL should fail in all loaders and raise an exception
    with pytest.raises(Exception):  # noqa: B017
        kabigon.load_url_sync("not-a-valid-url")
