from urllib.parse import urlparse
from urllib.parse import urlunparse

from .errors import NotTwitterURLError
from .loader import Loader
from .playwright import PlaywrightLoader

TWITTER_DOMAINS = [
    "twitter.com",
    "x.com",
    "fxtwitter.com",
    "vxtwitter.com",
    "fixvx.com",
    "twittpr.com",
    "api.fxtwitter.com",
    "fixupx.com",
]


def replace_domain(url: str, new_domain: str = "x.com") -> str:
    return urlunparse(urlparse(url)._replace(netloc=new_domain))


def is_x_url(url: str) -> bool:
    return urlparse(url).netloc in TWITTER_DOMAINS


class TwitterLoader(Loader):
    def __init__(self) -> None:
        self.playwright_loader = PlaywrightLoader(wait_until="networkidle")

    def load(self, url: str) -> str:
        if not is_x_url(url):
            raise NotTwitterURLError(url)

        url = replace_domain(url)

        return self.playwright_loader.load(url)

    async def async_load(self, url: str):
        if not is_x_url(url):
            raise NotTwitterURLError(url)

        url = replace_domain(url)

        return await self.playwright_loader.async_load(url)
