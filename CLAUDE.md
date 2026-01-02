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

# Run mypy type checking
make type
# Or: uv run mypy --install-types --non-interactive .

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
   - `PttLoader`, `TwitterLoader`, `YoutubeYtdlpLoader`: Specialized loaders

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
- `mypy`: Type checking

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
- Use modern Python 3.10+ syntax: `list[str]`, `dict[str, Any]`
- mypy configured to ignore missing imports

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
