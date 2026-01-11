# kabigon

[![PyPI version](https://badge.fury.io/py/kabigon.svg)](https://badge.fury.io/py/kabigon)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/narumiruna/kabigon/branch/main/graph/badge.svg)](https://codecov.io/gh/narumiruna/kabigon)

A URL content loader library that extracts content from various sources (YouTube, Instagram Reels, Twitter/X, Reddit, Truth Social, GitHub files, PDFs, web pages) and converts them to text/markdown format.

## Features

✨ **Multi-Platform Support**: YouTube, Twitter/X, Truth Social, Reddit, Instagram Reels, PTT, GitHub files, PDFs, and generic web pages

🔄 **Async-First Design**: Built with async/await for efficient parallel processing

🎯 **Smart Fallback**: Automatically tries multiple extraction strategies until one succeeds

🚀 **Simple API**: Single-line usage with sensible defaults, or full control with custom loader chains

🔌 **Extensible**: Easy to add new loaders for additional platforms

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [CLI](#cli)
  - [Python API - Sync](#python-api---sync)
  - [Python API - Async](#python-api---async)
- [Supported Sources](#supported-sources)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

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
kabigon https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md
kabigon https://example.com/document.pdf
```

### Python API - Sync

```python
import kabigon

url = "https://www.google.com.tw"

# Simplest usage - automatically uses the best loader
content = kabigon.load_url_sync(url)
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
    content = await kabigon.load_url(url)
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
    results = await asyncio.gather(*[kabigon.load_url(url) for url in urls])
    for url, content in zip(urls, results):
        print(f"{url}: {len(content)} chars")

asyncio.run(main())
```

### API Comparison

| Usage | Simplest | Custom Loader Chain |
|-------|----------|---------------------|
| **Sync** | `kabigon.load_url_sync(url)` | `loader.load_sync(url)` |
| **Async** | `await kabigon.load_url(url)` | `await loader.load(url)` |
| **Batch Async** | `await asyncio.gather(*[kabigon.load_url(url) for url in urls])` | `await asyncio.gather(*[loader.load(url) for url in urls])` |

## Supported Sources

| Source | Loader | Description |
|--------|--------|-------------|
| YouTube | `YoutubeLoader` | Extracts video transcripts |
| YouTube | `YoutubeYtdlpLoader` | Audio transcription via yt-dlp + Whisper |
| Twitter/X | `TwitterLoader` | Extracts tweet content |
| Truth Social | `TruthSocialLoader` | Extracts Truth Social posts |
| Reddit | `RedditLoader` | Extracts Reddit posts and comments |
| Instagram Reels | `ReelLoader` | Audio transcription + metadata |
| GitHub | `GitHubLoader` | Fetches file content (supports `github.com/.../blob/...` URLs) |
| PDF | `PDFLoader` | Extracts text from PDF files (URL or local) |
| PTT | `PttLoader` | Taiwan PTT forum posts |
| Generic Web | `PlaywrightLoader` | Browser-based scraping for any website |
| Generic Web | `HttpxLoader` | Simple HTTP requests with markdown conversion |

## Examples

See the [`examples/`](examples/) directory for more usage examples:

- [`simple_usage.py`](examples/simple_usage.py) - Basic single-line usage
- [`async_usage.py`](examples/async_usage.py) - Async usage and parallel batch processing
- [`twitter.py`](examples/twitter.py) - Twitter/X post extraction
- [`truthsocial.py`](examples/truthsocial.py) - Truth Social post extraction
- [`read_reddit.py`](examples/read_reddit.py) - Reddit post and comments extraction
- [`ptt.py`](examples/ptt.py) - PTT forum post extraction
- [`fetch_billgertz_tweet.py`](examples/fetch_billgertz_tweet.py) - Real-world Twitter scraping example

## Troubleshooting

### Playwright browser not installed

**Error**: `Executable doesn't exist at /path/to/chromium`

**Solution**: Install Playwright browsers after installing kabigon:
```bash
playwright install chromium
```

### FFmpeg not found (for audio transcription)

**Error**: `ffmpeg not found`

**Solution**: Install FFmpeg for your platform:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

Or set custom FFmpeg path:
```bash
export FFMPEG_PATH=/path/to/ffmpeg
```

### Timeout errors

**Error**: `Timeout 30000ms exceeded`

**Solution**: Increase timeout for slow-loading pages:
```python
# Increase timeout to 60 seconds
loader = kabigon.PlaywrightLoader(timeout=60_000)
content = loader.load_sync(url)
```

### CAPTCHA or rate limiting

Some websites may show CAPTCHAs or block automated access. For Reddit, kabigon automatically uses `old.reddit.com` to avoid CAPTCHAs. For other sites, you may need to:

- Add delays between requests
- Use a custom user agent
- Implement retry logic with exponential backoff

### Logging and debugging

Enable debug logging to see what's happening:
```bash
export LOGURU_LEVEL=DEBUG
kabigon <url>
```

Or in Python:
```python
import os
os.environ["LOGURU_LEVEL"] = "DEBUG"
import kabigon
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/narumiruna/kabigon.git
cd kabigon

# Install dependencies with uv
uv sync

# Install Playwright browsers
playwright install chromium
```

### Testing

```bash
# Run all tests with coverage
uv run pytest -v -s --cov=src tests

# Run specific test file
uv run pytest -v -s tests/loaders/test_youtube.py
```

Current test coverage: **69%** (37 tests passing)

### Linting and Type Checking

```bash
# Run linter
uv run ruff check .

# Run type checker
uv run ty check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Building and Publishing

```bash
# Build wheel
uv build -f wheel

# Publish to PyPI
uv publish
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

When adding a new loader:
1. Create a new file in `src/kabigon/loaders/`
2. Inherit from the `Loader` base class
3. Implement `async def load(url: str) -> str`
4. Add domain validation
5. Add tests in `tests/loaders/`
6. Update documentation

See [`CLAUDE.md`](CLAUDE.md) for detailed development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.
