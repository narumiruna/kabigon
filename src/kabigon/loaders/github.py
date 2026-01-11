from __future__ import annotations

from urllib.parse import urlparse

import httpx

from kabigon.core.exception import InvalidURLError
from kabigon.core.loader import Loader

GITHUB_HOST = "github.com"
RAW_GITHUB_HOST = "raw.githubusercontent.com"


def check_github_url(url: str) -> None:
    host = urlparse(url).netloc
    if host not in {GITHUB_HOST, RAW_GITHUB_HOST}:
        raise InvalidURLError(url, "GitHub")


def to_raw_github_url(url: str) -> str:
    """Convert a GitHub blob URL to a raw.githubusercontent.com URL.

    Supports:
      - https://github.com/<owner>/<repo>/blob/<ref>/<path>
      - https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>
    """
    parsed = urlparse(url)
    if parsed.netloc == RAW_GITHUB_HOST:
        return url

    if parsed.netloc != GITHUB_HOST:
        raise InvalidURLError(url, "GitHub")

    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 5 or parts[2] != "blob":
        raise InvalidURLError(url, "GitHub blob")

    owner, repo, _, ref = parts[:4]
    path = "/".join(parts[4:])
    if not path:
        raise InvalidURLError(url, "GitHub blob file")

    return f"https://{RAW_GITHUB_HOST}/{owner}/{repo}/{ref}/{path}"


class GitHubLoader(Loader):
    async def load(self, url: str) -> str:
        check_github_url(url)
        raw_url = to_raw_github_url(url)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                raw_url,
                follow_redirects=True,
                headers={"Accept": "text/plain, text/markdown;q=0.9, */*;q=0.1"},
            )
            response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "text" not in content_type and "json" not in content_type and "xml" not in content_type:
            raise InvalidURLError(url, f"GitHub text content-type (got {content_type!r})")

        return response.text
