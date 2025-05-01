import httpx

from .loader import Loader
from .utils import html_to_markdown


class HttpxLoader(Loader):
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self.headers = headers

    def load(self, url: str) -> str:
        response = httpx.get(url, headers=self.headers, follow_redirects=False)
        response.raise_for_status()
        return html_to_markdown(response.content)

    async def async_load(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, follow_redirects=True)
            response.raise_for_status()
            return html_to_markdown(response.content)
