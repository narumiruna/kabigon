from __future__ import annotations

import logging
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Literal

from playwright.async_api import Page
from playwright.async_api import Request
from playwright.async_api import Route
from playwright.async_api import TimeoutError
from playwright.async_api import async_playwright

from kabigon.core.errors import LoaderTimeoutError

BrowserPageHook = Callable[[Page], Awaitable[None]]
BrowserContentExtractor = Callable[[Page], Awaitable[str]]
BrowserWaitUntil = Literal["commit", "domcontentloaded", "load", "networkidle"]

DEFAULT_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
DEFAULT_BLOCKED_RESOURCE_TYPES = frozenset({"font", "image", "media"})

logger = logging.getLogger(__name__)


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
) -> str:
    async with async_playwright() as p:
        logger.debug("[%s] Launching Chromium browser (headless=%s)", loader_name, browser_headless)
        browser = await p.chromium.launch(headless=browser_headless)
        context = None
        try:
            if user_agent is None:
                logger.debug("[%s] Creating browser context", loader_name)
                context = await browser.new_context()
            else:
                logger.debug("[%s] Creating browser context with custom user agent", loader_name)
                context = await browser.new_context(user_agent=user_agent)
            page = await context.new_page()

            if block_resource_types:
                logger.debug("[%s] Blocking browser resource types: %s", loader_name, sorted(block_resource_types))

                async def route_handler(route: Route, request: Request) -> None:
                    if request.resource_type in block_resource_types:
                        await route.abort()
                        return
                    await route.continue_()

                await page.route("**/*", route_handler)

            try:
                logger.debug(
                    "[%s] Navigating to URL (timeout_ms=%s, wait_until=%s)",
                    loader_name,
                    timeout_ms,
                    wait_until,
                )
                if wait_until is None:
                    await page.goto(url, timeout=timeout_ms)
                else:
                    await page.goto(url, timeout=timeout_ms, wait_until=wait_until)
            except TimeoutError as e:
                timeout_seconds = (timeout_ms or 0) / 1000 if timeout_ms else 30
                logger.warning("[%s] Browser navigation timed out after %ss", loader_name, timeout_seconds)
                raise LoaderTimeoutError(loader_name, url, timeout_seconds, timeout_suggestion) from e

            if after_goto is not None:
                logger.debug("[%s] Running post-navigation hook", loader_name)
                await after_goto(page)

            if extract_content is not None:
                logger.debug("[%s] Extracting browser content with custom extractor", loader_name)
                return await extract_content(page)
            logger.debug("[%s] Extracting full browser page content", loader_name)
            return await page.content()
        finally:
            if context is not None:
                logger.debug("[%s] Closing browser context", loader_name)
                await context.close()
            logger.debug("[%s] Closing Chromium browser", loader_name)
            await browser.close()


__all__ = [
    "DEFAULT_BLOCKED_RESOURCE_TYPES",
    "DEFAULT_BROWSER_USER_AGENT",
    "BrowserContentExtractor",
    "BrowserPageHook",
    "BrowserWaitUntil",
    "fetch_browser_html",
]
