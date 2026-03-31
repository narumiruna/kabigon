# GOTCHA

## Python import shadowing with same-name module and package

- Pitfall: Keeping both `src/kabigon/pipelines.py` and `src/kabigon/pipelines/` at the same time causes ambiguous imports and brittle behavior.
- Why it was non-obvious: Both structures can coexist on disk, but import resolution and downstream references can silently drift depending on import style.
- Rule: Use exactly one shape for `pipelines` at a time. If the design chooses single-module routing, remove the `pipelines/` package completely.

## CLI tests can be invalidated by moving loader composition into service layer

- Pitfall: If CLI `--loader` path delegates directly to an application service that resolves loaders from global infrastructure registry, monkeypatching CLI-local loader definitions in tests no longer affects execution.
- Why it was non-obvious: CLI still validates names against local `LOADER_DEFS`, so tests may pass name validation but fail at runtime when service-layer lookup uses a different source.
- Rule: Keep CLI custom-loader execution path coupled to CLI-local loader registry (or inject registry dependency explicitly) so test-time overrides stay effective.
