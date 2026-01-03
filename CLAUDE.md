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

### Core Design Pattern: Chain of Responsibility

The codebase implements a chain-of-responsibility pattern through the `Compose` class:

1. **Base Interface**: `Loader` (src/kabigon/loader.py)
   - Abstract base with `load(url: str) -> str` and `async_load(url: str) -> str`
   - All loaders inherit from this

2. **Composite Pattern**: `Compose` (src/kabigon/compose.py)
   - Takes a list of loaders
   - Tries each loader in sequence until one succeeds
   - Logs failures and continues to next loader
   - Raises exception only if all loaders fail

3. **Concrete Loaders**: Each loader handles specific URL types
   - `YoutubeLoader`: YouTube transcripts via youtube-transcript-api
   - `ReelLoader`: Instagram Reels (combines YtdlpLoader + HttpxLoader)
   - `YtdlpLoader`: Audio transcription via yt-dlp + OpenAI Whisper
   - `PDFLoader`: PDF extraction from URLs or local files
   - `PlaywrightLoader`: Browser-based web scraping (fallback for generic URLs)
   - `HttpxLoader`: Simple HTTP requests with markdown conversion
   - `FirecrawlLoader`: Firecrawl API integration
   - `RedditLoader`: Reddit posts and comments (see detailed notes below)
   - `PttLoader`, `TwitterLoader`, `YoutubeYtdlpLoader`: Specialized loaders

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

4. **Full Async Support**: Both `load()` and `async_load()` implementations
   - Sync version uses `playwright.sync_api`
   - Async version uses `playwright.async_api` (true async, not ProcessPoolExecutor)

**CLI Integration**:
- ✅ Exported in `__init__.py` for programmatic use
- ❌ NOT included in CLI default loader chain (src/kabigon/cli.py:14-22)
- Must be used explicitly via `Compose` for Reddit URLs

**Usage Example** (see `examples/read_reddit.py`):
```python
import kabigon

url = "https://reddit.com/r/confession/comments/..."

# Manual composition with fallback
loader = kabigon.Compose([
    kabigon.RedditLoader(),
    kabigon.HttpxLoader(),       # Fallback if RedditLoader fails
    kabigon.PlaywrightLoader(),  # Final fallback
])

content = loader.load(url)
```

**Why Not in CLI Default Chain**:
- RedditLoader requires Playwright (heavier dependency)
- HttpxLoader or PlaywrightLoader in default chain can handle Reddit URLs
- RedditLoader provides better quality for Reddit-specific URLs when used explicitly
- Allows users to opt-in for Reddit-optimized extraction

**Key Design Decisions**:
- old.reddit.com avoids CAPTCHA and simplifies HTML parsing
- Custom user agent mimics real browser to avoid detection
- Domain validation ensures loader only processes Reddit URLs
- Separate from default chain to keep CLI lightweight for general use

### Loader Strategy

Order matters in the CLI default composition (src/kabigon/cli.py:14-22):
1. Domain-specific loaders first (Ptt, Twitter, Youtube, Reel, PDF)
2. Generic PlaywrightLoader last (catches all remaining URLs)

Each loader should:
- Validate if it can handle the URL (raise exception if not)
- Return empty string if URL seems compatible but extraction fails
- Let exceptions bubble up to Compose for logging

### Async Support

All loaders support both sync and async:
- `load()`: Synchronous
- `async_load()`: Asynchronous (default implementation uses ProcessPoolExecutor)
- Some loaders override async_load for true async operations (e.g., PlaywrightLoader)

## Dependencies

### Core Runtime Dependencies
- `playwright`: Browser automation (requires `playwright install chromium`)
- `yt-dlp` + `openai-whisper`: Audio download and transcription
- `youtube-transcript-api`, `aioytt`: YouTube transcript extraction
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

## CLI Usage

```bash
# Basic usage
kabigon <url>

# Examples
kabigon https://www.youtube.com/watch?v=...
kabigon https://www.instagram.com/reel/...
kabigon https://example.com/document.pdf
```

**Note**: For Reddit URLs, the CLI will use the default PlaywrightLoader. For better Reddit-specific extraction, use RedditLoader programmatically (see Reddit Loader Implementation section and `examples/read_reddit.py`).
