# kabigon

A Python library and CLI tool that extracts content from URLs and returns plain text or markdown. Point it at a YouTube video, a tweet, a Reddit thread, a PDF, or any web page — kabigon selects the right loader automatically.

Intended for developers and data engineers who need reliable, source-aware text extraction without writing per-site scraping logic.

## Features

- Automatic loader selection for YouTube, Twitter/X, Truth Social, Reddit, Instagram Reels, PTT, GitHub, BBC, CNN, PDF, and generic web pages
- Fallback chain: if the primary loader fails, remaining loaders are tried in order without repeating already-attempted ones
- Async-first (`async`/`await`) with a synchronous wrapper for scripts and notebooks
- Single-line Python API: `kabigon.load_url_sync(url)`
- CLI for ad-hoc extraction and debugging
- Extensible: add a loader by subclassing `Loader` and implementing one method

## Requirements

- Python 3.12+
- [Playwright](https://playwright.dev/python/) Chromium browser (for generic web scraping)
- FFmpeg (only for audio/video transcription loaders)
- `FIRECRAWL_API_KEY` environment variable (only for the Firecrawl loader)

## Installation

```bash
# Install as a CLI tool
uv tool install kabigon

# Or run directly without installing
uvx kabigon <url>
```

After installation, install the Chromium browser for Playwright:

```bash
playwright install chromium
```

## Quick Start

```python
import kabigon

text = kabigon.load_url_sync("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(text)
```

## Usage

### CLI

```bash
# Auto-select the best loader
kabigon https://www.youtube.com/watch?v=dQw4w9WgXcQ
kabigon https://x.com/user/status/123456789
kabigon https://reddit.com/r/python/comments/xyz/
kabigon https://github.com/user/repo/blob/main/README.md
kabigon https://example.com/document.pdf
```

### Python — sync

```python
import kabigon

text = kabigon.load_url_sync("https://www.google.com")
print(text)
```

### Python — async

```python
import asyncio
import kabigon

async def main() -> None:
    text = await kabigon.load_url("https://www.google.com")
    print(text)

asyncio.run(main())
```

### Parallel batch loading

```python
import asyncio
import kabigon

async def main() -> None:
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

## API Reference

All public functions are importable from the `kabigon` package.

| Function | Signature | Description |
|----------|-----------|-------------|
| `load_url_sync` | `(url: str) -> str` | Load a URL synchronously using automatic loader selection |
| `load_url` | `async (url: str) -> str` | Load a URL asynchronously using automatic loader selection |
| `available_loaders` | `() -> list[str]` | Return names of all registered loaders |
| `explain_plan` | `(url: str) -> dict[str, object]` | Return the planned loader chain for a URL without executing it |

```python
import kabigon

# Inspect which loaders would be used for a URL
plan = kabigon.explain_plan("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(plan)

# List all loader names
print(kabigon.available_loaders())
```

## Commands

### `kabigon <url>`

Load content from a URL. Automatically selects the best loader.

```bash
kabigon https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### `kabigon --list`

Print all available loaders and their descriptions.

```bash
kabigon --list
```

### `kabigon --loader <names> <url>`

Override automatic loader selection with a comma-separated list of loader names, tried in order.

```bash
kabigon --loader twitter,playwright https://x.com/user/status/123
```

Use this only for debugging or testing specific loaders. The automatic path is preferred for normal use.

## Configuration

### Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `FIRECRAWL_API_KEY` | For `firecrawl` loader | API key for the [Firecrawl](https://firecrawl.dev) web extraction service |
| `FFMPEG_PATH` | Optional | Custom path to the FFmpeg binary used by Whisper / yt-dlp |

### Docker

A `Dockerfile` is provided. The image includes Playwright with Chromium and runs `xvfb-run` for headless rendering.

```bash
docker build -t kabigon .
docker run --rm kabigon kabigon https://example.com
```

## Project Structure

```
src/kabigon/
├── core/          # Loader ABC, exceptions, and shared helpers
├── loaders/       # Concrete loader implementations (one file per source)
├── pipelines/     # Pipeline catalog: maps URL patterns to loader chains
├── api.py         # Public Python interface (load_url, explain_plan, …)
├── cli.py         # Typer CLI entrypoint
└── load_chain.py  # Chain execution and fallback logic
tests/
├── loaders/       # Per-loader unit tests
examples/          # Runnable usage samples
```

URL-to-pipeline matching lives in `kabigon.pipelines`; loader ordering and fallback policy live in `kabigon.load_chain`.

## Development

```bash
git clone https://github.com/narumiruna/kabigon.git
cd kabigon
uv sync
playwright install chromium
```

Lint, format, and type-check:

```bash
uv run ruff check .        # lint
uv run ruff format .       # format
uv run ty check .          # type check
uv run ruff check --fix .  # auto-fix lint issues
```

## Testing

```bash
# Full suite with coverage
uv run pytest -v -s --cov=src tests

# Single loader file
uv run pytest -v -s tests/loaders/test_youtube.py

# Single test
uv run pytest -v -s tests/loaders/test_youtube.py::test_name
```

Tests must be deterministic and must not rely on live network calls.

## Troubleshooting

### Playwright browser not installed

```
Executable doesn't exist at /path/to/chromium
```

```bash
playwright install chromium
```

### FFmpeg not found

```
ffmpeg not found
```

Install FFmpeg or point to a custom binary:

```bash
# Ubuntu / Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Custom binary
export FFMPEG_PATH=/path/to/ffmpeg
```

### Playwright timeout

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

Some sites block automated access. kabigon automatically redirects Reddit requests to `old.reddit.com` to avoid CAPTCHAs. For other sites, add delays between requests or implement retry logic in your calling code.

## Contributing

To add a new loader:

1. Create `src/kabigon/loaders/<source>.py` and subclass `Loader`.
2. Implement `async def load(self, url: str) -> str`.
3. Export the class from `src/kabigon/loaders/__init__.py`.
4. Register the loader in `src/kabigon/loader_registry.py`.
5. If the loader handles a specific source, add a pipeline entry in `src/kabigon/pipelines/catalog.py`.
6. Update load-chain and planning consistency tests if the execution plan changes.
7. Add loader tests in `tests/loaders/`.

## License

[MIT](LICENSE)
