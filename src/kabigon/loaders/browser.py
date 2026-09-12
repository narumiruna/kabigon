from __future__ import annotations

import logging
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Literal

from playwright.async_api import Browser
from playwright.async_api import Page
from playwright.async_api import Request
from playwright.async_api import Route
from playwright.async_api import TimeoutError
from playwright.async_api import async_playwright

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderTimeoutError
from kabigon.core.retrieval import RetrievedHtml

BrowserPageHook = Callable[[Page], Awaitable[None]]
BrowserContentExtractor = Callable[[Page], Awaitable[str]]
BrowserWaitUntil = Literal["commit", "domcontentloaded", "load", "networkidle"]

DEFAULT_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
DEFAULT_BLOCKED_RESOURCE_TYPES = frozenset({"font", "image", "media"})
logger = logging.getLogger(__name__)


async def _fetch_with_browser(
    browser: Browser,
    url: str,
    *,
    loader_name: str,
    timeout_ms: float | None,
    timeout_suggestion: str,
    wait_until: BrowserWaitUntil | None,
    user_agent: str | None,
    block_resource_types: frozenset[str],
    after_goto: BrowserPageHook | None,
    extract_content: BrowserContentExtractor | None,
) -> RetrievedHtml:
    context = await browser.new_context(user_agent=user_agent)
    try:
        page = await context.new_page()
        if block_resource_types:

            async def route_handler(route: Route, request: Request) -> None:
                if request.resource_type in block_resource_types:
                    await route.abort()
                else:
                    await route.continue_()

            await page.route("**/*", route_handler)

        try:
            if wait_until is None:
                response = await page.goto(url, timeout=timeout_ms)
            else:
                response = await page.goto(url, timeout=timeout_ms, wait_until=wait_until)
        except TimeoutError as error:
            timeout_seconds = (timeout_ms or 0) / 1000 if timeout_ms else 30
            raise LoaderTimeoutError(loader_name, url, timeout_seconds, timeout_suggestion) from error

        if response is not None and response.status >= 400:
            raise LoaderContentError(loader_name, url, f"HTTP request failed with status {response.status}")
        if after_goto is not None:
            await after_goto(page)
        content = await extract_content(page) if extract_content is not None else await page.content()
        headers = getattr(response, "headers", {}) if response is not None else {}
        content_type = headers.get("content-type", "text/html") if isinstance(headers, dict) else "text/html"
        return RetrievedHtml(content, content_type)
    finally:
        await context.close()


async def fetch_browser_html_response(
    url: str,
    *,
    loader_name: str,
    timeout_ms: float | None,
    timeout_suggestion: str,
    wait_until: BrowserWaitUntil | None = None,
    user_agent: str | None = None,
    browser_headless: bool = True,
    block_resource_types: frozenset[str] = frozenset(),
    after_goto: BrowserPageHook | None = None,
    extract_content: BrowserContentExtractor | None = None,
    browser: Browser | None = None,
) -> RetrievedHtml:
    if browser is not None:
        return await _fetch_with_browser(
            browser,
            url,
            loader_name=loader_name,
            timeout_ms=timeout_ms,
            timeout_suggestion=timeout_suggestion,
            wait_until=wait_until,
            user_agent=user_agent,
            block_resource_types=block_resource_types,
            after_goto=after_goto,
            extract_content=extract_content,
        )

    async with async_playwright() as playwright:
        owned_browser = await playwright.chromium.launch(headless=browser_headless)
        try:
            return await _fetch_with_browser(
                owned_browser,
                url,
                loader_name=loader_name,
                timeout_ms=timeout_ms,
                timeout_suggestion=timeout_suggestion,
                wait_until=wait_until,
                user_agent=user_agent,
                block_resource_types=block_resource_types,
                after_goto=after_goto,
                extract_content=extract_content,
            )
        finally:
            await owned_browser.close()


async def fetch_browser_html(
    url: str,
    *,
    loader_name: str,
    timeout_ms: float | None,
    timeout_suggestion: str,
    wait_until: BrowserWaitUntil | None = None,
    user_agent: str | None = None,
    browser_headless: bool = True,
    block_resource_types: frozenset[str] = frozenset(),
    after_goto: BrowserPageHook | None = None,
    extract_content: BrowserContentExtractor | None = None,
    browser: Browser | None = None,
) -> str:
    response = await fetch_browser_html_response(
        url,
        loader_name=loader_name,
        timeout_ms=timeout_ms,
        timeout_suggestion=timeout_suggestion,
        wait_until=wait_until,
        user_agent=user_agent,
        browser_headless=browser_headless,
        block_resource_types=block_resource_types,
        after_goto=after_goto,
        extract_content=extract_content,
        browser=browser,
    )
    return response.content


__all__ = [
    "DEFAULT_BLOCKED_RESOURCE_TYPES",
    "DEFAULT_BROWSER_USER_AGENT",
    "BrowserContentExtractor",
    "BrowserPageHook",
    "BrowserWaitUntil",
    "fetch_browser_html",
    "fetch_browser_html_response",
]
