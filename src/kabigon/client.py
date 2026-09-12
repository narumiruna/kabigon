from __future__ import annotations

import asyncio
import contextlib
import importlib
import threading
import time
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any
from typing import cast
from urllib.parse import urlparse

from kabigon.core.execution import reset_deadline
from kabigon.core.execution import set_deadline
from kabigon.core.loader import Loader
from kabigon.core.resources import Browser
from kabigon.core.resources import CurlSession
from kabigon.core.resources import HttpClient
from kabigon.core.results import LoadResult
from kabigon.load_chain import resolve_load_chain
from kabigon.loader_registry import BBC
from kabigon.loader_registry import CNN
from kabigon.loader_registry import CURL_CFFI
from kabigon.loader_registry import FIRECRAWL
from kabigon.loader_registry import GITHUB
from kabigon.loader_registry import HTTPX
from kabigon.loader_registry import LTN
from kabigon.loader_registry import PDF
from kabigon.loader_registry import PI_SESSION
from kabigon.loader_registry import PLAYWRIGHT
from kabigon.loader_registry import PLAYWRIGHT_FAST
from kabigon.loader_registry import PLAYWRIGHT_NETWORKIDLE
from kabigon.loader_registry import PTT
from kabigon.loader_registry import REDDIT
from kabigon.loader_registry import REEL
from kabigon.loader_registry import TRUTHSOCIAL
from kabigon.loader_registry import TWITTER
from kabigon.loader_registry import YOUTUBE
from kabigon.loader_registry import YOUTUBE_YTDLP
from kabigon.loader_registry import YTDLP
from kabigon.loader_registry import LoaderDef
from kabigon.loader_registry import get_loader_def
from kabigon.loader_registry import get_loader_factory

_POSITIVE_DEADLINE = "deadline must be positive"
_POSITIVE_LIMIT = "concurrency limits must be positive"
_CLIENT_CONTEXT_REQUIRED = "Use KabigonClient with `async with`"
_CLIENT_LOOP_MISMATCH = "KabigonClient cannot be reused across event loops"
_INVALID_TARGET = "Target must be an HTTP(S) URL or a local PDF path"


class _ClientLoader(Loader):
    def __init__(self, client: KabigonClient, definition: LoaderDef) -> None:
        self.client = client
        self.definition = definition

    async def load(self, url: str) -> str:
        loader = get_loader_factory(self.definition.name, self.client)()
        return await loader.load(url)


class KabigonClient:
    """Own reusable extraction resources for one asyncio event loop."""

    def __init__(
        self,
        *,
        deadline: float | None = None,
        request_limit: int = 8,
        browser_limit: int = 2,
        worker_limit: int = 2,
    ) -> None:
        if deadline is not None and deadline <= 0:
            raise ValueError(_POSITIVE_DEADLINE)
        for _name, value in (
            ("request_limit", request_limit),
            ("browser_limit", browser_limit),
            ("worker_limit", worker_limit),
        ):
            if value <= 0:
                raise ValueError(_POSITIVE_LIMIT)

        self.deadline = deadline
        self._request_slots = asyncio.Semaphore(request_limit)
        self._browser_slots = asyncio.Semaphore(browser_limit)
        self._worker_slots = asyncio.Semaphore(worker_limit)
        self._http_lock = asyncio.Lock()
        self._curl_lock = asyncio.Lock()
        self._browser_lock = asyncio.Lock()
        self._http: HttpClient | None = None
        self._curl: CurlSession | None = None
        self._browser: Browser | None = None
        self._playwright: Any | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._entered = False
        self._models: dict[str, Any] = {}
        self._model_init_lock = threading.Lock()
        self._model_use_locks: dict[str, threading.Lock] = {}

    async def __aenter__(self) -> KabigonClient:
        loop = asyncio.get_running_loop()
        if self._loop is not None and self._loop is not loop:
            raise RuntimeError(_CLIENT_LOOP_MISMATCH)
        if self._entered:
            return self
        self._loop = loop
        self._entered = True
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    def _check_loop(self) -> None:
        if not self._entered:
            raise RuntimeError(_CLIENT_CONTEXT_REQUIRED)
        if self._loop is not asyncio.get_running_loop():
            raise RuntimeError(_CLIENT_LOOP_MISMATCH)

    async def http_client(self) -> HttpClient:
        self._check_loop()
        if self._http is None:
            async with self._http_lock:
                if self._http is None:
                    httpx = importlib.import_module("httpx")
                    self._http = httpx.AsyncClient()
        return self._http

    async def curl_session(self) -> CurlSession:
        self._check_loop()
        if self._curl is None:
            async with self._curl_lock:
                if self._curl is None:
                    requests = importlib.import_module("curl_cffi.requests")
                    self._curl = requests.AsyncSession(impersonate="chrome")
        return cast("CurlSession", self._curl)

    async def browser(self) -> Browser:
        self._check_loop()
        if self._browser is None:
            async with self._browser_lock:
                if self._browser is None:
                    async_api = importlib.import_module("playwright.async_api")
                    self._playwright = await async_api.async_playwright().start()
                    self._browser = await self._playwright.chromium.launch(headless=True)
        return self._browser

    def loader_kwargs(self, loader_def: LoaderDef) -> dict[str, Any]:
        name = loader_def.name
        kwargs: dict[str, Any] = {}
        if name in {
            HTTPX,
            CURL_CFFI,
            PLAYWRIGHT,
            PLAYWRIGHT_FAST,
            PLAYWRIGHT_NETWORKIDLE,
            BBC,
            CNN,
            LTN,
            PTT,
            REDDIT,
            TRUTHSOCIAL,
            TWITTER,
            PI_SESSION,
            GITHUB,
            PDF,
            REEL,
        }:
            kwargs["resource_provider"] = self
        if name in {YOUTUBE, YOUTUBE_YTDLP, YTDLP, PDF, FIRECRAWL, REEL}:
            kwargs["run_blocking"] = self.run_blocking
        if name in {YOUTUBE_YTDLP, YTDLP, REEL}:
            kwargs["model_provider"] = self.whisper_model
        return kwargs

    async def _admit(self, loader_name: str, operation: Callable[[], Awaitable[str]]) -> str:
        kind = get_loader_def(loader_name).resource_kind
        if kind == "worker":
            return await operation()
        semaphore = self._browser_slots if kind == "browser" else self._request_slots
        async with semaphore:
            return await operation()

    async def run_browser[T](self, operation: Callable[[], Awaitable[T]]) -> T:
        async with self._browser_slots:
            return await operation()

    async def run_blocking[T](self, operation: Callable[[], T]) -> T:
        await self._worker_slots.acquire()
        task = asyncio.create_task(asyncio.to_thread(operation))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            with contextlib.suppress(Exception):
                await task
            raise
        finally:
            self._worker_slots.release()

    def whisper_model(self, model_name: str) -> tuple[Any, threading.Lock]:
        with self._model_init_lock:
            if model_name not in self._models:
                whisper = importlib.import_module("whisper")
                self._models[model_name] = whisper.load_model(model_name)
                self._model_use_locks[model_name] = threading.Lock()
            return self._models[model_name], self._model_use_locks[model_name]

    async def load_url_detailed(self, url: str) -> LoadResult:
        self._check_loop()
        _validate_target(url)
        deadline_at = time.monotonic() + self.deadline if self.deadline is not None else None
        token = set_deadline(deadline_at)
        try:
            chain = resolve_load_chain(
                url,
                get_factory=lambda name: lambda: _ClientLoader(self, get_loader_def(name)),
                admit=self._admit,
            )
            return await chain.load_detailed()
        finally:
            reset_deadline(token)

    async def load_url(self, url: str) -> str:
        return (await self.load_url_detailed(url)).content

    async def aclose(self) -> None:
        if not self._entered:
            return
        resources = (
            (self._browser, "close"),
            (self._playwright, "stop"),
            (self._curl, "close"),
            (self._http, "aclose"),
        )
        self._browser = None
        self._playwright = None
        self._curl = None
        self._http = None
        self._entered = False
        first_error: Exception | None = None
        for resource, close_method in resources:
            if resource is None:
                continue
            try:
                await getattr(resource, close_method)()
            except Exception as error:  # noqa: BLE001
                if first_error is None:
                    first_error = error
        if first_error is not None:
            raise first_error


def _validate_target(target: str) -> None:
    parsed = urlparse(target)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return
    if not parsed.scheme and target.lower().endswith(".pdf"):
        return
    raise ValueError(_INVALID_TARGET)


__all__ = ["KabigonClient"]
