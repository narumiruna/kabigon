import io
from pathlib import Path
from typing import IO
from typing import Any

import httpx
from pypdf import PdfReader

from .loader import Loader

DEFAULT_HEADERS = {
    "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8,en-US;q=0.7,en;q=0.6",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",  # noqa
}


class NotPDFError(Exception):
    def __init__(self, url: str) -> None:
        super().__init__(f"URL is not a PDF: {url}")


class PDFLoader(Loader):
    def load(self, url_or_file: str) -> str:
        if not url_or_file.startswith("http"):
            return read_pdf_content(url_or_file)

        resp = httpx.get(url_or_file, headers=DEFAULT_HEADERS, follow_redirects=True)
        resp.raise_for_status()

        if resp.headers.get("content-type") != "application/pdf":
            raise NotPDFError(url_or_file)

        return read_pdf_content(io.BytesIO(resp.content))

    async def async_load(self, url_or_file: str) -> str:
        if not url_or_file.startswith("http"):
            return read_pdf_content(url_or_file)

        async with httpx.AsyncClient() as client:
            resp = await client.get(url_or_file, headers=DEFAULT_HEADERS, follow_redirects=True)
            resp.raise_for_status()

            if resp.headers.get("content-type") != "application/pdf":
                raise NotPDFError(url_or_file)

            return read_pdf_content(io.BytesIO(resp.content))


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
