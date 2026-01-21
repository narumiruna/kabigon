import logging
from urllib.parse import urlparse
from urllib.parse import urlunparse

from playwright.async_api import TimeoutError
from playwright.async_api import async_playwright

from kabigon.core.exception import LoaderNotApplicableError
from kabigon.core.exception import LoaderTimeoutError
from kabigon.core.loader import Loader

from .utils import html_to_markdown

logger = logging.getLogger(__name__)

REDDIT_DOMAINS = [
    "reddit.com",
    "www.reddit.com",
    "old.reddit.com",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def check_reddit_url(url: str) -> None:
    """Check if URL is from Reddit.

    Args:
        url: The URL to check

    Raises:
        LoaderNotApplicableError: If URL is not from Reddit
    """
    netloc = urlparse(url).netloc
    if netloc not in REDDIT_DOMAINS:
        raise LoaderNotApplicableError(
            "RedditLoader",
            url,
            f"Not a Reddit URL. Expected domains: {', '.join(REDDIT_DOMAINS)}"
        )


def convert_to_old_reddit(url: str) -> str:
    """Convert Reddit URL to old.reddit.com format.

    Args:
        url: Original Reddit URL

    Returns:
        URL with old.reddit.com domain
    """
    parsed = urlparse(url)
    return str(urlunparse(parsed._replace(netloc="old.reddit.com")))


class RedditLoader(Loader):
    """Loader for Reddit posts and comments.

    Uses old.reddit.com for better content extraction without CAPTCHA.
    """

    def __init__(self, timeout: float = 30_000) -> None:
        """Initialize RedditLoader.

        Args:
            timeout: Timeout in milliseconds for page loading (default: 30 seconds)
        """
        self.timeout = timeout

    async def load(self, url: str) -> str:
        """Asynchronously load Reddit content from URL.

        Args:
            url: Reddit URL to load

        Returns:
            Loaded content as markdown

        Raises:
            LoaderNotApplicableError: If URL is not from Reddit
            LoaderTimeoutError: If page loading times out
        """
        logger.debug(f"[RedditLoader] Processing URL: {url}")
        check_reddit_url(url)
        url = convert_to_old_reddit(url)
        logger.debug(f"[RedditLoader] Converted to old Reddit: {url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            try:
                await page.goto(url, timeout=self.timeout, wait_until="networkidle")
                logger.debug("[RedditLoader] Page loaded successfully")
            except TimeoutError as e:
                await browser.close()
                logger.warning(f"[RedditLoader] Timeout after {self.timeout / 1000}s: {url}")
                raise LoaderTimeoutError(
                    "RedditLoader",
                    url,
                    self.timeout / 1000,
                    "Reddit pages can be slow to load. Try increasing the timeout."
                ) from e

            content = await page.content()
            await browser.close()

            result = html_to_markdown(content)
            logger.debug(f"[RedditLoader] Successfully extracted content ({len(result)} chars)")
            return result
