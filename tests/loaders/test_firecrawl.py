from types import SimpleNamespace

import pytest

from kabigon.domain.errors import FirecrawlAPIKeyNotSetError
from kabigon.domain.errors import LoaderError
from kabigon.loaders.firecrawl import FirecrawlLoader


def test_firecrawl_loader_prefers_scrape_url(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeApp:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.called = ""

        def scrape_url(self, url: str, formats: list[str], timeout: int | None) -> object:
            self.called = f"scrape_url:{url}:{formats}:{timeout}"
            return SimpleNamespace(success=True, markdown="# ok")

    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    monkeypatch.setattr("kabigon.loaders.firecrawl.FirecrawlApp", FakeApp)

    loader = FirecrawlLoader(timeout=123)
    content = loader.load_sync("https://example.com")

    assert content == "# ok"
    assert loader.app.called == "scrape_url:https://example.com:['markdown']:123"


def test_firecrawl_loader_falls_back_to_scrape(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeApp:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.called = ""

        def scrape(self, url: str, formats: list[str], timeout: int | None) -> object:
            self.called = f"scrape:{url}:{formats}:{timeout}"
            return SimpleNamespace(markdown="# fallback")

    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    monkeypatch.setattr("kabigon.loaders.firecrawl.FirecrawlApp", FakeApp)

    loader = FirecrawlLoader(timeout=456)
    content = loader.load_sync("https://example.com")

    assert content == "# fallback"
    assert loader.app.called == "scrape:https://example.com:['markdown']:456"


def test_firecrawl_loader_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
    with pytest.raises(FirecrawlAPIKeyNotSetError):
        FirecrawlLoader()


def test_firecrawl_loader_raises_when_no_markdown(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeApp:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

        def scrape(self, url: str, formats: list[str], timeout: int | None) -> object:
            return SimpleNamespace(success=True)

    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    monkeypatch.setattr("kabigon.loaders.firecrawl.FirecrawlApp", FakeApp)

    loader = FirecrawlLoader()
    with pytest.raises(LoaderError, match="did not include markdown"):
        loader.load_sync("https://example.com")
