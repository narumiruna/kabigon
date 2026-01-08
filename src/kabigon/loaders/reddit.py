from urllib.parse import urlparse
from urllib.parse import urlunparse

from playwright.async_api import async_playwright

from kabigon.core.exception import InvalidURLError
from kabigon.core.loader import Loader

from .utils import html_to_markdown

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
        ValueError: If URL is not from Reddit
    """
    netloc = urlparse(url).netloc
    if netloc not in REDDIT_DOMAINS:
        raise InvalidURLError(url, "Reddit")


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
            ValueError: If URL is not from Reddit
        """
        check_reddit_url(url)
        url = convert_to_old_reddit(url)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()
            await page.goto(url, timeout=self.timeout, wait_until="networkidle")
            content = await page.content()
            await browser.close()

            return html_to_markdown(content)
