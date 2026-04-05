import asyncio

import httpx
import pytest

from kabigon.loaders import reddit
from kabigon.loaders.reddit import RedditLoader
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


class Json403ThenRssResponse:
    def __init__(self, url: str) -> None:
        self._url = url
        self.text = RSS_XML

    def raise_for_status(self) -> None:
        if self._url.endswith(".json"):
            raise httpx.HTTPStatusError(
                "forbidden",
                request=httpx.Request("GET", "https://www.reddit.com"),
                response=httpx.Response(403),
            )

    def json(self) -> object:
        raise AssertionError("json() should not be called")


class Json403ThenRssClient:
    def __init__(self, **_: object) -> None:
        return None

    async def __aenter__(self) -> "Json403ThenRssClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    async def get(self, url: str, headers: dict[str, str] | None = None) -> Json403ThenRssResponse:
        if url.endswith(".json"):
            assert headers is not None
            assert headers["Accept"] == "application/json"
        return Json403ThenRssResponse(url)


def test_to_reddit_json_url_normalizes_host_and_path() -> None:
    url = "https://old.reddit.com/r/selfhosted/comments/abc123/example/?utm_source=share"
    assert to_reddit_json_url(url) == "https://www.reddit.com/r/selfhosted/comments/abc123/example.json"


def test_to_reddit_rss_url_normalizes_host_and_path() -> None:
    url = "https://old.reddit.com/r/selfhosted/comments/abc123/example/?utm_source=share"
    assert to_reddit_rss_url(url) == "https://www.reddit.com/r/selfhosted/comments/abc123/example/.rss"


def test_reddit_loader_prefers_json_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> object:
            return [
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

    class FakeClient:
        def __init__(self, **_: object) -> None:
            return None

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

        async def get(self, url: str, headers: dict[str, str]) -> FakeResponse:
            assert url == "https://www.reddit.com/r/selfhosted/comments/abc123/example.json"
            assert headers["Accept"] == "application/json"
            return FakeResponse()

    async def fail_fallback(self: RedditLoader, url: str) -> str:
        raise AssertionError(f"fallback should not be called: {url}")

    monkeypatch.setattr(reddit.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(RedditLoader, "_load_via_old_reddit", fail_fallback)

    result = asyncio.run(
        RedditLoader().load("https://www.reddit.com/r/selfhosted/comments/abc123/example/?utm_source=share")
    )
    assert "Nomad selfhosted trip planner" in result
    assert "Great project" in result
    assert "u/bob" in result
    assert "Looks useful!" in result


def test_reddit_loader_falls_back_when_json_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fallback(self: RedditLoader, url: str) -> str:
        return f"fallback:{url}"

    monkeypatch.setattr(reddit.httpx, "AsyncClient", Json403ThenRssClient)
    monkeypatch.setattr(RedditLoader, "_load_via_old_reddit", fake_fallback)

    result = asyncio.run(RedditLoader().load("https://www.reddit.com/r/python/comments/abc/demo/"))
    assert "Demo Feed" in result
    assert "Post title" in result
    assert "RSS content" in result
