## Goal

Remove the over-engineered or unused code found by the ponytail audit while preserving the documented public API (`kabigon.load_url*`, `available_loaders`, `explain_plan`), CLI behavior, and deterministic test suite.

## Context

This plan covers these cuts: Typer/Rich removal, internal barrel deletion, `check_*_url` wrapper deletion, one-field source target deletion, duplicate SVG deletion, single-entry CI matrix shrinkage, duplicate pre-commit hook deletion, unused `read_html_content` deletion, Docker `xvfb-run`/`xauth` deletion, and `_PipelineEntry` deletion.

## Architecture

Keep the current domain seams: Pipeline catalog owns Pipeline matching, Load chain owns execution plans, Loader registry owns factory wiring. These changes should delete indirection, not introduce new layers.

## Tech Stack

Remove `typer` and `rich` from runtime dependencies after replacing the single-command CLI with stdlib `argparse` and `print`.

## Assumptions

- Direct imports from `kabigon.core`, `kabigon.sources`, and `kabigon.pipelines` package barrels are not part of the documented public API.
- `kabigon.loaders.*` direct imports remain advanced escape hatches, but the `check_*_url` wrappers are not worth keeping when `parse_*_target` exists.

## Plan

- [ ] Capture a baseline before changes with `git status --short`, `uv run pytest -v -s tests/test_cli.py tests/sources/test_applicability.py tests/pipelines/test_catalog.py`, and `uv run ruff check .`; verify the starting point is known from command output.
- [ ] Replace the Typer CLI in `src/kabigon/cli.py` with stdlib `argparse` and `print` while keeping `kabigon <url>`, `kabigon --list`, `kabigon --loader <names> <url>`, and `--verbose`; verify with updated `tests/test_cli.py` and `uv run kabigon --list`.
- [ ] Remove `typer` and `rich` from `pyproject.toml`, refresh `uv.lock`, and update tests that imported `typer.testing`; verify with `rg -n "typer|rich" pyproject.toml uv.lock src tests` returning no runtime references except intentional historical text if any.
- [ ] Delete unused package barrels `src/kabigon/sources/__init__.py`, `src/kabigon/core/__init__.py`, and `src/kabigon/pipelines/__init__.py`; verify imports still target concrete modules with `rg -n "from kabigon\.(sources|core|pipelines) import|import kabigon\.(sources|core|pipelines)" src tests examples README.md docs`.
- [ ] Delete `check_*_url` wrappers from loader modules and update tests to call `parse_*_target` or `is_*_url`; verify with `rg -n "def check_.*_url|check_.*_url" src tests` returning no matches.
- [ ] Delete one-field target dataclasses in `src/kabigon/sources/applicability.py`, keeping only target objects whose extra fields are consumed (`YouTubeVideoTarget`, `GitHubTarget`, `TwitterTarget`); verify with `uv run pytest -v -s tests/sources/test_applicability.py tests/loaders/test_bbc.py tests/loaders/test_cnn.py tests/loaders/test_github.py tests/loaders/test_ltn.py tests/loaders/test_reddit.py tests/loaders/test_reel.py tests/loaders/test_truthsocial.py tests/loaders/test_twitter.py tests/loaders/test_youtube.py tests/loaders/test_youtube_ytdlp.py`.
- [ ] Delete unused `read_html_content` from `src/kabigon/loaders/utils.py`; verify with `rg -n "read_html_content" src tests examples README.md docs` returning no matches.
- [ ] Replace `_PipelineEntry` in `src/kabigon/pipelines/catalog.py` with a plain tuple table; verify with `uv run pytest -v -s tests/pipelines/test_catalog.py tests/test_load_chain.py tests/test_load_url.py`.
- [ ] Delete generated `docs/architecture/url-processing.svg` and update `README.md` to link to or render the Mermaid source instead; verify with `test ! -e docs/architecture/url-processing.svg` and `rg -n "url-processing\.svg" README.md docs` returning no matches.
- [ ] Inline the single Python version in `.github/workflows/ci.yml` and `.github/workflows/publish.yml`; verify with `rg -n "matrix:|python-version" .github/workflows/ci.yml .github/workflows/publish.yml` showing no one-item matrix.
- [ ] Delete the duplicate `tombi-format` hook from `.pre-commit-config.yaml`; verify with `grep -c "id: tombi-format" .pre-commit-config.yaml` returning `1`.
- [ ] Remove `xauth` installation and `xvfb-run` from `Dockerfile`, using `CMD ["kabigon"]`, and update README Docker text; verify with `rg -n "xvfb-run|xauth" Dockerfile README.md` returning no matches.
- [ ] Run format and full quality gates after all cuts: `uv run ruff format .`, `uv run ruff check .`, `uv run ty check .`, and `uv run pytest -v -s --cov=src tests`; verify every command exits 0.

## Risks

- Removing internal package barrels can break undocumented third-party imports; mitigate by keeping the documented top-level `kabigon` API unchanged.
- Replacing Typer changes help text formatting; mitigate by testing behavior and exit codes, not Typer-specific formatting.
- Deleting target dataclasses changes return values for parse functions that are only validators; mitigate by keeping parser names and exception behavior stable.

## Rollback / Recovery

- Revert individual cuts by path if a public compatibility issue appears: `src/kabigon/cli.py` + dependency files for CLI rollback, `src/kabigon/sources/applicability.py` for parser rollback, or deleted `__init__.py` files for barrel rollback.

## Completion Checklist

- [ ] CLI still supports auto-load, `--list`, `--loader`, and `--verbose`, verified by `uv run pytest -v -s tests/test_cli.py` and `uv run kabigon --list`.
- [ ] Runtime dependencies no longer include `typer` or `rich`, verified by `rg -n "typer|rich" pyproject.toml uv.lock src tests`.
- [ ] Deleted bloat stays deleted, verified by `test ! -e docs/architecture/url-processing.svg`, no `read_html_content`, no `check_*_url`, no duplicate `tombi-format`, and no `xvfb-run|xauth` matches.
- [ ] Source applicability and Pipeline matching remain correct, verified by `uv run pytest -v -s tests/sources/test_applicability.py tests/pipelines/test_catalog.py tests/test_load_chain.py tests/test_load_url.py`.
- [ ] Full project quality is verified by `uv run ruff check .`, `uv run ty check .`, and `uv run pytest -v -s --cov=src tests` exiting 0.
