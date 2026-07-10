# MEMORY

## GOTCHA

- Keep only one `pipelines` shape at a time; do not keep both `src/kabigon/pipelines.py` and `src/kabigon/pipelines/`.
- Keep CLI `--loader` composition coupled to CLI-local `LOADER_DEFS` (or inject registry explicitly) so test monkeypatching remains effective.
- Keep `openai_web` on `firecrawl` only with `NO_FALLBACK`; do not append default fallback loaders for that route.
- For local example runs, execute the user's exact command first and only add env overrides (for example `UV_CACHE_DIR`) after reproducing a concrete failure.
- Symptom: Reddit loads fall through after JSON returns 403/blocked. Cause: Reddit blocks unauthenticated JSON more aggressively while RSS is still the more reliable lightweight source when fetched with default httpx headers. Fix: prefer RSS before JSON and do not add browser-like headers to RSS requests.
- Treat CLI `--loader` and direct `kabigon.loaders.*` usage as advanced escape hatches; the preferred public interface is automatic Pipeline planning through `kabigon <url>` / `kabigon.load_url(url)`.
- Keep Load chain Loader construction lazy; do not let later Fallback loader constructors run before earlier Loader attempts fail.
- Symptom: `rich` stays in `uv.lock` after removing direct CLI deps. Cause: `curl-cffi` 0.15 depends on `rich`. Fix: keep `curl-cffi<0.15` while the no-Rich runtime goal applies.

## TASTE

- Prefer centralized URL matching in a single module instead of splitting routing rules across many small modules.
- Prefer plain data-table definitions for loader/pipeline wiring over `*Spec` abstractions when behavior is straightforward.
- Prefer top-level flow clarity (CLI and routing path) over extra indirection layers.
- Prefer an application-level Pipeline catalog to own Pipeline metadata; keep loader registry focused on loader factory wiring.
- Prefer Load chain as the runnable + explainable retrieval seam; keep Pipeline catalog and registry as supporting modules.
