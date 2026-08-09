import io
import logging
from pathlib import Path
from typing import IO
from typing import Any

import httpx
from curl_cffi import requests as curl_requests
from pypdf import PdfReader

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderNotApplicableError
from kabigon.core.loader import Loader
from kabigon.sources.applicability import parse_pdf_target
from kabigon.sources.applicability import require_loader_applicability

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8,en-US;q=0.7,en;q=0.6",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",  # noqa
}
DEFAULT_TIMEOUT = 20.0


class PDFLoader(Loader):
    async def load(self, url_or_file: str) -> str:  # ty:ignore[invalid-method-override]
        logger.info("[PDFLoader] Processing URL or file: %s", url_or_file)
        require_loader_applicability("PDFLoader", url_or_file, parse_pdf_target)

        if not url_or_file.startswith("http"):
            # Local file
            logger.info("[PDFLoader] Reading local PDF file")
            logger.debug("[PDFLoader] Local PDF path: %s", url_or_file)
            try:
                result = read_pdf_content(url_or_file)
            except Exception as e:
                logger.warning("[PDFLoader] Failed to read local PDF: %s", e)
                raise LoaderContentError(
                    "PDFLoader",
                    url_or_file,
                    f"Failed to read local PDF: {e}",
                    "Check that the file exists and is a valid PDF.",
                ) from e
            else:
                logger.info("[PDFLoader] Loaded local PDF content (%s chars)", len(result))
                return result

        # Remote URL
        logger.info("[PDFLoader] Fetching remote PDF")
        content, content_type = await fetch_remote_pdf(url_or_file)
        if "application/pdf" not in content_type:
            logger.debug("[PDFLoader] Not a PDF (content-type: %s)", content_type)
            raise LoaderNotApplicableError("PDFLoader", url_or_file, f"Not a PDF file (content-type: {content_type})")

        try:
            result = read_pdf_content(io.BytesIO(content))
        except Exception as e:
            logger.warning("[PDFLoader] Failed to parse PDF: %s", e)
            raise LoaderContentError(
                "PDFLoader",
                url_or_file,
                f"Failed to parse PDF: {e}",
                "The PDF may be corrupted or use unsupported features.",
            ) from e
        else:
            logger.info("[PDFLoader] Loaded remote PDF content (%s chars)", len(result))
            return result


async def fetch_remote_pdf(url: str) -> tuple[bytes, str]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=DEFAULT_HEADERS, follow_redirects=True)
            response.raise_for_status()
    except httpx.TransportError as httpx_error:
        logger.warning("[PDFLoader] httpx transport failed, retrying with curl_cffi: %s", httpx_error)
        try:
            async with curl_requests.AsyncSession(impersonate="chrome") as session:
                fallback_response = await session.get(
                    url,
                    headers=DEFAULT_HEADERS,
                    timeout=DEFAULT_TIMEOUT,
                    allow_redirects=True,
                )
                fallback_response.raise_for_status()
        except Exception as fallback_error:
            logger.warning("[PDFLoader] curl_cffi fallback failed: %s", fallback_error)
            raise LoaderContentError(
                "PDFLoader",
                url,
                f"HTTP request failed: {httpx_error}; curl_cffi fallback failed: {fallback_error}",
                "Check that the URL is accessible and valid.",
            ) from fallback_error
        return fallback_response.content, fallback_response.headers.get("content-type", "")
    except httpx.HTTPError as error:
        logger.warning("[PDFLoader] HTTP error: %s", error)
        raise LoaderContentError(
            "PDFLoader", url, f"HTTP error: {error}", "Check that the URL is accessible and valid."
        ) from error

    return response.content, response.headers.get("content-type", "")


def read_pdf_content(f: str | Path | IO[Any]) -> str:
    lines = []
    with PdfReader(f) as reader:
        for page in reader.pages:
            text = page.extract_text(extraction_mode="plain")
            for line in text.splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
    return "\n".join(lines)
