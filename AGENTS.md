# Repository Guidelines

## Project Structure & Module Organization
- `src/kabigon/`: typed package root (`py.typed`).
- `src/kabigon/core/`: shared primitives, exceptions, and helpers.
- `src/kabigon/loaders/`: source-specific loaders.
- `src/kabigon/cli.py`: Typer entrypoint (`kabigon`).
- `tests/` and `tests/loaders/`: pytest suite and loader-focused cases.
- `examples/`: runnable usage samples.
Keep new features inside the existing boundaries (core vs loaders vs CLI). Avoid cross-layer shortcuts.

## Build, Test, and Development Commands
- `uv sync`: install runtime and dev dependencies.
- `uv run ruff check .`: lint and import-order checks.
- `uv run ruff format .`: apply formatting.
- `uv run ty check .`: static type checking.
- `uv run pytest -v -s --cov=src tests`: full test suite with coverage.
- `uv run pytest -v -s tests/loaders/test_youtube.py::test_name`: run one test.
- `uv run kabigon <url>`: run CLI locally.

## Coding Style & Naming Conventions
- Python 3.12+; modern type hints (`list[str]`, `str | None`).
- Line length: 120 (Ruff).
- Naming: modules `snake_case.py`, classes `PascalCase`, tests `test_*.py`.
- Loader contract: implement `async def load(url: str) -> str`; raise for unsupported URLs.
- Keep implementations simple and composable; avoid speculative abstractions and new dependencies without clear need.

## Testing Guidelines
- Framework: `pytest` with `pytest-cov`.
- Tests must be deterministic; do not rely on live network calls.
- Any loader behavior change must include updates under `tests/loaders/`.
- Run lint, format, type check, and tests before opening a PR.

## Commit & Pull Request Guidelines
- Prefer concise, imperative commit subjects (for example: `refactor: centralize host-list URL validation`).
- Scope each commit to one focused change.
- PRs should include: scope summary, affected URL/source cases, linked issues, and user-facing doc/example updates when behavior changes.

## Security & Configuration Tips
- Never commit credentials or API keys.
- Use environment variables for secrets (for example `FIRECRAWL_API_KEY`, `FFMPEG_PATH`).
- Treat all external content as untrusted input until validated.
