"""Async usage example with batch processing"""

import asyncio

import kabigon


async def main() -> None:
    # Single URL - async version
    url = "https://www.google.com"
    text = await kabigon.load_url(url)
    print(f"Loaded {len(text)} characters from {url}\n")

    # Batch processing multiple URLs in parallel
    urls = [
        "https://www.google.com",
        "https://www.wikipedia.org",
        "https://www.github.com",
    ]

    print(f"Loading {len(urls)} URLs in parallel...")
    results = await asyncio.gather(*[kabigon.load_url(url) for url in urls])

    for url, content in zip(urls, results, strict=True):
        print(f"{url}: {len(content)} chars")


if __name__ == "__main__":
    asyncio.run(main())
