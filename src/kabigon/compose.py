from urllib.parse import urlparse
from urllib.parse import urlunparse

from loguru import logger

from .errors import LoaderError
from .loader import Loader

REPLACEMENTS = {
    "api.fxtwitter.com": [
        "twitter.com",
        "x.com",
        "fxtwitter.com",
        "vxtwitter.com",
        "fixvx.com",
        "twittpr.com",
        "fixupx.com",
    ]
}


def replace_domain(url: str) -> str:
    parsed = urlparse(url)
    for target, source in REPLACEMENTS.items():
        if parsed.netloc in source:
            fixed_url = parsed._replace(netloc=target)
            return urlunparse(fixed_url)
    return url


class Compose(Loader):
    def __init__(self, loaders: list[Loader]) -> None:
        self.loaders = loaders

    def load(self, url: str) -> str:
        url = replace_domain(url)

        for loader in self.loaders:
            try:
                content = loader.load(url)

                if not content:
                    logger.info("[{}] Failed to load URL: {}, got empty result", loader.__class__.__name__, url)
                    continue

                logger.info("[{}] Successfully loaded URL: {}", loader.__class__.__name__, url)
                return content

            except Exception as e:
                logger.info("[{}] Failed to load URL: {}, got error: {}", loader.__class__.__name__, url, e)

        raise LoaderError(f"Failed to load URL: {url}")

    async def async_load(self, url: str) -> str:
        url = replace_domain(url)

        for loader in self.loaders:
            try:
                content = await loader.async_load(url)

                if not content:
                    logger.info("[{}] Failed to load URL: {}, got empty result", loader.__class__.__name__, url)
                    continue

                logger.info("[{}] Successfully loaded URL: {}", loader.__class__.__name__, url)
                return content

            except Exception as e:
                logger.info("[{}] Failed to load URL: {}, got error: {}", loader.__class__.__name__, url, e)

        raise LoaderError(f"Failed to load URL: {url}")
