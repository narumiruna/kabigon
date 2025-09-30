from urllib.parse import urlparse
from urllib.parse import urlunparse

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
    return str(urlunparse(urlparse(url)._replace(netloc=new_domain)))


def check_x_url(url: str) -> None:
    if urlparse(url).netloc not in TWITTER_DOMAINS:
        raise ValueError(f"URL is not a Twitter URL: {url}")


class TwitterLoader(Loader):
    def __init__(self, timeout: float = 30_000) -> None:
        self.playwright_loader = PlaywrightLoader(wait_until="networkidle", timeout=timeout)

    def load(self, url: str) -> str:
        check_x_url(url)

        url = replace_domain(url)

        return self.playwright_loader.load(url)

    async def async_load(self, url: str):
        check_x_url(url)

        url = replace_domain(url)

        return await self.playwright_loader.async_load(url)
