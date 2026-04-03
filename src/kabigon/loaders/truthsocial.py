import logging
from contextlib import suppress
from typing import Literal

from playwright.async_api import Request
from playwright.async_api import Route
from playwright.async_api import TimeoutError
from playwright.async_api import async_playwright

from kabigon.domain.errors import LoaderTimeoutError
from kabigon.domain.loader import Loader

from .url_match import ensure_host_in
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
    ensure_host_in(url, TRUTHSOCIAL_DOMAINS, loader_name="TruthSocialLoader", source_name="Truth Social")


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
            wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "domcontentloaded"

            async def route_handler(route: Route, request: Request) -> None:
                if request.resource_type in {"image", "media", "font"}:
                    await route.abort()
                    return
                await route.continue_()

            await page.route("**/*", route_handler)

            try:
                await page.goto(url, timeout=self.timeout, wait_until=wait_until)
                with suppress(TimeoutError):
                    await page.wait_for_selector(
                        "article, .status, [data-testid='status'], [data-testid='post-content']",
                        state="attached",
                        timeout=min(self.timeout, 5_000),
                    )
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
