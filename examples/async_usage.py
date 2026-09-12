"""Async usage with reusable bounded resources and detailed results."""

import asyncio

import kabigon


async def main() -> None:
    urls = [
        "https://www.google.com",
        "https://www.wikipedia.org",
        "https://www.github.com",
    ]

    async with kabigon.KabigonClient(deadline=30, request_limit=8, browser_limit=2, worker_limit=2) as client:
        results = await asyncio.gather(*(client.load_url_detailed(url) for url in urls))

    for url, result in zip(urls, results, strict=True):
        print(f"{url}: {len(result.content)} chars via {result.loader_id} ({result.content_type})")
        for attempt in result.attempts:
            print(f"  {attempt.loader_id}: {attempt.status} in {attempt.elapsed_seconds:.3f}s")


if __name__ == "__main__":
    asyncio.run(main())
