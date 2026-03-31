# GOTCHA

## Python import shadowing with same-name module and package

- Pitfall: Keeping both `src/kabigon/pipelines.py` and `src/kabigon/pipelines/` at the same time causes ambiguous imports and brittle behavior.
- Why it was non-obvious: Both structures can coexist on disk, but import resolution and downstream references can silently drift depending on import style.
- Rule: Use exactly one shape for `pipelines` at a time. If the design chooses single-module routing, remove the `pipelines/` package completely.
