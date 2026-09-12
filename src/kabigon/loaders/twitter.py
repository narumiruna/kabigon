import contextlib
import logging
import re
from urllib.parse import urlparse

from playwright.async_api import Page
from playwright.async_api import TimeoutError

from kabigon.core.errors import LoaderContentError
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


def _status_id(url: str) -> str | None:
    match = re.search(r"/status/([0-9]+)(?:/|$)", urlparse(url).path)
    return match.group(1) if match else None


def replace_domain(url: str, new_domain: str = "x.com") -> str:
    target = parse_twitter_target(url)
    if new_domain == "x.com":
        return target.normalized_url
    return target.normalized_url.replace("//x.com", f"//{new_domain}", 1)


class TwitterLoader(Loader):
    def __init__(self, timeout: float = 20_000, wait_for_tweet_timeout: float = 15_000) -> None:
        self.timeout = timeout
        self.wait_for_tweet_timeout = wait_for_tweet_timeout

    async def load(self, url: str) -> str:
        logger.info("[TwitterLoader] Processing URL: %s", url)
        parse_twitter_target(url)

        url = replace_domain(url)
        status_id = _status_id(url)
        logger.info("[TwitterLoader] Fetching normalized URL: %s", url)

        selectors = TWEET_READY_SELECTORS
        if status_id is not None:
            selectors = [
                f'article a[href$="/status/{status_id}"] time',
                f'article a[href$="/status/{status_id}/"] time',
                f'article a[href*="/status/{status_id}?"] time',
                f'article a[href*="/status/{status_id}#"] time',
            ]

        async def wait_for_tweet(page: Page) -> None:
            with contextlib.suppress(TimeoutError):
                await page.wait_for_selector(
                    ", ".join(selectors),
                    state="visible",
                    timeout=min(self.timeout or self.wait_for_tweet_timeout, self.wait_for_tweet_timeout),
                )

        async def extract_tweet_content(page: Page) -> str:
            if status_id is None:
                return await page.content()

            for article in await page.locator("article").all():
                # The first timestamp permalink identifies the article itself;
                # later permalinks may belong to a quoted tweet.
                permalink = article.locator('a[href*="/status/"]').filter(has=page.locator("time")).first
                if await permalink.count() == 0:
                    continue
                href = await permalink.get_attribute("href")
                if href and _status_id(href) == status_id:
                    return await article.evaluate("el => el.outerHTML")

            raise LoaderContentError("TwitterLoader", url, f"Could not find the requested tweet ({status_id})")

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
