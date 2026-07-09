import asyncio

import httpx
import pytest

from kabigon.loaders import reddit
from kabigon.loaders.reddit import RedditLoader
from kabigon.loaders.reddit import convert_to_old_reddit
from kabigon.loaders.reddit import to_reddit_json_url
from kabigon.loaders.reddit import to_reddit_rss_url

RSS_XML = """
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Demo Feed</title>
  <entry>
    <title>Post title</title>
    <author><name>alice</name></author>
    <updated>2026-03-27T06:12:49+00:00</updated>
    <content type="html">&lt;div&gt;&lt;p&gt;RSS content&lt;/p&gt;&lt;/div&gt;</content>
  </entry>
</feed>
""".strip()

JSON_PAYLOAD = [
    {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Nomad selfhosted trip planner",
                        "author": "alice",
                        "subreddit": "selfhosted",
                        "score": 123,
                        "permalink": "/r/selfhosted/comments/abc123/example/",
                        "selftext": "Great project",
                    }
                }
            ]
        }
    },
    {
        "data": {
            "children": [
                {"kind": "t1", "data": {"author": "bob", "score": 7, "body": "Looks useful!"}},
            ]
        }
    },
]


class RedditResponse:
    def __init__(self, url: str, *, status_code: int = 200, payload: object = JSON_PAYLOAD) -> None:
        self._url = url
        self._status_code = status_code
        self._payload = payload
        self.text = RSS_XML

    def raise_for_status(self) -> None:
        if self._status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self._status_code}",
                request=httpx.Request("GET", self._url),
                response=httpx.Response(self._status_code),
            )

    def json(self) -> object:
        return self._payload


class RssOnlyClient:
    def __init__(self, **_: object) -> None:
        return None

    async def __aenter__(self) -> "RssOnlyClient":
        return self

    async def __aexit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        return None

    async def get(self, url: str, headers: dict[str, str] | None = None) -> RedditResponse:
        assert url == "https://www.reddit.com/r/python/comments/abc/demo/.rss"
        assert headers is None
        return RedditResponse(url)


class Rss403ThenJsonClient:
    def __init__(self, **_: object) -> None:
        return None

    async def __aenter__(self) -> "Rss403ThenJsonClient":
        return self

    async def __aexit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        return None

    async def get(self, url: str, headers: dict[str, str] | None = None) -> RedditResponse:
        if url.endswith("/.rss"):
            assert headers is None
            return RedditResponse(url, status_code=403)
        if url.endswith(".json"):
            assert headers is not None
            assert headers["Accept"] == "application/json"
            return RedditResponse(url)
        raise AssertionError(f"unexpected URL: {url}")


class RssAndJson403Client:
    def __init__(self, **_: object) -> None:
        return None

    async def __aenter__(self) -> "RssAndJson403Client":
        return self

    async def __aexit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        return None

    async def get(self, url: str, headers: dict[str, str] | None = None) -> RedditResponse:
        if url.endswith(".json"):
            assert headers is not None
            assert headers["Accept"] == "application/json"
        else:
            assert headers is None
        return RedditResponse(url, status_code=403)


def test_to_reddit_json_url_normalizes_host_and_path() -> None:
    url = "https://old.reddit.com/r/selfhosted/comments/abc123/example/?utm_source=share"
    assert to_reddit_json_url(url) == "https://www.reddit.com/r/selfhosted/comments/abc123/example.json"


def test_to_reddit_rss_url_normalizes_host_and_path() -> None:
    url = "https://old.reddit.com/r/selfhosted/comments/abc123/example/?utm_source=share"
    assert to_reddit_rss_url(url) == "https://www.reddit.com/r/selfhosted/comments/abc123/example/.rss"


def test_reddit_short_url_normalizes_to_comments_path() -> None:
    url = "https://redd.it/abc123?utm_source=share"
    assert to_reddit_json_url(url) == "https://www.reddit.com/comments/abc123.json"
    assert to_reddit_rss_url(url) == "https://www.reddit.com/comments/abc123/.rss"
    assert convert_to_old_reddit(url) == "https://old.reddit.com/comments/abc123"


def test_reddit_loader_prefers_rss_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail_fallback(_self: RedditLoader, url: str) -> str:
        raise AssertionError(f"fallback should not be called: {url}")

    monkeypatch.setattr(reddit.httpx, "AsyncClient", RssOnlyClient)
    monkeypatch.setattr(RedditLoader, "_load_via_old_reddit", fail_fallback)

    result = asyncio.run(RedditLoader().load("https://www.reddit.com/r/python/comments/abc/demo/"))
    assert "Demo Feed" in result
    assert "Post title" in result
    assert "RSS content" in result


def test_reddit_loader_falls_back_to_json_when_rss_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail_fallback(_self: RedditLoader, url: str) -> str:
        raise AssertionError(f"fallback should not be called: {url}")

    monkeypatch.setattr(reddit.httpx, "AsyncClient", Rss403ThenJsonClient)
    monkeypatch.setattr(RedditLoader, "_load_via_old_reddit", fail_fallback)

    result = asyncio.run(
        RedditLoader().load("https://www.reddit.com/r/selfhosted/comments/abc123/example/?utm_source=share")
    )
    assert "Nomad selfhosted trip planner" in result
    assert "Great project" in result
    assert "u/bob" in result
    assert "Looks useful!" in result


def test_reddit_loader_uses_old_reddit_when_rss_and_json_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fallback(_self: RedditLoader, url: str) -> str:
        return f"fallback:{url}"

    monkeypatch.setattr(reddit.httpx, "AsyncClient", RssAndJson403Client)
    monkeypatch.setattr(RedditLoader, "_load_via_old_reddit", fake_fallback)

    result = asyncio.run(RedditLoader().load("https://www.reddit.com/r/python/comments/abc/demo/"))
    assert result == "fallback:https://www.reddit.com/r/python/comments/abc/demo/"
