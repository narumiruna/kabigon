from . import loaders
from .core.loader import Loader
from .loader_registry import DEFAULT_PIPELINE_STEP_NAMES
from .loader_registry import LOADER_SPECS_BY_NAME
from .routing import route_url_to_pipeline_names


def _get_default_loader() -> loaders.Compose:
    """Get the default fallback loader composition.

    Returns:
        Compose: Default loader chain used as routed fallback
    """
    loader_chain = _build_loaders(DEFAULT_PIPELINE_STEP_NAMES)
    return loaders.Compose(loader_chain)


def _build_pipeline_ids(url: str) -> list[str]:
    targeted = route_url_to_pipeline_names(url)
    fallback = [name for name in DEFAULT_PIPELINE_STEP_NAMES if name not in targeted]
    return [*targeted, *fallback]


def _build_loaders(step_names: list[str]) -> list[Loader]:
    return [LOADER_SPECS_BY_NAME[name].factory() for name in step_names]


def _get_loader_for_url(url: str) -> Loader:
    pipeline = _build_pipeline_ids(url)
    loader_chain = _build_loaders(pipeline)
    if len(loader_chain) == 1:
        return loader_chain[0]
    return loaders.Compose(loader_chain)


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
    loader = _get_loader_for_url(url)
    return loader.load_sync(url)


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
    loader = _get_loader_for_url(url)
    return await loader.load(url)
