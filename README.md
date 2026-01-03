# kabigon

A URL content loader library that extracts content from various sources (YouTube, Instagram Reels, Twitter/X, Reddit, PDFs, web pages) and converts them to text/markdown format.

## Installation

```shell
pip install kabigon
playwright install chromium
```

## Usage

### CLI

```shell
kabigon <url>

# Examples
kabigon https://www.youtube.com/watch?v=dQw4w9WgXcQ
kabigon https://x.com/elonmusk/status/123456789
kabigon https://reddit.com/r/python/comments/xyz/...
kabigon https://example.com/document.pdf
```

### Python API - Sync

```python
import kabigon

url = "https://www.google.com.tw"

# Simple usage
content = kabigon.PlaywrightLoader().load_sync(url)
print(content)

# With multiple loaders (tries each in order)
loader = kabigon.Compose([
    kabigon.TwitterLoader(),
    kabigon.YoutubeLoader(),
    kabigon.RedditLoader(),
    kabigon.PDFLoader(),
    kabigon.PlaywrightLoader(),  # Fallback for generic URLs
])
content = loader.load_sync(url)
print(content)
```

### Python API - Async

```python
import asyncio
import kabigon

async def main():
    url = "https://www.google.com.tw"

    # Single URL
    loader = kabigon.PlaywrightLoader()
    content = await loader.load(url)
    print(content)

    # Batch processing multiple URLs in parallel
    urls = [
        "https://x.com/user1/status/123",
        "https://youtube.com/watch?v=abc",
        "https://reddit.com/r/python/comments/xyz",
    ]

    loader = kabigon.Compose([
        kabigon.TwitterLoader(),
        kabigon.YoutubeLoader(),
        kabigon.RedditLoader(),
        kabigon.PlaywrightLoader(),
    ])

    # Parallel processing
    results = await asyncio.gather(*[loader.load(url) for url in urls])
    for url, content in zip(urls, results):
        print(f"{url}: {len(content)} chars")

asyncio.run(main())
```

## Supported Sources

| Source | Loader | Description |
|--------|--------|-------------|
| YouTube | `YoutubeLoader` | Extracts video transcripts |
| Twitter/X | `TwitterLoader` | Extracts tweet content |
| Reddit | `RedditLoader` | Extracts Reddit posts and comments |
| Instagram Reels | `ReelLoader` | Audio transcription + metadata |
| PDF | `PDFLoader` | Extracts text from PDF files (URL or local) |
| PTT | `PttLoader` | Taiwan PTT forum posts |
| Generic Web | `PlaywrightLoader` | Browser-based scraping for any website |
| Generic Web | `HttpxLoader` | Simple HTTP requests with markdown conversion |
