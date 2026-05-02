import logging
from contextlib import suppress

from playwright.async_api import Page
from playwright.async_api import TimeoutError

from kabigon.core.loader import Loader
from kabigon.sources.applicability import parse_truthsocial_target

from .browser import DEFAULT_BLOCKED_RESOURCE_TYPES
from .browser import DEFAULT_BROWSER_USER_AGENT
from .browser import fetch_browser_html
from .utils import html_to_markdown

logger = logging.getLogger(__name__)


def check_truthsocial_url(url: str) -> None:
    """Check if URL is from Truth Social.

    Args:
        url: The URL to check

    Raises:
        LoaderNotApplicableError: If URL is not from Truth Social
    """
    parse_truthsocial_target(url)


class TruthSocialLoader(Loader):
    """Loader for Truth Social posts.

    Truth Social requires JavaScript rendering and longer wait times
    for content to fully load.
    """

    def __init__(self, timeout: float = 60_000) -> None:
        """Initialize TruthSocialLoader.

        Args:
            timeout: Timeout in milliseconds for page loading (default: 60 seconds)
        """
        self.timeout = timeout

    async def load(self, url: str) -> str:
        """Load Truth Social content from URL.

        Args:
            url: Truth Social URL to load

        Returns:
            Loaded content as markdown

        Raises:
            LoaderNotApplicableError: If URL is not from Truth Social
            LoaderTimeoutError: If page loading times out
        """
        logger.debug("[TruthSocialLoader] Processing URL: %s", url)
        parse_truthsocial_target(url)

        async def wait_for_post_content(page: Page) -> None:
            with suppress(TimeoutError):
                await page.wait_for_selector(
                    "article, .status, [data-testid='status'], [data-testid='post-content']",
                    state="attached",
                    timeout=min(self.timeout, 5_000),
                )

        content = await fetch_browser_html(
            url,
            loader_name="TruthSocialLoader",
            timeout_ms=self.timeout,
            timeout_suggestion="Truth Social pages require JavaScript and can be slow. Try increasing the timeout.",
            wait_until="domcontentloaded",
            user_agent=DEFAULT_BROWSER_USER_AGENT,
            block_resource_types=DEFAULT_BLOCKED_RESOURCE_TYPES,
            after_goto=wait_for_post_content,
        )
        logger.debug("[TruthSocialLoader] Page loaded successfully")

        result = html_to_markdown(content)
        logger.debug("[TruthSocialLoader] Successfully extracted content (%s chars)", len(result))
        return result
