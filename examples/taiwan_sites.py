"""Batch-load a curated set of well-known Taiwanese websites.

Demonstrates how kabigon's default loader chain handles a variety of Taiwan-
focused content: news portals, forums, communities, and aggregators. Each URL
is fetched concurrently via ``kabigon.load_url`` and the result is summarised
(character count + first non-empty line as a sanity check).

Run:
    uv run python examples/taiwan_sites.py
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import kabigon

TAIWAN_SITES: list[tuple[str, str]] = [
    ("PTT 八卦版文章", "https://www.ptt.cc/bbs/Gossiping/M.1746078381.A.FFC.html"),
    ("中央社 CNA", "https://www.cna.com.tw/"),
    ("聯合新聞網 UDN", "https://udn.com/news/index"),
    ("自由時報", "https://www.ltn.com.tw/"),
    ("商業周刊", "https://www.businessweekly.com.tw/"),
    ("Yahoo 奇摩", "https://tw.yahoo.com/"),
    ("ETtoday", "https://www.ettoday.net/"),
    ("巴哈姆特", "https://www.gamer.com.tw/"),
]


@dataclass(frozen=True)
class FetchResult:
    name: str
    url: str
    ok: bool
    detail: str


async def _fetch(name: str, url: str) -> FetchResult:
    try:
        text = await kabigon.load_url(url)
    except Exception as exc:  # noqa: BLE001 - surface any loader error
        return FetchResult(name=name, url=url, ok=False, detail=f"{type(exc).__name__}: {exc}")

    preview = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if len(preview) > 60:
        preview = preview[:57] + "..."
    return FetchResult(name=name, url=url, ok=True, detail=f"{len(text):>6} chars | {preview}")


async def main() -> None:
    print(f"Loading {len(TAIWAN_SITES)} Taiwanese sites in parallel...\n")
    results = await asyncio.gather(*(_fetch(name, url) for name, url in TAIWAN_SITES))

    for r in results:
        marker = "✅" if r.ok else "❌"
        print(f"{marker} {r.name:<16} {r.detail}")

    ok_count = sum(1 for r in results if r.ok)
    print(f"\nSummary: {ok_count}/{len(results)} succeeded.")


if __name__ == "__main__":
    asyncio.run(main())
