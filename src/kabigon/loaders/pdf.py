import io
import logging
from pathlib import Path
from typing import IO
from typing import Any

import httpx
from pypdf import PdfReader

from kabigon.core.exception import LoaderContentError
from kabigon.core.exception import LoaderNotApplicableError
from kabigon.core.loader import Loader

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8,en-US;q=0.7,en;q=0.6",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",  # noqa
}


class PDFLoader(Loader):
    async def load(self, url_or_file: str) -> str:  # ty:ignore[invalid-method-override]
        logger.debug(f"[PDFLoader] Processing: {url_or_file}")

        if not url_or_file.startswith("http"):
            # Local file
            logger.debug(f"[PDFLoader] Reading local file: {url_or_file}")
            try:
                result = read_pdf_content(url_or_file)
                logger.debug(f"[PDFLoader] Successfully read local PDF ({len(result)} chars)")
                return result
            except Exception as e:
                logger.warning(f"[PDFLoader] Failed to read local PDF: {e}")
                raise LoaderContentError(
                    "PDFLoader",
                    url_or_file,
                    f"Failed to read local PDF: {e}",
                    "Check that the file exists and is a valid PDF."
                ) from e

        # Remote URL
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url_or_file, headers=DEFAULT_HEADERS, follow_redirects=True)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                logger.warning(f"[PDFLoader] HTTP error: {e}")
                raise LoaderContentError(
                    "PDFLoader",
                    url_or_file,
                    f"HTTP error: {e}",
                    "Check that the URL is accessible and valid."
                ) from e

            content_type = resp.headers.get("content-type", "")
            if "application/pdf" not in content_type:
                logger.debug(f"[PDFLoader] Not a PDF (content-type: {content_type})")
                raise LoaderNotApplicableError(
                    "PDFLoader",
                    url_or_file,
                    f"Not a PDF file (content-type: {content_type})"
                )

            try:
                result = read_pdf_content(io.BytesIO(resp.content))
                logger.debug(f"[PDFLoader] Successfully read remote PDF ({len(result)} chars)")
                return result
            except Exception as e:
                logger.warning(f"[PDFLoader] Failed to parse PDF: {e}")
                raise LoaderContentError(
                    "PDFLoader",
                    url_or_file,
                    f"Failed to parse PDF: {e}",
                    "The PDF may be corrupted or use unsupported features."
                ) from e


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
