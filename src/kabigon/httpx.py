import httpx

from .loader import Loader
from .utils import html_to_markdown

DEFAULT_HEADERS = {
    "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8,en-US;q=0.7,en;q=0.6",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",  # noqa
    "Cookie": "over18=1",  # Required for some sites like PTT
}


class HttpxLoader(Loader):
    def load(self, url: str) -> str:
        response = httpx.get(url, headers=DEFAULT_HEADERS, follow_redirects=True)
        response.raise_for_status()
        return html_to_markdown(response.content)

    async def async_load(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=DEFAULT_HEADERS, follow_redirects=True)
            response.raise_for_status()
            return html_to_markdown(response.content)
