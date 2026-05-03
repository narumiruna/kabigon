import asyncio
import contextlib
import logging

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page
from playwright.async_api import TimeoutError

from kabigon.core.loader import Loader
from kabigon.sources.applicability import parse_twitter_target

from .browser import DEFAULT_BLOCKED_RESOURCE_TYPES
from .browser import DEFAULT_BROWSER_USER_AGENT
from .browser import fetch_browser_html
from .utils import html_to_markdown

logger = logging.getLogger(__name__)
TWEET_READY_SELECTORS = [
    'article [data-testid="tweetText"]',
    'article [data-testid="tweet"]',
    '[data-testid="tweetText"]',
]


def replace_domain(url: str, new_domain: str = "x.com") -> str:
    target = parse_twitter_target(url)
    if new_domain == "x.com":
        return target.normalized_url
    return target.normalized_url.replace("//x.com", f"//{new_domain}", 1)


def check_x_url(url: str) -> None:
    parse_twitter_target(url)


class TwitterLoader(Loader):
    def __init__(self, timeout: float = 20_000, wait_for_tweet_timeout: float = 15_000) -> None:
        self.timeout = timeout
        self.wait_for_tweet_timeout = wait_for_tweet_timeout

    async def _wait_for_any_selector(self, page: Page, *, selectors: list[str], timeout_ms: float) -> None:
        async def wait_one(selector: str) -> None:
            await page.wait_for_selector(selector, state="visible", timeout=timeout_ms)

        tasks = [asyncio.create_task(wait_one(selector)) for selector in selectors]
        try:
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=timeout_ms / 1000,
            )
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()

    async def load(self, url: str) -> str:
        logger.info("[TwitterLoader] Processing URL: %s", url)
        parse_twitter_target(url)

        url = replace_domain(url)
        logger.info("[TwitterLoader] Fetching normalized URL: %s", url)

        async def wait_for_tweet(page: Page) -> None:
            with contextlib.suppress(TimeoutError):
                await self._wait_for_any_selector(
                    page,
                    selectors=TWEET_READY_SELECTORS,
                    timeout_ms=min(self.timeout or self.wait_for_tweet_timeout, self.wait_for_tweet_timeout),
                )

        async def extract_tweet_content(page: Page) -> str:
            try:
                tweet_articles = page.locator("article").filter(has=page.locator('[data-testid="tweetText"]'))
                if await tweet_articles.count() > 0:
                    content = await tweet_articles.nth(0).evaluate("el => el.outerHTML")
                    logger.debug("[TwitterLoader] Extracted tweet article content")
                else:
                    content = await page.content()
                    logger.debug("[TwitterLoader] Using full page content")
            except (PlaywrightError, TimeoutError):
                content = await page.content()
                logger.debug("[TwitterLoader] Fallback to full page content after error")
            return content

        content = await fetch_browser_html(
            url,
            loader_name="TwitterLoader",
            timeout_ms=self.timeout,
            timeout_suggestion=(
                "Twitter/X pages can be slow. Try increasing the timeout or check if the page requires login."
            ),
            wait_until="domcontentloaded",
            user_agent=DEFAULT_BROWSER_USER_AGENT,
            block_resource_types=DEFAULT_BLOCKED_RESOURCE_TYPES,
            after_goto=wait_for_tweet,
            extract_content=extract_tweet_content,
        )
        result = html_to_markdown(content)
        logger.info("[TwitterLoader] Extracted Twitter content (%s chars)", len(result))
        return result
