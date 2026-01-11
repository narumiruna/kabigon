from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

from kabigon.core.exception import InvalidURLError
from kabigon.core.loader import Loader

from .utils import html_to_markdown

GITHUB_HOST = "github.com"
RAW_GITHUB_HOST = "raw.githubusercontent.com"

_VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

_IGNORED_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "nav",
    "header",
    "footer",
}


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


class _SubtreeHTMLExtractor(HTMLParser):
    def __init__(self, root_tag: str) -> None:
        super().__init__(convert_charrefs=True)
        self.root_tag = root_tag
        self._capturing = False
        self._depth = 0
        self._ignored_depth = 0
        self._out: list[str] = []

    def get_html(self) -> str:
        return "".join(self._out).strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == self.root_tag and not self._capturing:
            self._capturing = True
            self._depth = 1
            self._out.append(self.get_starttag_text() or f"<{tag}>")
            return

        if not self._capturing:
            return

        if tag in _IGNORED_TAGS:
            self._ignored_depth += 1
            return

        self._out.append(self.get_starttag_text() or f"<{tag}>")
        if tag not in _VOID_TAGS:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if not self._capturing:
            return

        if self._ignored_depth:
            if tag in _IGNORED_TAGS:
                self._ignored_depth -= 1
            return

        self._out.append(f"</{tag}>")
        if tag not in _VOID_TAGS:
            self._depth -= 1

        if self._depth <= 0:
            self._capturing = False

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self._capturing:
            return
        if self._ignored_depth or tag in _IGNORED_TAGS:
            return
        self._out.append(self.get_starttag_text() or f"<{tag} />")

    def handle_data(self, data: str) -> None:
        if not self._capturing or self._ignored_depth:
            return
        self._out.append(data)


def extract_main_html(html: str) -> str:
    """Extract GitHub's primary content area without site-specific selectors."""
    for tag in ("main", "article"):
        parser = _SubtreeHTMLExtractor(tag)
        parser.feed(html)
        extracted = parser.get_html()
        if extracted:
            return extracted
    return html


class GitHubLoader(Loader):
    async def load(self, url: str) -> str:
        check_github_url(url)
        parsed = urlparse(url)

        if parsed.netloc == RAW_GITHUB_HOST or "/blob/" in parsed.path:
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

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                follow_redirects=True,
                headers={
                    "Accept": "text/html,application/xhtml+xml",
                    "User-Agent": "kabigon (httpx)",
                },
            )
            response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type:
            raise InvalidURLError(url, f"GitHub HTML content-type (got {content_type!r})")

        main_html = extract_main_html(response.text)
        return html_to_markdown(main_html)
