from __future__ import annotations

import asyncio
import io
import logging
from collections.abc import Awaitable
from collections.abc import Callable
from pathlib import Path
from typing import IO
from typing import Any

import httpx
from curl_cffi import requests as curl_requests
from pypdf import PdfReader

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderNotApplicableError
from kabigon.core.execution import remaining_seconds
from kabigon.core.loader import Loader
from kabigon.core.resources import ResourceProvider
from kabigon.sources.applicability import parse_pdf_target
from kabigon.sources.applicability import require_loader_applicability

logger = logging.getLogger(__name__)
DEFAULT_HEADERS = {
    "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8,en-US;q=0.7,en;q=0.6",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    ),
}
DEFAULT_TIMEOUT = 20.0
BlockingRunner = Callable[[Callable[[], str]], Awaitable[str]]


class PDFLoader(Loader):
    def __init__(
        self,
        resource_provider: ResourceProvider | None = None,
        run_blocking: BlockingRunner | None = None,
    ) -> None:
        self.resource_provider = resource_provider
        self.run_blocking = run_blocking

    async def _parse(self, source: str | Path | IO[Any]) -> str:
        def operation() -> str:
            return read_pdf_content(source)

        if self.run_blocking is not None:
            return await self.run_blocking(operation)
        return await asyncio.to_thread(operation)

    async def load(self, url_or_file: str) -> str:  # ty:ignore[invalid-method-override]
        require_loader_applicability("PDFLoader", url_or_file, parse_pdf_target)

        if not url_or_file.startswith("http"):
            try:
                return await self._parse(url_or_file)
            except Exception as error:
                raise LoaderContentError(
                    "PDFLoader",
                    url_or_file,
                    f"Failed to read local PDF: {error}",
                    "Check that the file exists and is a valid PDF.",
                ) from error

        content, content_type = await fetch_remote_pdf(url_or_file, resource_provider=self.resource_provider)
        if "application/pdf" not in content_type:
            raise LoaderNotApplicableError("PDFLoader", url_or_file, f"Not a PDF file (content-type: {content_type})")

        try:
            return await self._parse(io.BytesIO(content))
        except Exception as error:
            raise LoaderContentError(
                "PDFLoader",
                url_or_file,
                f"Failed to parse PDF: {error}",
                "The PDF may be corrupted or use unsupported features.",
            ) from error


async def fetch_remote_pdf(url: str, *, resource_provider: ResourceProvider | None = None) -> tuple[bytes, str]:
    remaining = remaining_seconds()
    timeout = min(DEFAULT_TIMEOUT, remaining) if remaining is not None else DEFAULT_TIMEOUT
    try:
        if resource_provider is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=DEFAULT_HEADERS, follow_redirects=True, timeout=timeout)
        else:
            client = await resource_provider.http_client()
            response = await client.get(url, headers=DEFAULT_HEADERS, follow_redirects=True, timeout=timeout)
        response.raise_for_status()
    except httpx.TransportError as httpx_error:
        logger.warning("[PDFLoader] httpx transport failed, retrying with curl_cffi: %s", httpx_error)
        try:
            if resource_provider is None:
                async with curl_requests.AsyncSession(impersonate="chrome") as session:
                    fallback_response = await session.get(
                        url,
                        headers=DEFAULT_HEADERS,
                        timeout=timeout,
                        allow_redirects=True,
                    )
            else:
                session = await resource_provider.curl_session()
                fallback_response = await session.get(
                    url,
                    headers=DEFAULT_HEADERS,
                    timeout=timeout,
                    allow_redirects=True,
                )
            fallback_response.raise_for_status()
        except Exception as fallback_error:
            raise LoaderContentError(
                "PDFLoader",
                url,
                f"HTTP request failed: {httpx_error}; curl_cffi fallback failed: {fallback_error}",
                "Check that the URL is accessible and valid.",
            ) from fallback_error
        return fallback_response.content, fallback_response.headers.get("content-type", "")
    except httpx.HTTPError as error:
        raise LoaderContentError(
            "PDFLoader", url, f"HTTP error: {error}", "Check that the URL is accessible and valid."
        ) from error

    return response.content, response.headers.get("content-type", "")


def read_pdf_content(f: str | Path | IO[Any]) -> str:
    lines: list[str] = []
    with PdfReader(f) as reader:
        for page in reader.pages:
            text = page.extract_text(extraction_mode="plain")
            for line in text.splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
    return "\n".join(lines)
