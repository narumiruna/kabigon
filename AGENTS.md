# Repository Guidelines

## Purpose

This document is the single source of truth for contributor and agent behavior in this repository.

## Project Overview

Kabigon is a URL content loader library that extracts content from multiple sources and converts results to text or markdown.

## Project Structure

- `src/kabigon/`: typed Python package (`src/kabigon/py.typed`)
- `src/kabigon/core/`: shared primitives (`Loader`, exceptions, helpers)
- `src/kabigon/loaders/`: source-specific loaders
- `src/kabigon/cli.py`: Typer CLI entrypoint (`kabigon`)
- `tests/`: pytest suite
- `tests/loaders/`: loader-focused tests
- `examples/`: runnable usage samples

## Build, Test, and Development Commands

- Setup: `uv sync`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run ty check .`
- Test (coverage): `uv run pytest -v -s --cov=src tests`
- Run one test file: `uv run pytest -v -s tests/loaders/test_youtube.py`
- Run one test case: `uv run pytest -v -s tests/loaders/test_youtube.py::test_name`
- Run CLI locally: `uv run kabigon <url>`
- Build wheel: `uv build -f wheel`
- Publish: `uv publish`

## Architecture

### Core Pattern

- The codebase is async-first.
- The loader system uses chain of responsibility via `Compose`.
- `Compose` tries loaders in order and stops at first success.

### Loader Contract

- All loaders MUST implement `async def load(url: str) -> str`.
- `load_sync(url: str) -> str` is the sync wrapper around async loading.
- A loader MUST raise if the URL is unsupported.
- A loader SHOULD return an empty string when URL is supported but extraction yields no content.
- Exceptions are handled by `Compose` for fallback behavior and logging.

### Default Loader Order

Defined in `src/kabigon/api.py`:

1. `PttLoader`
2. `TwitterLoader`
3. `TruthSocialLoader`
4. `RedditLoader`
5. `YoutubeLoader`
6. `ReelLoader`
7. `YoutubeYtdlpLoader`
8. `PDFLoader`
9. `PlaywrightLoader`

`PlaywrightLoader` is the final generic fallback.

## Coding Conventions

- Python version: 3.12+
- Prefer small, composable loaders.
- Naming:
  - modules: `snake_case.py`
  - classes: `PascalCase`
  - tests: `test_*.py`
- Type hints MUST use modern Python syntax (for example `list[str]`).

## Lint, Format, and Type Rules

- Ruff line length: 120
- Imports are sorted by Ruff/isort rules.
- All code changes MUST pass:
  - `uv run ruff check .`
  - `uv run ruff format .`
  - `uv run ty check .`

## Testing Rules

- Framework: `pytest` + `pytest-cov`
- Tests MUST be deterministic.
- Live network calls in tests MUST be avoided.
- Loader changes MUST include related updates in `tests/loaders/`.

## Pre-commit Requirement

If `.pre-commit-config.yaml` exists, all changes MUST pass:

- `prek run -a`

## Dependencies and Environment

### Runtime Dependencies

- `playwright`
- `yt-dlp`
- `openai-whisper`
- `youtube-transcript-api`
- `pypdf`
- `httpx`
- `markdownify`
- `firecrawl-py`
- `typer`
- `rich`

### Development Dependencies

- `pytest`
- `pytest-cov`
- `ruff`
- `ty`

### Environment Variables

- `FFMPEG_PATH`
- `FIRECRAWL_API_KEY`

## Security and Secrets

- Credentials MUST NOT be committed.
- Outputs from external systems MUST be treated as untrusted until verified.

## Commit and Pull Request Guidelines

- Commit subjects SHOULD be concise and imperative.
- PRs SHOULD include:
  - scope summary
  - covered URL/source cases
  - linked issues
- User-facing behavior changes MUST update `README.md` and/or `examples/`.

## Documentation Rules

- Documentation MUST be written in Markdown.
- Documentation MUST use clear, standard English.
- Each document MUST have one well-defined purpose.
- Rules MUST be enforceable and unambiguous.
- Foundational rules MUST NOT be duplicated across documents.
- Each documentation file MUST be under 600 lines.
- Language MUST be concise and precise.
- Design and structure MUST avoid unnecessary complexity.
- Scope and responsibility boundaries MUST be explicit.
