# kabigon

[![PyPI version](https://badge.fury.io/py/kabigon.svg)](https://badge.fury.io/py/kabigon)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/narumiruna/kabigon/branch/main/graph/badge.svg)](https://codecov.io/gh/narumiruna/kabigon)

A Python library and CLI tool that extracts content from URLs and returns plain text or markdown. Point it at a YouTube video, a tweet, a Reddit thread, a PDF, or any web page — kabigon selects the right loader automatically.

Intended for developers and data engineers who need reliable, source-aware text extraction without writing per-site scraping logic.

## Features

- Automatic loader selection for YouTube, Twitter/X, Truth Social, Reddit, Instagram Reels, PTT, GitHub, pi.dev shared sessions, BBC, CNN, PDF, and generic web pages
- Source-safe fallback chains: strict targets retry only strategies that preserve the requested content semantics
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

This release retains the full dependency set in the default installation for compatibility; browser, Firecrawl, and transcription dependencies have not moved to extras. After installation, install the Chromium browser for Playwright:

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
kabigon 'https://pi.dev/session/#0230effc86f4a142c885cb59fe9725d5'
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

### Reusable client, deadlines, and batch loading

`KabigonClient` owns reusable HTTP sessions, a browser process, and bounded blocking workers. Use one client from one event loop and close it with `async with`. `deadline` is a total budget in seconds for each load; it is unset by default for compatibility. Positive `request_limit`, `browser_limit`, and `worker_limit` values bound admitted work, and time spent waiting for a slot counts toward the deadline.

After a deadline expires, kabigon starts no new loader attempts and propagates cancellation to async operations. Python cannot forcibly stop arbitrary work already running in a thread, so client shutdown may wait for admitted transcription or parsing work to drain. One-shot `load_url()` and `load_url_sync()` create and close a short-lived client under the same contract; neither promises hard wall-clock termination of a running thread.

```python
import asyncio
import kabigon


async def main() -> None:
    urls = [
        "https://x.com/user/status/123",
        "https://youtube.com/watch?v=abc",
        "https://reddit.com/r/python/comments/xyz",
    ]
    async with kabigon.KabigonClient(deadline=30, request_limit=8, browser_limit=2, worker_limit=2) as client:
        results = await asyncio.gather(*(client.load_url(url) for url in urls))
    for url, content in zip(urls, results, strict=True):
        print(f"{url}: {len(content)} chars")


asyncio.run(main())
```

## API Reference

All public functions are importable from the `kabigon` package.

| Function | Signature | Description |
|----------|-----------|-------------|
| `load_url_sync` | `(url: str, *, deadline: float \| None = None) -> str` | Load once synchronously and close its short-lived client |
| `load_url` | `async (url: str, *, deadline: float \| None = None) -> str` | Load once asynchronously and close its short-lived client |
| `load_url_detailed` | `async (url: str, *, deadline: float \| None = None) -> LoadResult` | Return content plus actual loader/category and ordered attempts |
| `KabigonClient` | `(*, deadline=None, request_limit=8, browser_limit=2, worker_limit=2)` | Reuse bounded resources inside one event loop |
| `available_loaders` | `() -> list[str]` | Return names of all registered loaders without importing implementations |
| `explain_plan` | `(url: str) -> dict[str, object]` | Return the planned loader chain and missing environment variables without executing it |

```python
import asyncio

import kabigon

# Inspect which loaders would be used for a URL
plan = kabigon.explain_plan("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(plan)

# List all loader names
print(kabigon.available_loaders())

# Inspect actual execution, including skipped requirements and transport fallback
result = asyncio.run(kabigon.load_url_detailed("https://example.com"))
print(result.content, result.loader_id, result.content_type)
print(result.to_dict()["attempts"])
```

## Extraction behavior

- Missing environment requirements are checked per alternative. An unavailable loader is recorded as skipped while available alternatives continue; if no planned alternative is eligible, resolution fails before constructing an SDK client.
- Generic HTML loaders accept non-empty pages, including content shorter than 300 characters. Empty pages and recognized challenge headings are rejected; challenge heuristics are not applied to source transcripts, code, or PDF text.
- HTTP 4xx and 5xx responses fail extraction, including browser-based retrieval, so the load chain can try its next loader.
- GitHub and news article extraction preserves escaped text such as literal HTML examples and excludes ignored subtrees without capturing surrounding page content.
- BBC, CNN, and LTN retries use HTTPX, curl_cffi, then a browser, but every transport feeds the same article extractor. Generic page markdown is never accepted as a news article.
- Twitter/X status URLs require the requested post; profiles use the generic HTML plan. A missing tweet does not fall through to unrelated page text.
- YouTube video URLs require transcript output and never fall through to generic HTML. Playlist pages without a selected video use the generic plan; a video URL containing a playlist ID still transcribes only that video.
- PDF, pi.dev session, social-post, and GitHub source plans reject generic fallback output. GitHub blob URLs take precedence over the PDF suffix rule.
- Explicit `--loader` selection remains a debugging escape hatch. Its output is categorized by the loader actually used, but explicit generic extraction is not source verification.

## Architecture

The automatic path uses `kabigon.pipelines` to select a source-aware pipeline and content contract, then `kabigon.load_chain` executes one ordered plan. Requirements are evaluated per attempt, implementations are imported and constructed only when attempted, whitespace-only or contract-incompatible results are rejected, and `LoaderError.details` remains the readable all-failed representation. `LoadResult` is produced by this same runtime rather than a second execution engine.

`KabigonClient` owns reusable sessions, one lazily launched browser with isolated contexts, and bounded workers. Standalone Loader construction remains supported and owns its local cleanup.

Architecture diagram source: [`docs/architecture/url-processing.mmd`](docs/architecture/url-processing.mmd)

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

Use this only for debugging or testing specific loaders. The automatic path is preferred for normal use. Registry metadata exposes `pi-session`, `ltn`, and `curl-cffi`; internal `playwright-fast` and `playwright-networkidle` variants are intentionally hidden from CLI selection and listing.

## Configuration

### Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `FIRECRAWL_API_KEY` | For `firecrawl` loader | API key for the [Firecrawl](https://firecrawl.dev) web extraction service |
| `FFMPEG_PATH` | Optional | FFmpeg executable or containing directory used for yt-dlp post-processing and Whisper audio decoding |

### Docker

A `Dockerfile` is provided. The default image includes Playwright with headless Chromium. Build with Xvfb only when you need Chromium `headless=False`.

```bash
docker build -t kabigon .
docker run --rm kabigon https://example.com

# Optional: support Chromium headless=False
docker build --build-arg KABIGON_WITH_XVFB=1 -t kabigon:xvfb .
```

## Project Structure

```
src/kabigon/
├── core/          # Loader ABC, exceptions, and shared helpers
├── loaders/       # Concrete loader implementations (one file per source)
├── pipelines/     # Pipeline catalog: maps URL patterns to loader chains
├── api.py         # One-shot Python interface (load_url, load_url_detailed, …)
├── client.py      # Reusable resource ownership, limits, and deadlines
├── cli.py         # argparse CLI entrypoint
└── load_chain.py  # Chain execution, acceptance, and attempt records
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

`FFMPEG_PATH` applies to both audio download post-processing and decoding for transcription. The configured binary does not need to be on `PATH`; when the variable is unset, kabigon uses `ffmpeg` from `PATH`.

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
