# Repository Guidelines

## Project Structure & Module Organization

- `src/kabigon/`: Python package (typed via `src/kabigon/py.typed`).
  - `src/kabigon/loaders/`: source-specific loaders (YouTube, Twitter/X, Reddit, GitHub, PDF, Playwright, etc.).
  - `src/kabigon/core/`: shared primitives (base `Loader`, exceptions, helpers).
  - `src/kabigon/cli.py`: Typer CLI entrypoint (`kabigon`).
- `tests/`: pytest suite (see `tests/loaders/` for loader-focused tests).
- `examples/`: runnable usage samples.

## Build, Test, and Development Commands

- Setup: `uv sync` (creates/updates `.venv` from `pyproject.toml`/`uv.lock`).
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run ty check .`
- Test (with coverage): `uv run pytest -v -s --cov=src tests`
- Run CLI locally: `uv run kabigon <url>`
- Build wheel: `uv build -f wheel`
- Publish: `uv publish`

## Coding Style & Naming Conventions

- Python 3.12+, `async`-first APIs; prefer small, composable loaders.
- Formatting/linting: Ruff, 120-char lines (`[tool.ruff]`), sorted imports via Ruff.
- Naming: modules in `snake_case.py`, classes in `PascalCase`, tests `test_*.py`.

## Testing Guidelines

- Framework: `pytest` + `pytest-cov`. Keep tests deterministic and avoid live network calls.
- Add/modify tests alongside loader changes under `tests/loaders/`.

## Commit & Pull Request Guidelines

- Commits typically use concise, imperative subjects (e.g., “Add GitHubLoader”, “Fix test …”).
- PRs: include a brief description, what URLs/cases were covered, and link issues where applicable; update `README.md`/`examples/` when adding user-facing behavior.

## Configuration & Secrets

- Do not commit credentials. Common env vars: `FIRECRAWL_API_KEY`, `FFMPEG_PATH`.
- For browser-based loaders, install Playwright once: `playwright install chromium`.
