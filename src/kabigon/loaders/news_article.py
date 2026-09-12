from __future__ import annotations

import logging
import time
from collections.abc import Awaitable
from collections.abc import Callable

from kabigon.core.errors import LoaderContentError
from kabigon.core.execution import record_attempt
from kabigon.core.execution import remaining_seconds
from kabigon.core.resources import Browser
from kabigon.core.resources import CurlSession
from kabigon.core.resources import HttpClient
from kabigon.core.resources import ResourceProvider
from kabigon.core.results import AttemptRecord
from kabigon.core.results import AttemptStatus
from kabigon.core.retrieval import RetrievedHtml

from .html_extractors import extract_article_body_from_json_ld
from .html_extractors import extract_first_tag_subtree
from .httpx import fetch_httpx_html
from .utils import html_to_markdown

logger = logging.getLogger(__name__)

DEFAULT_NEWS_ARTICLE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ),
}
_IGNORED_TAGS = {"script", "style", "noscript", "svg"}
ArticleExtractor = Callable[[str, str, str], str]
HtmlTransport = Callable[[str, str, dict[str, str]], Awaitable[str]]


def extract_news_article_main_html(html: str) -> str:
    return extract_first_tag_subtree(html, ("article", "main"), ignored_tags=_IGNORED_TAGS)


def extract_news_article_text(html: str, url: str, loader_name: str) -> str:
    json_ld_body = extract_article_body_from_json_ld(html)
    if json_ld_body:
        return json_ld_body
    result = html_to_markdown(extract_news_article_main_html(html)).strip()
    if not result:
        raise LoaderContentError(loader_name, url, "Could not find article body")
    return result


async def fetch_news_article_html(
    url: str,
    *,
    loader_name: str,
    headers: dict[str, str],
    http_client: HttpClient | None = None,
) -> str:
    response = await fetch_httpx_html(
        url,
        headers=headers,
        client=http_client,
        loader_name=loader_name,
        request_timeout=remaining_seconds(),
    )
    if "html" not in response.content_type.lower():
        raise LoaderContentError(loader_name, url, f"Expected HTML content, got: {response.content_type!r}")
    return response.content


def _transport_attempt(
    loader_id: str, status: AttemptStatus, started: float, error: BaseException | None = None
) -> None:
    record_attempt(
        AttemptRecord(
            loader_id,
            status,
            round(max(0.0, time.monotonic() - started), 6),
            type(error).__name__ if error is not None else None,
            "Article transport failed" if error is not None else None,
        )
    )


async def load_news_article(
    url: str,
    *,
    loader_name: str,
    validate_url: Callable[[str], object],
    headers: dict[str, str],
    extractor: ArticleExtractor = extract_news_article_text,
    registry_id: str | None = None,
    http_client: HttpClient | None = None,
    curl_session: CurlSession | None = None,
    browser: Browser | None = None,
    resource_provider: ResourceProvider | None = None,
) -> str:
    validate_url(url)
    source_id = registry_id or loader_name

    async def via_httpx(target: str, name: str, request_headers: dict[str, str]) -> str:
        active_http_client = await resource_provider.http_client() if resource_provider is not None else http_client
        if active_http_client is None:
            return await fetch_news_article_html(target, loader_name=name, headers=request_headers)
        return await fetch_news_article_html(
            target,
            loader_name=name,
            headers=request_headers,
            http_client=active_http_client,
        )

    async def via_curl(target: str, name: str, request_headers: dict[str, str]) -> str:
        from .curl_cffi import fetch_curl_html

        active_curl_session = await resource_provider.curl_session() if resource_provider is not None else curl_session
        response = await fetch_curl_html(
            target,
            request_timeout=remaining_seconds() or 20.0,
            headers=request_headers,
            session=active_curl_session,
            loader_name=name,
        )
        if "html" not in response.content_type.lower():
            raise LoaderContentError(name, target, f"Expected HTML content, got: {response.content_type!r}")
        return response.content

    async def via_browser(target: str, name: str, _request_headers: dict[str, str]) -> str:
        from .browser import fetch_browser_html_response

        async def fetch() -> RetrievedHtml:
            active_browser = await resource_provider.browser() if resource_provider is not None else browser
            return await fetch_browser_html_response(
                target,
                loader_name=name,
                timeout_ms=min(30_000, (remaining_seconds() or 30.0) * 1000),
                timeout_suggestion="Article page timed out while using the browser transport.",
                wait_until="domcontentloaded",
                browser=active_browser,
            )

        response = await resource_provider.run_browser(fetch) if resource_provider is not None else await fetch()
        if "html" not in response.content_type.lower():
            raise LoaderContentError(name, target, f"Expected HTML content, got: {response.content_type!r}")
        return response.content

    errors: list[Exception] = []
    for transport_id, transport in (("httpx", via_httpx), ("curl-cffi", via_curl), ("browser", via_browser)):
        started = time.monotonic()
        try:
            html = await transport(url, loader_name, headers)
            result = extractor(html, url, loader_name)
        except Exception as error:  # noqa: BLE001
            errors.append(error)
            _transport_attempt(f"{source_id}:{transport_id}", AttemptStatus.FAILED, started, error)
            continue
        _transport_attempt(f"{source_id}:{transport_id}", AttemptStatus.SUCCESS, started)
        return result

    reason = "; ".join(f"{type(error).__name__}: {error}" for error in errors)
    raise LoaderContentError(loader_name, url, f"All article transports failed: {reason}")


__all__ = [
    "DEFAULT_NEWS_ARTICLE_HEADERS",
    "extract_news_article_main_html",
    "extract_news_article_text",
    "fetch_news_article_html",
    "load_news_article",
]
