# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kabigon is a URL content loader library that extracts content from various sources (YouTube, Instagram Reels, PDFs, web pages) and converts them to text/markdown format. It uses a chain-of-responsibility pattern where multiple loaders are tried in sequence until one succeeds.

## Development Commands

### Testing
```bash
# Run all tests with coverage
make test
# Or directly:
uv run pytest -v -s --cov=src tests

# Run a single test file
uv run pytest -v -s tests/test_youtube_ytdlp.py

# Run a specific test
uv run pytest -v -s tests/test_youtube_ytdlp.py::test_name
```

### Linting and Type Checking
```bash
# Run ruff linter
make lint
# Or: uv run ruff check .

# Run ty type checking
make type
# Or: uv run ty check .

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
make publish
# Or: uv build -f wheel && uv publish
```

### Version Management
- Uses bump-my-version for version bumps
- Configured to automatically run `uv lock --upgrade` and commit uv.lock on version bump
- Version is in pyproject.toml line 3

## Architecture

### Core Design Pattern: Async-First with Chain of Responsibility

The codebase implements a chain-of-responsibility pattern with async-first design:

1. **Base Interface**: `Loader` (src/kabigon/loader.py)
   - **Primary API**: `async def load(url: str) -> str` - All loaders implement this
   - **Convenience wrapper**: `def load_sync(url: str) -> str` - Wraps async with `asyncio.run()`
   - All loaders inherit from this base class

2. **Composite Pattern**: `Compose` (src/kabigon/compose.py)
   - Takes a list of loaders
   - Tries each loader in sequence until one succeeds (using `await loader.load(url)`)
   - Logs failures and continues to next loader
   - Raises exception only if all loaders fail
   - Supports both async (`await compose.load()`) and sync (`compose.load_sync()`) usage

3. **Concrete Loaders**: Each loader handles specific URL types
   - `YoutubeLoader`: YouTube transcripts via youtube-transcript-api
   - `YoutubeYtdlpLoader`: YouTube audio transcription via yt-dlp + OpenAI Whisper
   - `TwitterLoader`: Twitter/X posts (see src/kabigon/twitter.py)
   - `TruthSocialLoader`: Truth Social posts (see detailed notes below)
   - `RedditLoader`: Reddit posts and comments (see detailed notes below)
   - `ReelLoader`: Instagram Reels (combines YtdlpLoader + HttpxLoader)
   - `PttLoader`: PTT forum posts (Taiwan)
   - `PDFLoader`: PDF extraction from URLs or local files
   - `YtdlpLoader`: Audio transcription via yt-dlp + OpenAI Whisper
   - `PlaywrightLoader`: Browser-based web scraping (fallback for generic URLs)
   - `HttpxLoader`: Simple HTTP requests with markdown conversion
   - `FirecrawlLoader`: Firecrawl API integration

### Truth Social Loader Implementation

**Location**: `src/kabigon/truthsocial.py`

**Approach**: TruthSocialLoader handles Truth Social posts with specific strategies for JavaScript-heavy pages:

1. **Domain Validation**: Checks URL is from Truth Social domains before processing
   - Supported domains: `truthsocial.com`, `www.truthsocial.com`
   - Implemented via `check_truthsocial_url()` function
   - Raises `ValueError` if URL is not from Truth Social

2. **Playwright-Based Scraping**: Uses headless Chromium with extended timeout
   - Default timeout: 60 seconds (longer than other loaders due to heavy JS)
   - Wait strategy: `wait_until="networkidle"` to ensure full page load
   - Custom User Agent: Chrome 131 on Windows (truthsocial.py:10-12)
   - Truth Social heavily relies on JavaScript for content rendering

3. **Async Implementation**: Uses Playwright's async API
   - Primary implementation: `async def load()` using `playwright.async_api`
   - Sync wrapper available via `load_sync()` inherited from base `Loader` class
   - True async implementation (not using thread pools)

**CLI Integration**:
- ✅ Exported in `__init__.py` for programmatic use
- ✅ Included in CLI default loader chain (src/kabigon/cli.py:21)
- Positioned after TwitterLoader, before RedditLoader

**Usage Example** (see `examples/truthsocial.py`):
```python
import kabigon

url = "https://truthsocial.com/@realDonaldTrump/posts/123456"

# Direct usage
loader = kabigon.TruthSocialLoader()
content = loader.load_sync(url)

# With Compose
loader = kabigon.Compose([
    kabigon.TruthSocialLoader(),
    kabigon.PlaywrightLoader(),  # Fallback
])

# Async usage
import asyncio
content = asyncio.run(loader.load(url))
```

**Key Design Decisions**:
- Extended timeout (60s) to handle JavaScript-heavy content
- networkidle wait strategy ensures content is fully loaded
- Similar pattern to TwitterLoader and RedditLoader

**Test Coverage**: 86% (tests/test_truthsocial.py)

### Reddit Loader Implementation

**Location**: `src/kabigon/reddit.py`

**Approach**: The RedditLoader uses a specific strategy to avoid Reddit's CAPTCHA challenges:

1. **URL Conversion**: Automatically converts any Reddit URL to `old.reddit.com` format
   - Modern Reddit often shows CAPTCHAs for automated access
   - old.reddit.com is more scraper-friendly and has simpler HTML structure
   - Implemented via `convert_to_old_reddit()` function in reddit.py:31-41

2. **Playwright-Based Scraping**: Uses headless Chromium with custom user agent
   - User Agent: Chrome 131 on Windows (reddit.py:12-14)
   - Wait strategy: `wait_until="networkidle"` to ensure full page load
   - Configurable timeout (default: 30 seconds)

3. **Domain Validation**: Checks URL is from Reddit domains before processing
   - Supported domains: `reddit.com`, `www.reddit.com`, `old.reddit.com`
   - Implemented via `check_reddit_url()` function in reddit.py:17-28
   - Raises `ValueError` if URL is not from Reddit

4. **Async Implementation**: Uses Playwright's async API
   - Primary implementation: `async def load()` using `playwright.async_api`
   - Sync wrapper available via `load_sync()` inherited from base `Loader` class
   - True async implementation (not using thread pools)

**CLI Integration**:
- ✅ Exported in `__init__.py` for programmatic use
- ✅ **Included in CLI default loader chain** (src/kabigon/cli.py:20)
- Available for all kabigon CLI invocations

**Usage Example** (see `examples/read_reddit.py`):
```python
import kabigon

url = "https://reddit.com/r/confession/comments/..."

# Using CLI default chain (includes RedditLoader)
from kabigon.cli import run
run(url)

# Or manual composition with fallback
loader = kabigon.Compose([
    kabigon.RedditLoader(),
    kabigon.HttpxLoader(),       # Fallback if RedditLoader fails
    kabigon.PlaywrightLoader(),  # Final fallback
])

# Sync usage
content = loader.load_sync(url)

# Async usage
import asyncio
content = asyncio.run(loader.load(url))
```

**Integration Decision**:
- ✅ Now included in CLI default chain for better Reddit URL handling
- RedditLoader's old.reddit.com strategy avoids CAPTCHA effectively
- Positioned before generic PlaywrightLoader for optimized extraction

**Key Design Decisions**:
- old.reddit.com avoids CAPTCHA and simplifies HTML parsing
- Custom user agent mimics real browser to avoid detection
- Domain validation ensures loader only processes Reddit URLs
- Separate from default chain to keep CLI lightweight for general use

### Loader Strategy

Order matters in the CLI default composition (src/kabigon/cli.py:17-30):
1. Domain-specific loaders first (in order):
   - PttLoader (Taiwan PTT forum)
   - TwitterLoader (Twitter/X)
   - TruthSocialLoader (Truth Social)
   - RedditLoader (Reddit)
   - YoutubeLoader (YouTube transcripts)
   - ReelLoader (Instagram Reels)
   - YoutubeYtdlpLoader (YouTube audio transcription)
   - PDFLoader (PDF files)
2. Generic PlaywrightLoader last (catches all remaining URLs)
   - First attempt: timeout=50s, wait_until="networkidle" (thorough)
   - Second attempt: timeout=10s (faster fallback)

Each loader should:
- Implement `async def load(url: str) -> str` as the primary method
- Validate if it can handle the URL (raise exception if not)
- Return empty string if URL seems compatible but extraction fails
- Let exceptions bubble up to Compose for logging

### Async-First Design

**All loaders are async-first** with sync convenience wrappers:

- **`async def load(url: str) -> str`**: Primary implementation (all loaders must implement this)
- **`def load_sync(url: str) -> str`**: Convenience wrapper that calls `asyncio.run(self.load(url))`

**Benefits**:
- Natural support for parallel processing with `asyncio.gather()`
- Better performance for I/O-bound operations
- Playwright and httpx are async-native, no need for thread pools
- Backward compatible via `load_sync()` wrapper

**Usage patterns**:
```python
# Sync (simple scripts, CLI)
content = loader.load_sync(url)

# Async (single URL in async context)
content = await loader.load(url)

# Async (parallel batch processing)
results = await asyncio.gather(*[loader.load(url) for url in urls])
```

## Dependencies

### Core Runtime Dependencies
- `playwright`: Browser automation (requires `playwright install chromium`)
- `yt-dlp` + `openai-whisper`: Audio download and transcription
- `youtube-transcript-api`: YouTube transcript extraction
- `pypdf`: PDF text extraction
- `httpx`: HTTP client
- `markdownify`: HTML to Markdown conversion
- `firecrawl-py`: Firecrawl API client
- `typer` + `rich`: CLI interface
- `loguru`: Logging

### Dev Dependencies
- `pytest` + `pytest-cov`: Testing
- `ruff`: Linting and formatting
- `ty`: Type checking

### Environment Variables
- `LOGURU_LEVEL`: Set logging level (default: INFO)
- `FFMPEG_PATH`: Custom FFmpeg location for yt-dlp

## Code Conventions

### Ruff Configuration
- Line length: 120
- Force single-line imports (isort)
- Enabled rules: bugbear, comprehensions, pycodestyle, pyflakes, isort, pep8-naming, simplify, pyupgrade
- `__init__.py` ignores F401 (unused import) and F403 (star import)

### Type Hints
- Use modern Python 3.12+ syntax: `list[str]`, `dict[str, Any]`
- ty configured to ignore missing imports
- All type checks must pass (`make type` or `uv run ty check .`)

## Testing Notes

- Tests are minimal (only test_hello.py and test_youtube_ytdlp.py)
- pytest configured to ignore DeprecationWarnings
- Coverage reports generated with pytest-cov

## Installation for Development

```bash
# Clone and enter directory
git clone <repo-url>
cd kabigon

# Install with dev dependencies
uv sync

# Install playwright browsers
playwright install chromium
```

## Python API

### Simplest Usage

**Sync** (single line):
```python
import kabigon
text = kabigon.load_url_sync("https://example.com")
```

**Async** (for batch processing):
```python
import asyncio
import kabigon

# Single URL
text = await kabigon.load_url("https://example.com")

# Parallel batch processing
urls = ["url1", "url2", "url3"]
results = await asyncio.gather(*[kabigon.load_url(url) for url in urls])
```

These convenience functions use the same default loader chain as the CLI (see `_get_default_loader()` in `api.py`).

### Custom Loader Chain

For more control over which loaders to use:

**Sync**:
```python
loader = kabigon.Compose([
    kabigon.TwitterLoader(),
    kabigon.PlaywrightLoader(),
])
text = loader.load_sync(url)
```

**Async**:
```python
text = await loader.load(url)
```

## CLI Usage

```bash
# Basic usage
kabigon <url>

# Examples
kabigon https://www.youtube.com/watch?v=...
kabigon https://x.com/user/status/123456789
kabigon https://reddit.com/r/python/comments/xyz/...
kabigon https://www.instagram.com/reel/...
kabigon https://example.com/document.pdf
kabigon https://www.ptt.cc/bbs/Gossiping/...
```

**Supported URL Types**: The CLI automatically detects and uses the appropriate loader:
- Twitter/X → TwitterLoader (converts to x.com)
- Truth Social → TruthSocialLoader (60s timeout, networkidle)
- Reddit → RedditLoader (converts to old.reddit.com)
- YouTube → YoutubeLoader (transcript) or YoutubeYtdlpLoader (audio transcription)
- Instagram Reels → ReelLoader
- PDF files → PDFLoader
- PTT forum → PttLoader
- Generic URLs → PlaywrightLoader (browser-based scraping)
