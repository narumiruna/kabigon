# kabigon

[![PyPI version](https://badge.fury.io/py/kabigon.svg)](https://badge.fury.io/py/kabigon)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/narumiruna/kabigon/branch/main/graph/badge.svg)](https://codecov.io/gh/narumiruna/kabigon)

A Python library that extracts content from URLs and converts the result to text or markdown. Feed it a YouTube video, a tweet, a Reddit thread, a PDF, or any web page — kabigon picks the right loader automatically.

## Features

- **Smart routing** — recognises YouTube, Twitter/X, Truth Social, Reddit, Instagram Reels, PTT, GitHub, BBC, CNN, PDFs, and generic web pages, then selects the best extraction pipeline
- **Automatic fallback** — if the primary loader fails, remaining loaders are tried in order without repeating work
- **Async-first** — built on `async`/`await`; a synchronous wrapper is provided for convenience
- **Single-line API** — `kabigon.load_url_sync(url)` is all you need to get started
- **Extensible** — add a new loader by subclassing `Loader` and implementing one method

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI](#cli)
- [Python API](#python-api)
- [Supported Sources](#supported-sources)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

## Installation

```bash
# Install as a CLI tool
uv tool install kabigon

# Or run directly without installing
uvx kabigon <url>
```

After installation, install a browser for Playwright (required for generic web scraping):

```bash
playwright install chromium
```

## Quick Start

```python
import kabigon

# One line to load any URL
text = kabigon.load_url_sync("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(text)
```

## CLI

```bash
# Load content from a URL (auto-selects the best loader)
kabigon https://www.youtube.com/watch?v=dQw4w9WgXcQ

# List all available loaders
kabigon --list

# Advanced: bypass automatic planning with a specific loader or loader chain
kabigon --loader youtube https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

By default, kabigon routes the URL to a source-specific pipeline first, then falls back to the remaining default loaders without repeating already-attempted ones. Prefer this automatic path unless you are debugging or intentionally bypassing pipeline planning.

More examples:

```bash
kabigon https://x.com/elonmusk/status/123456789
kabigon https://truthsocial.com/@realDonaldTrump/posts/123456
kabigon https://reddit.com/r/python/comments/xyz/...
kabigon https://github.com/user/repo/blob/main/README.md
kabigon https://example.com/document.pdf
```

## Python API

### Sync

```python
import kabigon

# Automatic loader selection
text = kabigon.load_url_sync("https://www.google.com")
print(text)
```

### Async

```python
import asyncio
import kabigon

async def main() -> None:
    text = await kabigon.load_url("https://www.google.com")
    print(text)

    # Parallel batch loading
    urls = [
        "https://x.com/user/status/123",
        "https://youtube.com/watch?v=abc",
        "https://reddit.com/r/python/comments/xyz",
    ]
    results = await asyncio.gather(*[kabigon.load_url(url) for url in urls])
    for url, content in zip(urls, results, strict=True):
        print(f"{url}: {len(content)} chars")

asyncio.run(main())
```

### Advanced Loader Selection

Most callers should use `kabigon.load_url()` or `kabigon.load_url_sync()` so pipeline planning, targeted loaders, and fallback policy stay in one place. For debugging or advanced experiments, the CLI can run an explicit loader order:

```shell
kabigon --loader twitter,playwright https://x.com/user/status/123
```

### Utility Functions

```python
import kabigon

# Show which loaders kabigon would use for a URL
plan = kabigon.explain_plan("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(plan)

# List all registered loader names
loaders = kabigon.available_loaders()
print(loaders)
```

### API Summary

| Style | Recommended interface | Advanced loader order |
|-------|-----------------------|-----------------------|
| **Sync** | `kabigon.load_url_sync(url)` | `kabigon --loader name,name URL` |
| **Async** | `await kabigon.load_url(url)` | Use individual Loader adapters directly |
| **Batch** | `await asyncio.gather(*[kabigon.load_url(u) for u in urls])` | Use individual Loader adapters directly |

## Supported Sources

| Source | Loader | Notes |
|--------|--------|-------|
| YouTube | `YoutubeLoader` | Transcript extraction via `youtube-transcript-api` |
| YouTube | `YoutubeYtdlpLoader` | Audio download + Whisper transcription |
| Twitter / X | `TwitterLoader` | Supports `x.com`, `fxtwitter.com`, `vxtwitter.com`, and others |
| Truth Social | `TruthSocialLoader` | Post content extraction |
| Reddit | `RedditLoader` | Posts and comments; auto-redirects to `old.reddit.com` |
| Instagram Reels | `ReelLoader` | Audio transcription via yt-dlp + Whisper |
| GitHub | `GitHubLoader` | File content from `github.com/.../blob/...` and `raw.githubusercontent.com` |
| BBC | `BBCLoader` | Article-aware HTML parsing |
| CNN | `CNNLoader` | Article-aware HTML parsing |
| PDF | `PDFLoader` | Text extraction from remote or local PDF files |
| PTT | `PttLoader` | Taiwan PTT (BBS) forum posts |
| Generic web | `PlaywrightLoader` | Full browser rendering via Playwright |
| Generic web | `HttpxLoader` | Lightweight HTTP fetch + HTML-to-markdown |
| Generic web | `FirecrawlLoader` | Web extraction via the [Firecrawl](https://firecrawl.dev) API |
| Audio / Video | `YtdlpLoader` | Generic audio transcription via yt-dlp + Whisper |

## Architecture

kabigon follows a layered architecture:

```
Interface (CLI)  →  Application (pipeline catalog, load chain)  →  Domain (Loader ABC, errors)
                                                                 ↓
                                                           Loaders (concrete implementations)
```

**Request flow:**

1. The URL enters via the CLI or `load_url()`.
2. `pipeline_catalog.py` matches known sources (YouTube, Twitter, …) and returns the matched pipeline metadata.
3. `load_chain.py` turns that into a runnable load chain: targeted loaders followed by fallback loaders, plus explanation metadata.
4. `load_chain.py` executes the ordered Loader attempts and returns the first successful result.

`explain_plan()` returns Pipeline, requirement, and execution-plan metadata without constructing concrete loaders. Actual loading builds and executes the runnable Load chain.

There are three fallback levels to keep distinct:

- **Fallback loaders** are added to the Execution plan after Targeted loaders when policy allows it.
- The Load chain executes that ordered Loader list and records why each Loader failed.
- A Loader may also have Loader-internal fallback, such as trying multiple source-specific fetch strategies inside one Loader.

To add a new loader, create a file in `src/kabigon/loaders/`, subclass `Loader`, implement `async def load(self, url: str) -> str`, register it in `infrastructure/registry.py`, and add a pipeline entry in `application/pipeline_catalog.py` if the loader handles a specific source.

## Configuration

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `FFMPEG_PATH` | Custom path to the FFmpeg binary (used by Whisper / yt-dlp audio transcription) |
| `FIRECRAWL_API_KEY` | API key for the [Firecrawl](https://firecrawl.dev) loader |

### Docker

A `Dockerfile` is provided for containerised usage:

```bash
docker build -t kabigon .

# "kabigon" after the image name is the CLI command
docker run --rm kabigon kabigon https://example.com
```

The image includes Playwright with Chromium and uses `xvfb-run` for headless browser rendering.

## Troubleshooting

### Playwright browser not installed

```
Executable doesn't exist at /path/to/chromium
```

Install the browser after installing kabigon:

```bash
playwright install chromium
```

### FFmpeg not found

```
ffmpeg not found
```

Install FFmpeg:

```bash
# Ubuntu / Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

Or point to a custom binary:

```bash
export FFMPEG_PATH=/path/to/ffmpeg
```

### Timeout errors

```
Timeout 30000ms exceeded
```

Increase the timeout for slow-loading pages:

```python
from kabigon.loaders import PlaywrightLoader

loader = PlaywrightLoader(timeout=60_000)
text = loader.load_sync(url)
```

### CAPTCHA / rate limiting

Some websites block automated access. kabigon automatically uses `old.reddit.com` for Reddit to avoid CAPTCHAs. For other sites, consider adding delays between requests or implementing retry logic.

## Development

### Setup

```bash
git clone https://github.com/narumiruna/kabigon.git
cd kabigon
uv sync
playwright install chromium
```

### Testing

```bash
# Full suite with coverage
uv run pytest -v -s --cov=src tests

# Single file
uv run pytest -v -s tests/loaders/test_youtube.py

# Single test
uv run pytest -v -s tests/loaders/test_youtube.py::test_name
```

### Linting and Type Checking

```bash
uv run ruff check .       # lint
uv run ruff format .      # format
uv run ty check .         # type check
uv run ruff check --fix . # auto-fix lint issues
```

### Building and Publishing

```bash
uv build -f wheel
uv publish
```

### Adding a New Loader

1. Create `src/kabigon/loaders/<source>.py` and subclass `Loader`.
2. Implement `async def load(self, url: str) -> str`.
3. Export the class from `src/kabigon/loaders/__init__.py`.
4. Register the loader in `src/kabigon/infrastructure/registry.py`.
5. Add a Pipeline catalog entry in `src/kabigon/application/pipeline_catalog.py` if the loader handles a specific source.
6. Add or update Load chain and registry consistency tests when the Execution plan should change.
7. Add Loader tests in `tests/loaders/`.

## License

[MIT](LICENSE)
