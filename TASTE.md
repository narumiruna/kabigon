# TASTE

## Preference Signals

1. Prefer centralized URL matching in a single module (`src/kabigon/pipelines.py`) instead of splitting routing rules across many small modules.
2. Prefer plain data-table definitions for loader/pipeline wiring over `*Spec` dataclass abstractions when the behavior is straightforward.
3. Prefer implementation clarity in top-level flow (CLI and routing path) over extra indirection layers.
