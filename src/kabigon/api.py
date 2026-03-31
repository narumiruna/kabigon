from .retrieval.orchestrator import resolve_loader


def load_url_sync(url: str) -> str:
    """Load content from a URL using routed pipeline + default fallback.

    The function first routes URL types (for example YouTube -> YouTube loaders),
    then appends the remaining default fallback loaders without duplicates.

    Args:
        url: The URL to load content from

    Returns:
        str: Extracted content as markdown

    Raises:
        Exception: If all loaders fail to load the URL

    Example:
        >>> import kabigon
        >>> text = kabigon.load_url_sync("https://example.com")
        >>> print(text)
    """
    return resolve_loader(url).load_sync(url)


async def load_url(url: str) -> str:
    """Asynchronously load content from a URL using routed pipeline + default fallback.

    This is an async version of load_url_sync() for async contexts.

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
        ...     text = await kabigon.load_url("https://example.com")
        ...     print(text)
        >>> asyncio.run(main())
    """
    return await resolve_loader(url).load(url)
