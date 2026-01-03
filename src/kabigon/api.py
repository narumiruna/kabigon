from .compose import Compose
from .pdf import PDFLoader
from .playwright import PlaywrightLoader
from .ptt import PttLoader
from .reddit import RedditLoader
from .reel import ReelLoader
from .truthsocial import TruthSocialLoader
from .twitter import TwitterLoader
from .youtube import YoutubeLoader
from .youtube_ytdlp import YoutubeYtdlpLoader


def _get_default_loader() -> Compose:
    """Get the default loader composition used by CLI.

    Returns:
        Compose: Default loader chain with all available loaders
    """
    return Compose(
        [
            PttLoader(),
            TwitterLoader(),
            TruthSocialLoader(),
            RedditLoader(),
            YoutubeLoader(),
            ReelLoader(),
            YoutubeYtdlpLoader(),
            PDFLoader(),
            PlaywrightLoader(timeout=50_000, wait_until="networkidle"),
            PlaywrightLoader(timeout=10_000),
        ]
    )


def load_url_sync(url: str) -> str:
    """Load content from a URL using the default loader chain.

    This is a convenience function that uses the same loader chain as the CLI.
    It tries each loader in sequence until one succeeds.

    Args:
        url: The URL to load content from

    Returns:
        str: Extracted content as markdown

    Raises:
        Exception: If all loaders fail to load the URL

    Example:
        >>> import kabigon
        >>> text = kabigon.load_url("https://example.com")
        >>> print(text)
    """
    loader = _get_default_loader()
    return loader.load_sync(url)


async def load_url(url: str) -> str:
    """Asynchronously load content from a URL using the default loader chain.

    This is an async version of load_url() that can be used in async contexts.

    Args:
        url: The URL to load content from

    Returns:
        str: Extracted content as markdown

    Raises:
        Exception: If all loaders fail to load the URL

    Example:
        >>> import asyncio
        >>> import kabigon
        >>> async def main():
        ...     text = await kabigon.load_url_async("https://example.com")
        ...     print(text)
        >>> asyncio.run(main())
    """
    loader = _get_default_loader()
    return await loader.load(url)
