# Early Load Chain Architecture

This document records Kabigon's early pre-routing architecture around `v0.14.1` and earlier. That design did not have a Pipeline catalog, URL routing, planner, or execution policy object. It used one fixed `Compose` chain and relied on each Loader to either succeed or fail.

## Core Shape

```text
URL -> fixed Compose loader order -> first successful Loader result
```

The load chain was deliberately simple:

- The caller supplied one URL.
- `Compose` attempted Loaders in a fixed order.
- A Loader failure did not stop the chain.
- An empty result was treated as failure and the next Loader was attempted.
- The first non-empty result was returned.
- If every Loader failed or returned empty output, `Compose` raised an error.

There was no URL-specific planning step. Loader order encoded the retrieval strategy.

## `v0.10.1` and `v0.12.0`

The CLI owned the load chain directly. `src/kabigon/cli.py` instantiated `Compose([...])` inside `run()` and called `loader.load(url)` or `loader.load_sync(url)` depending on the version's async boundary.

Representative shape:

```python
def run(url: str) -> None:
    loader = Compose(
        [
            PttLoader(),
            TwitterLoader(),
            YoutubeLoader(),
            ReelLoader(),
            PDFLoader(),
            PlaywrightLoader(),
        ]
    )
    result = loader.load(url)
    print(result)
```

By `v0.12.0`, the chain had grown but was still CLI-local:

```python
def run(url: str) -> None:
    loader = Compose(
        [
            PttLoader(),
            TwitterLoader(),
            TruthSocialLoader(),
            RedditLoader(),
            YoutubeLoader(),
            ReelLoader(),
            YoutubeYtdlpLoader(),
            PDFLoader(),
            PlaywrightLoader(timeout=50_000, wait_until="networkidle"),
            PlaywrightLoader(timeout=10_000),
        ]
    )
    result = loader.load_sync(url)
    print(result)
```

The important property was not the exact Loader list; it was that the whole retrieval strategy was visible as one ordered list.

## `v0.13.0`

`v0.13.0` moved the fixed chain out of CLI and into `api._get_default_loader()`.

The CLI became a thin wrapper:

```python
def run(url: str) -> None:
    result = load_url_sync(url)
    print(result)
```

The API owned the default chain:

```python
def _get_default_loader() -> Compose:
    return Compose(
        [
            PttLoader(),
            TwitterLoader(),
            TruthSocialLoader(),
            RedditLoader(),
            YoutubeLoader(),
            ReelLoader(),
            YoutubeYtdlpLoader(),
            PDFLoader(),
            PlaywrightLoader(timeout=50_000, wait_until="networkidle"),
            PlaywrightLoader(timeout=10_000),
        ]
    )
```

This was the first clearer boundary:

- CLI handled input and output.
- API exposed `load_url_sync()` and `load_url()`.
- `Compose` handled fallback behavior.
- Individual Loaders handled source-specific extraction.

## `v0.14.1`

`v0.14.1` kept the same architecture after package reorganization. Loaders lived under `src/kabigon/loaders/`, and `api.py` built the default `loaders.Compose`.

The default chain was:

```python
return loaders.Compose(
    [
        loaders.PttLoader(),
        loaders.TwitterLoader(),
        loaders.TruthSocialLoader(),
        loaders.RedditLoader(),
        loaders.YoutubeLoader(),
        loaders.ReelLoader(),
        loaders.YoutubeYtdlpLoader(),
        loaders.PDFLoader(),
        loaders.GitHubLoader(),
        loaders.PlaywrightLoader(timeout=50_000, wait_until="networkidle"),
        loaders.PlaywrightLoader(timeout=10_000),
    ]
)
```

`Compose` remained the fallback engine:

```python
async def load(self, url: str) -> str:
    for loader in self.loaders:
        try:
            result = await loader.load(url)
        except Exception:
            continue

        if not result:
            continue

        return result

    raise LoaderError(url)
```

The actual implementation logged each failure and success, but the control flow was this small.

## Responsibilities

The early load chain had four practical responsibilities:

- `cli.py`: parse one URL and print the result.
- `api.py`: expose sync and async public loading functions.
- `Compose`: attempt Loaders in order and implement fallback semantics.
- `Loader`: validate and extract content for one source or technique.

There were no separate responsibilities for:

- Pipeline selection.
- URL classification before execution.
- Targeted Loader planning.
- Fallback policy selection.
- Loader factory registry.

Those concerns only became explicit later when URL-specific ordering was introduced.

## What Made It Useful

This shape was easy to understand because the execution path was linear and local. To change fallback behavior, inspect `Compose`. To change retrieval order, inspect `_get_default_loader()` or the CLI-local `Compose([...])` list in older tags.

The tradeoff was that every URL paid the same ordered attempts. A YouTube URL still depended on earlier Loaders failing before YouTube-specific Loaders ran if they appeared later in the list. That is the pressure that later led to URL routing and targeted loaders.

## Design Lesson

Prefer this fixed load chain when behavior can be expressed as one global fallback order. Move to Pipeline catalog and Execution plan concepts only when URL-specific ordering, URL-specific requirements, or explicit fallback policy is needed.
