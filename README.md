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
kabigon https://truthsocial.com/@realDonaldTrump/posts/123456
kabigon https://reddit.com/r/python/comments/xyz/...
kabigon https://example.com/document.pdf
```

### Python API - Sync

```python
import kabigon

url = "https://www.google.com.tw"

# Simplest usage - automatically uses the best loader
content = kabigon.load_url(url)
print(content)

# Or use specific loader
content = kabigon.PlaywrightLoader().load_sync(url)
print(content)

# With multiple loaders (tries each in order)
loader = kabigon.Compose([
    kabigon.TwitterLoader(),
    kabigon.TruthSocialLoader(),
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

    # Simplest usage - automatically uses the best loader
    content = await kabigon.load_url_async(url)
    print(content)

    # Or use specific loader
    loader = kabigon.PlaywrightLoader()
    content = await loader.load(url)
    print(content)

    # Batch processing multiple URLs in parallel
    urls = [
        "https://x.com/user1/status/123",
        "https://truthsocial.com/@user/posts/456",
        "https://youtube.com/watch?v=abc",
        "https://reddit.com/r/python/comments/xyz",
    ]

    loader = kabigon.Compose([
        kabigon.TwitterLoader(),
        kabigon.TruthSocialLoader(),
        kabigon.YoutubeLoader(),
        kabigon.RedditLoader(),
        kabigon.PlaywrightLoader(),
    ])

    # Parallel processing with automatic loader selection
    results = await asyncio.gather(*[kabigon.load_url_async(url) for url in urls])
    for url, content in zip(urls, results):
        print(f"{url}: {len(content)} chars")

asyncio.run(main())
```

### API Comparison

| Usage | Simplest | Custom Loader Chain |
|-------|----------|---------------------|
| **Sync** | `kabigon.load_url(url)` | `loader.load_sync(url)` |
| **Async** | `await kabigon.load_url_async(url)` | `await loader.load(url)` |
| **Batch Async** | `await asyncio.gather(*[kabigon.load_url_async(url) for url in urls])` | `await asyncio.gather(*[loader.load(url) for url in urls])` |

## Supported Sources

| Source | Loader | Description |
|--------|--------|-------------|
| YouTube | `YoutubeLoader` | Extracts video transcripts |
| YouTube | `YoutubeYtdlpLoader` | Audio transcription via yt-dlp + Whisper |
| Twitter/X | `TwitterLoader` | Extracts tweet content |
| Truth Social | `TruthSocialLoader` | Extracts Truth Social posts |
| Reddit | `RedditLoader` | Extracts Reddit posts and comments |
| Instagram Reels | `ReelLoader` | Audio transcription + metadata |
| PDF | `PDFLoader` | Extracts text from PDF files (URL or local) |
| PTT | `PttLoader` | Taiwan PTT forum posts |
| Generic Web | `PlaywrightLoader` | Browser-based scraping for any website |
| Generic Web | `HttpxLoader` | Simple HTTP requests with markdown conversion |
