import pytest

from kabigon.domain.errors import LoaderContentError
from kabigon.domain.errors import LoaderError
from kabigon.domain.errors import LoaderNotApplicableError
from kabigon.domain.errors import LoaderTimeoutError
from kabigon.domain.loader import Loader
from kabigon.loaders.compose import Compose


class NotApplicableLoader(Loader):
    async def load(self, url: str) -> str:
        raise LoaderNotApplicableError("NotApplicableLoader", url, "unsupported domain")


class EmptyLoader(Loader):
    async def load(self, url: str) -> str:
        return ""


class SuccessLoader(Loader):
    async def load(self, url: str) -> str:
        return "ok"


class TimeoutLoader(Loader):
    async def load(self, url: str) -> str:
        raise LoaderTimeoutError("TimeoutLoader", url, 3.0)


class ContentFailLoader(Loader):
    async def load(self, url: str) -> str:
        raise LoaderContentError("ContentFailLoader", url, "parse failed")


def test_compose_falls_back_on_not_applicable_and_empty_result():
    loader = Compose([NotApplicableLoader(), EmptyLoader(), SuccessLoader()])
    result = loader.load_sync("https://example.com")
    assert result == "ok"


def test_compose_raises_loader_error_with_details():
    loader = Compose([NotApplicableLoader(), TimeoutLoader(), ContentFailLoader(), EmptyLoader()])

    with pytest.raises(LoaderError) as exc_info:
        loader.load_sync("https://example.com")

    error = exc_info.value
    assert error.url == "https://example.com"
    assert error.details
    assert "NotApplicableLoader: Not applicable (unsupported domain)" in error.details
    assert "TimeoutLoader: Timeout after 3.0s" in error.details
    assert "ContentFailLoader: Content extraction failed - parse failed" in error.details
    assert "EmptyLoader: Empty result" in error.details
    assert "Attempted loaders:" in str(error)
