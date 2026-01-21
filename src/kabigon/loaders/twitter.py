import asyncio
import contextlib
import logging
from urllib.parse import urlparse
from urllib.parse import urlunparse

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page
from playwright.async_api import Request
from playwright.async_api import Route
from playwright.async_api import TimeoutError
from playwright.async_api import async_playwright

from kabigon.core.exception import LoaderNotApplicableError
from kabigon.core.exception import LoaderTimeoutError
from kabigon.core.loader import Loader

from .utils import html_to_markdown

logger = logging.getLogger(__name__)
TWITTER_DOMAINS = [
    "twitter.com",
    "x.com",
    "fxtwitter.com",
    "vxtwitter.com",
    "fixvx.com",
    "twittpr.com",
    "api.fxtwitter.com",
    "fixupx.com",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

TWEET_READY_SELECTORS = [
    'article [data-testid="tweetText"]',
    'article [data-testid="tweet"]',
    '[data-testid="tweetText"]',
]


def replace_domain(url: str, new_domain: str = "x.com") -> str:
    return str(urlunparse(urlparse(url)._replace(netloc=new_domain)))


def check_x_url(url: str) -> None:
    if urlparse(url).netloc not in TWITTER_DOMAINS:
        raise LoaderNotApplicableError(
            "TwitterLoader",
            url,
            f"Not a Twitter/X URL. Expected domains: {', '.join(TWITTER_DOMAINS)}"
        )


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
        logger.debug(f"[TwitterLoader] Processing URL: {url}")
        check_x_url(url)

        url = replace_domain(url)
        logger.debug(f"[TwitterLoader] Normalized URL: {url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            async def route_handler(route: Route, request: Request) -> None:
                if request.resource_type in {"image", "media", "font"}:
                    await route.abort()
                    return
                await route.continue_()

            await page.route("**/*", route_handler)

            try:
                await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
            except TimeoutError as e:
                await browser.close()
                logger.warning(f"[TwitterLoader] Timeout during page load: {e}")
                raise LoaderTimeoutError(
                    "TwitterLoader",
                    url,
                    self.timeout / 1000,
                    "Twitter/X pages can be slow. Try increasing the timeout or check if the page requires login."
                ) from e

            with contextlib.suppress(TimeoutError):
                await self._wait_for_any_selector(
                    page,
                    selectors=TWEET_READY_SELECTORS,
                    timeout_ms=min(self.timeout or self.wait_for_tweet_timeout, self.wait_for_tweet_timeout),
                )

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

            await browser.close()
            result = html_to_markdown(content)
            logger.debug(f"[TwitterLoader] Successfully converted to markdown ({len(result)} chars)")
            return result
