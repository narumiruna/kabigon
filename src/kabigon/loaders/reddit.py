import logging
from typing import Any
from typing import cast
from urllib.parse import urlparse
from urllib.parse import urlunparse
from xml.etree import ElementTree as ET

import httpx

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderTimeoutError
from kabigon.core.loader import Loader
from kabigon.sources.applicability import parse_reddit_target

from .browser import DEFAULT_BROWSER_USER_AGENT
from .browser import fetch_browser_html
from .utils import html_to_markdown

logger = logging.getLogger(__name__)
USER_AGENT = DEFAULT_BROWSER_USER_AGENT


def check_reddit_url(url: str) -> None:
    """Check if URL is from Reddit.

    Args:
        url: The URL to check

    Raises:
        LoaderNotApplicableError: If URL is not from Reddit
    """
    parse_reddit_target(url)


def convert_to_old_reddit(url: str) -> str:
    """Convert Reddit URL to old.reddit.com format.

    Args:
        url: Original Reddit URL

    Returns:
        URL with old.reddit.com domain
    """
    parsed = urlparse(url)
    return str(urlunparse(parsed._replace(netloc="old.reddit.com")))


def to_reddit_json_url(url: str) -> str:
    """Normalize Reddit URL to a `www.reddit.com/.../.json` API URL."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if not path.endswith(".json"):
        path = f"{path}.json"
    return str(urlunparse(parsed._replace(netloc="www.reddit.com", path=path, query="", fragment="")))


def to_reddit_rss_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if not path.endswith(".rss"):
        path = f"{path}/.rss"
    return str(urlunparse(parsed._replace(netloc="www.reddit.com", path=path, query="", fragment="")))


def _post_markdown(post: dict[str, Any]) -> str:
    title = str(post.get("title") or "").strip()
    author = str(post.get("author") or "unknown")
    subreddit = str(post.get("subreddit") or "unknown")
    score = post.get("score")
    permalink = str(post.get("permalink") or "").strip()
    permalink_url = f"https://www.reddit.com{permalink}" if permalink else ""
    body = str(post.get("selftext") or "").strip()
    external_url = str(post.get("url") or "").strip()

    lines = [f"# {title or '[untitled]'}", "", f"- Author: u/{author}", f"- Subreddit: r/{subreddit}"]
    if score is not None:
        lines.append(f"- Score: {score}")
    if permalink_url:
        lines.append(f"- Permalink: {permalink_url}")
    if body:
        lines.extend(["", body])
    elif external_url:
        lines.extend(["", f"External URL: {external_url}"])
    return "\n".join(lines)


def _append_comments_markdown(lines: list[str], children: list[dict[str, Any]], depth: int = 0) -> None:
    indent = "  " * depth
    for child in children:
        if child.get("kind") != "t1":
            continue

        data = child.get("data")
        if not isinstance(data, dict):
            continue

        author = str(data.get("author") or "unknown")
        score = data.get("score")
        body = str(data.get("body") or "").strip()
        header = f"{indent}- u/{author}"
        if score is not None:
            header += f" ({score})"
        lines.append(header + ":")
        if body:
            lines.extend(f"{indent}  {body_line}" for body_line in body.splitlines())
        else:
            lines.append(f"{indent}  [no text]")

        replies = data.get("replies")
        if isinstance(replies, dict):
            replies_data = replies.get("data")
            if isinstance(replies_data, dict):
                replies_children = replies_data.get("children")
                if isinstance(replies_children, list):
                    _append_comments_markdown(lines, replies_children, depth=depth + 1)


def _children_from_listing(listing: object, api_url: str) -> list[dict[str, Any]]:
    if not isinstance(listing, dict):
        raise LoaderContentError("RedditLoader", api_url, "Invalid listing payload.")
    listing_dict = cast(dict[str, Any], listing)
    listing_data = listing_dict.get("data")
    if not isinstance(listing_data, dict):
        raise LoaderContentError("RedditLoader", api_url, "Invalid listing data payload.")
    children = listing_data.get("children")
    if not isinstance(children, list):
        raise LoaderContentError("RedditLoader", api_url, "Invalid listing children payload.")
    return [child for child in children if isinstance(child, dict)]


def _extract_post(payload: object, api_url: str) -> dict[str, Any]:
    if not isinstance(payload, list) or len(payload) < 1:
        raise LoaderContentError("RedditLoader", api_url, "Unexpected Reddit JSON payload shape.")
    post_children = _children_from_listing(payload[0], api_url)
    if not post_children:
        raise LoaderContentError("RedditLoader", api_url, "Post not found in Reddit JSON payload.")
    post_data = post_children[0].get("data")
    if not isinstance(post_data, dict):
        raise LoaderContentError("RedditLoader", api_url, "Invalid post entry in Reddit JSON payload.")
    return post_data


def _extract_comment_children(payload: object, api_url: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or len(payload) < 2:
        return []
    return _children_from_listing(payload[1], api_url)


def _atom_text(parent: ET.Element, tag: str) -> str:
    node = parent.find(f"{{http://www.w3.org/2005/Atom}}{tag}")
    return (node.text or "").strip() if node is not None else ""


def _rss_to_markdown(xml_text: str, source_url: str) -> str:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise LoaderContentError(
            "RedditLoader",
            source_url,
            f"Invalid RSS XML payload: {e}",
        ) from e

    feed_title = _atom_text(root, "title") or "Reddit Post"
    lines = [f"# {feed_title}", "", f"- URL Source: {source_url}", "", "## Entries", ""]
    entries = root.findall("{http://www.w3.org/2005/Atom}entry")
    if not entries:
        lines.append("(No entries)")
        return "\n".join(lines).strip()

    for entry in entries:
        entry_title = _atom_text(entry, "title") or "[untitled]"
        updated = _atom_text(entry, "updated")
        author = ""
        author_node = entry.find("{http://www.w3.org/2005/Atom}author")
        if author_node is not None:
            author = _atom_text(author_node, "name")
        content_node = entry.find("{http://www.w3.org/2005/Atom}content")
        content_html = (content_node.text or "").strip() if content_node is not None else ""
        content_md = html_to_markdown(content_html).strip() if content_html else ""

        lines.append(f"### {entry_title}")
        if author:
            lines.append(f"- Author: {author}")
        if updated:
            lines.append(f"- Updated: {updated}")
        lines.append("")
        lines.append(content_md or "(No content)")
        lines.append("")
    return "\n".join(lines).strip()


class RedditLoader(Loader):
    """Loader for Reddit posts and comments.

    Uses old.reddit.com for better content extraction without CAPTCHA.
    """

    def __init__(self, timeout: float = 30_000) -> None:
        """Initialize RedditLoader.

        Args:
            timeout: Timeout in milliseconds for page loading (default: 30 seconds)
        """
        self.timeout = timeout

    async def _load_via_json(self, url: str) -> str:
        api_url = to_reddit_json_url(url)
        timeout_seconds = self.timeout / 1000
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
                response = await client.get(api_url, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as e:
            raise LoaderTimeoutError(
                "RedditLoader",
                api_url,
                timeout_seconds,
                "Reddit JSON endpoint timed out. Try increasing the timeout.",
            ) from e
        except (httpx.HTTPError, ValueError) as e:
            raise LoaderContentError(
                "RedditLoader",
                api_url,
                f"Reddit JSON request failed: {e}",
                "Try again later or use the Playwright fallback path.",
            ) from e

        post_data = _extract_post(payload, api_url)
        comment_children = _extract_comment_children(payload, api_url)

        result_lines = [_post_markdown(post_data), "", "## Comments", ""]
        if comment_children:
            _append_comments_markdown(result_lines, comment_children)
        else:
            result_lines.append("(No comments)")
        return "\n".join(result_lines).strip()

    async def _load_via_rss(self, url: str) -> str:
        rss_url = to_reddit_rss_url(url)
        timeout_seconds = self.timeout / 1000
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
                response = await client.get(rss_url)
                response.raise_for_status()
        except httpx.TimeoutException as e:
            raise LoaderTimeoutError(
                "RedditLoader",
                rss_url,
                timeout_seconds,
                "Reddit RSS endpoint timed out. Try increasing the timeout.",
            ) from e
        except httpx.HTTPError as e:
            raise LoaderContentError(
                "RedditLoader",
                rss_url,
                f"Reddit RSS request failed: {e}",
                "Try again later or use the Playwright fallback path.",
            ) from e

        return _rss_to_markdown(response.text, rss_url)

    async def _load_via_old_reddit(self, url: str) -> str:
        old_reddit_url = convert_to_old_reddit(url)
        logger.debug("[RedditLoader] Converted to old Reddit: %s", old_reddit_url)

        content = await fetch_browser_html(
            old_reddit_url,
            loader_name="RedditLoader",
            timeout_ms=self.timeout,
            timeout_suggestion="Reddit pages can be slow to load. Try increasing the timeout.",
            wait_until="networkidle",
            user_agent=DEFAULT_BROWSER_USER_AGENT,
        )
        logger.debug("[RedditLoader] Page loaded successfully via old Reddit")
        return html_to_markdown(content)

    async def load(self, url: str) -> str:
        """Asynchronously load Reddit content from URL.

        Args:
            url: Reddit URL to load

        Returns:
            Loaded content as markdown

        Raises:
            LoaderNotApplicableError: If URL is not from Reddit
            LoaderTimeoutError: If page loading times out
        """
        logger.debug("[RedditLoader] Processing URL: %s", url)
        parse_reddit_target(url)
        try:
            result = await self._load_via_json(url)
        except (LoaderContentError, LoaderTimeoutError) as json_error:
            logger.warning("[RedditLoader] JSON endpoint failed, trying RSS fallback: %s", json_error)
            try:
                result = await self._load_via_rss(url)
            except (LoaderContentError, LoaderTimeoutError) as rss_error:
                logger.warning("[RedditLoader] RSS fallback failed, falling back to old Reddit: %s", rss_error)
                result = await self._load_via_old_reddit(url)
                logger.debug(
                    "[RedditLoader] Successfully extracted content from old Reddit fallback (%s chars)",
                    len(result),
                )
                return result
            logger.debug("[RedditLoader] Successfully extracted content from RSS fallback (%s chars)", len(result))
            return result
        else:
            logger.debug("[RedditLoader] Successfully extracted content from JSON endpoint (%s chars)", len(result))
            return result
