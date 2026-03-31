"""Tests for custom exception classes."""

from kabigon.core.exception import LoaderContentError
from kabigon.core.exception import LoaderNotApplicableError
from kabigon.core.exception import LoaderTimeoutError


def test_loader_not_applicable_error():
    """Test LoaderNotApplicableError exception."""
    error = LoaderNotApplicableError("TestLoader", "https://example.com", "Not a valid URL")

    assert error.loader_name == "TestLoader"
    assert error.url == "https://example.com"
    assert error.reason == "Not a valid URL"
    assert "TestLoader" in str(error)
    assert "https://example.com" in str(error)
    assert "Not a valid URL" in str(error)


def test_loader_not_applicable_error_without_reason():
    """Test LoaderNotApplicableError without reason."""
    error = LoaderNotApplicableError("TestLoader", "https://example.com")

    assert error.loader_name == "TestLoader"
    assert error.url == "https://example.com"
    assert error.reason is None
    assert "TestLoader" in str(error)
    assert "https://example.com" in str(error)


def test_loader_timeout_error():
    """Test LoaderTimeoutError exception."""
    error = LoaderTimeoutError("TestLoader", "https://example.com", 30.0, "Try again")

    assert error.loader_name == "TestLoader"
    assert error.url == "https://example.com"
    assert error.timeout == 30.0
    assert error.suggestion == "Try again"
    assert "TestLoader" in str(error)
    assert "https://example.com" in str(error)
    assert "30.0s" in str(error)
    assert "Try again" in str(error)


def test_loader_timeout_error_default_suggestion():
    """Test LoaderTimeoutError with default suggestion."""
    error = LoaderTimeoutError("TestLoader", "https://example.com", 30.0)

    assert error.suggestion is None
    assert "TestLoader" in str(error)
    assert "https://example.com" in str(error)
    assert "30.0s" in str(error)
    # Should have a default suggestion
    assert "Suggestion:" in str(error)
    assert "timeout" in str(error).lower()


def test_loader_content_error():
    """Test LoaderContentError exception."""
    error = LoaderContentError("TestLoader", "https://example.com", "Empty content", "Check the URL")

    assert error.loader_name == "TestLoader"
    assert error.url == "https://example.com"
    assert error.reason == "Empty content"
    assert error.suggestion == "Check the URL"
    assert "TestLoader" in str(error)
    assert "https://example.com" in str(error)
    assert "Empty content" in str(error)
    assert "Check the URL" in str(error)


def test_loader_content_error_without_suggestion():
    """Test LoaderContentError without suggestion."""
    error = LoaderContentError("TestLoader", "https://example.com", "Empty content")

    assert error.loader_name == "TestLoader"
    assert error.url == "https://example.com"
    assert error.reason == "Empty content"
    assert error.suggestion is None
    assert "TestLoader" in str(error)
    assert "https://example.com" in str(error)
    assert "Empty content" in str(error)


def test_exception_inheritance():
    """Test that custom exceptions inherit from KabigonError."""
    from kabigon.core.exception import KabigonError

    error1 = LoaderNotApplicableError("Test", "url")
    error2 = LoaderTimeoutError("Test", "url", 10.0)
    error3 = LoaderContentError("Test", "url", "reason")

    assert isinstance(error1, KabigonError)
    assert isinstance(error2, KabigonError)
    assert isinstance(error3, KabigonError)
