from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace
from typing import ClassVar
from typing import cast

import pytest

from kabigon import client as client_module
from kabigon.client import KabigonClient
from kabigon.core.errors import LoaderError
from kabigon.core.execution import reset_deadline
from kabigon.core.execution import set_deadline
from kabigon.core.loader import Loader
from kabigon.core.resources import ResourceProvider
from kabigon.core.results import LoadResult
from kabigon.load_chain import resolve_explicit_load_chain
from kabigon.loaders.httpx import HttpxLoader


class FakeHttpClient:
    created = 0

    def __init__(self) -> None:
        type(self).created += 1
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakeChain:
    def __init__(self, result: LoadResult) -> None:
        self.result = result

    async def load_detailed(self) -> LoadResult:
        return self.result


def test_client_construction_opens_no_resources_and_first_use_is_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeHttpClient.created = 0
    monkeypatch.setattr(
        client_module.importlib,
        "import_module",
        lambda name: SimpleNamespace(AsyncClient=FakeHttpClient) if name == "httpx" else __import__(name),
    )

    async def scenario() -> FakeHttpClient:
        client = KabigonClient()
        assert client._http is None
        async with client:
            first, second = await asyncio.gather(client.http_client(), client.http_client())
            assert first is second
            assert FakeHttpClient.created == 1
            return first

    resource = asyncio.run(scenario())
    assert resource.closed is True


def test_client_closes_resources_when_body_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        client_module.importlib,
        "import_module",
        lambda name: SimpleNamespace(AsyncClient=FakeHttpClient) if name == "httpx" else __import__(name),
    )

    async def scenario() -> FakeHttpClient:
        resource = None
        with pytest.raises(RuntimeError, match="body failed"):
            async with KabigonClient() as client:
                resource = await client.http_client()
                raise RuntimeError("body failed")
        assert resource is not None
        return resource

    resource = asyncio.run(scenario())
    assert resource.closed is True


def test_concurrent_curl_and_browser_initialization_happens_once(  # noqa: C901
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counts = {"curl": 0, "playwright": 0, "browser": 0}

    class Curl:
        def __init__(self, **_kwargs) -> None:
            counts["curl"] += 1

        async def close(self) -> None:
            return None

    class Browser:
        async def close(self) -> None:
            return None

    class Chromium:
        async def launch(self, **_kwargs) -> Browser:
            counts["browser"] += 1
            return Browser()

    class Playwright:
        chromium = Chromium()

        async def stop(self) -> None:
            return None

    class Manager:
        async def start(self) -> Playwright:
            counts["playwright"] += 1
            return Playwright()

    real_import = client_module.importlib.import_module

    def fake_import(name: str):
        if name == "curl_cffi.requests":
            return SimpleNamespace(AsyncSession=Curl)
        if name == "playwright.async_api":
            return SimpleNamespace(async_playwright=Manager)
        return real_import(name)

    monkeypatch.setattr(client_module.importlib, "import_module", fake_import)

    async def scenario() -> None:
        async with KabigonClient() as client:
            curl_one, curl_two = await asyncio.gather(client.curl_session(), client.curl_session())
            browser_one, browser_two = await asyncio.gather(client.browser(), client.browser())
            assert curl_one is curl_two
            assert browser_one is browser_two

    asyncio.run(scenario())
    assert counts == {"curl": 1, "playwright": 1, "browser": 1}


def test_client_projects_detailed_result_and_checks_context(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = LoadResult("body", "httpx", "generic_web", False, ())

    def fake_resolve(*_args, **_kwargs) -> FakeChain:
        return FakeChain(expected)

    monkeypatch.setattr(client_module, "resolve_load_chain", fake_resolve)

    async def scenario() -> None:
        client = KabigonClient()
        with pytest.raises(RuntimeError, match="async with"):
            await client.load_url("https://example.com")
        async with client:
            assert await client.load_url_detailed("https://example.com") == expected
            assert await client.load_url("https://example.com") == "body"

    asyncio.run(scenario())


def test_client_cannot_be_reused_across_event_loops() -> None:
    client = KabigonClient()

    async def use_once() -> None:
        async with client:
            pass

    asyncio.run(use_once())
    with pytest.raises(RuntimeError, match="event loops"):
        asyncio.run(use_once())


def test_client_rejects_non_positive_limits_and_deadline() -> None:
    with pytest.raises(ValueError, match="deadline"):
        KabigonClient(deadline=0)
    with pytest.raises(ValueError, match="limits"):
        KabigonClient(worker_limit=0)


def test_blocking_cancellation_drains_before_releasing_worker_slot() -> None:
    first_started = threading.Event()
    release_first = threading.Event()
    second_started = threading.Event()

    def first() -> str:
        first_started.set()
        release_first.wait(timeout=2)
        return "first"

    def second() -> str:
        second_started.set()
        return "second"

    async def scenario() -> None:
        async with KabigonClient(worker_limit=1) as client:
            first_task = asyncio.create_task(client.run_blocking(first))
            await asyncio.to_thread(first_started.wait, 1)
            first_task.cancel()
            second_task = asyncio.create_task(client.run_blocking(second))
            await asyncio.sleep(0)
            assert not second_started.is_set()
            assert not first_task.done()
            release_first.set()
            with pytest.raises(asyncio.CancelledError):
                await first_task
            assert await second_task == "second"

    asyncio.run(scenario())


def test_reused_http_client_keeps_request_headers_isolated() -> None:
    class Response:
        text = "<p>body</p>"
        content = b"<p>body</p>"
        headers: ClassVar[dict[str, str]] = {"content-type": "text/html"}

        def raise_for_status(self) -> None:
            return None

    class Http:
        def __init__(self) -> None:
            self.headers: list[dict[str, str]] = []

        async def get(self, _url: str, **kwargs):
            self.headers.append(kwargs["headers"])
            return Response()

    class Provider:
        def __init__(self) -> None:
            self.http = Http()

        async def http_client(self):
            return self.http

    async def scenario() -> None:
        provider = Provider()
        resource_provider = cast("ResourceProvider", provider)
        first = HttpxLoader(headers={"X-Request": "first"}, resource_provider=resource_provider)
        second = HttpxLoader(headers={"X-Request": "second"}, resource_provider=resource_provider)
        await asyncio.gather(first.load("https://example.com/1"), second.load("https://example.com/2"))
        assert {headers["X-Request"] for headers in provider.http.headers} == {"first", "second"}
        assert provider.http.headers[0] is not provider.http.headers[1]

    asyncio.run(scenario())


def test_request_queue_time_counts_toward_deadline() -> None:
    called = False

    class Success(Loader):
        async def load(self, url: str) -> str:
            nonlocal called
            called = True
            return url

    async def scenario() -> None:
        async with KabigonClient(deadline=0.01, request_limit=1) as client:
            await client._request_slots.acquire()
            token = set_deadline(asyncio.get_running_loop().time() + 0.01)
            try:
                chain = resolve_explicit_load_chain(
                    "https://example.com",
                    ("httpx",),
                    {"httpx": Success}.__getitem__,
                    admit=client._admit,
                )
                with pytest.raises(LoaderError):
                    await chain.load()
            finally:
                reset_deadline(token)
                client._request_slots.release()

    asyncio.run(scenario())
    assert called is False


def test_chain_cancellation_reaches_active_loader() -> None:
    cancelled = asyncio.Event()

    class Waiting(Loader):
        async def load(self, url: str) -> str:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise
            return url

    async def scenario() -> None:
        chain = resolve_explicit_load_chain("https://example.com", ("waiting",), {"waiting": Waiting}.__getitem__)
        task = asyncio.create_task(chain.load())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert cancelled.is_set()

    asyncio.run(scenario())


def test_client_rejects_invalid_target_before_planning(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "resolve_load_chain", lambda *_args, **_kwargs: pytest.fail("must not plan"))

    async def scenario() -> None:
        async with KabigonClient() as client:
            with pytest.raises(ValueError, match="HTTP"):
                await client.load_url("not-a-valid-url")

    asyncio.run(scenario())
