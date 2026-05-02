# MEMORY

## GOTCHA

- Keep only one `pipelines` shape at a time; do not keep both `src/kabigon/pipelines.py` and `src/kabigon/pipelines/`.
- Keep CLI `--loader` composition coupled to CLI-local `LOADER_DEFS` (or inject registry explicitly) so test monkeypatching remains effective.
- Keep `openai_web` on `firecrawl` only with `NO_FALLBACK`; do not append default fallback loaders for that route.
- For local example runs, execute the user's exact command first and only add env overrides (for example `UV_CACHE_DIR`) after reproducing a concrete failure.
- Reddit RSS fallback can return 403 when using browser-like request headers; fetch RSS with default httpx headers.

## TASTE

- Prefer centralized URL matching in a single module instead of splitting routing rules across many small modules.
- Prefer plain data-table definitions for loader/pipeline wiring over `*Spec` abstractions when behavior is straightforward.
- Prefer top-level flow clarity (CLI and routing path) over extra indirection layers.
- Prefer an application-level Pipeline catalog to own Pipeline metadata; keep loader registry focused on loader factory wiring.
