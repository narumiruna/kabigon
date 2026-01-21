import logging
from urllib.parse import urlparse

from playwright.async_api import TimeoutError
from playwright.async_api import async_playwright

from kabigon.core.exception import LoaderNotApplicableError
from kabigon.core.exception import LoaderTimeoutError
from kabigon.core.loader import Loader

from .utils import html_to_markdown

logger = logging.getLogger(__name__)

TRUTHSOCIAL_DOMAINS = [
    "truthsocial.com",
    "www.truthsocial.com",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def check_truthsocial_url(url: str) -> None:
    """Check if URL is from Truth Social.

    Args:
        url: The URL to check

    Raises:
        LoaderNotApplicableError: If URL is not from Truth Social
    """
    netloc = urlparse(url).netloc
    if netloc not in TRUTHSOCIAL_DOMAINS:
        raise LoaderNotApplicableError(
            "TruthSocialLoader", url, f"Not a Truth Social URL. Expected domains: {', '.join(TRUTHSOCIAL_DOMAINS)}"
        )


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
        check_truthsocial_url(url)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            try:
                await page.goto(url, timeout=self.timeout, wait_until="networkidle")
                logger.debug("[TruthSocialLoader] Page loaded successfully")
            except TimeoutError as e:
                await browser.close()
                logger.warning("[TruthSocialLoader] Timeout after %ss: %s", self.timeout / 1000, url)
                raise LoaderTimeoutError(
                    "TruthSocialLoader",
                    url,
                    self.timeout / 1000,
                    "Truth Social pages require JavaScript and can be slow. Try increasing the timeout.",
                ) from e

            content = await page.content()
            await browser.close()

            result = html_to_markdown(content)
            logger.debug("[TruthSocialLoader] Successfully extracted content (%s chars)", len(result))
            return result
