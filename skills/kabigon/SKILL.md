---
name: kabigon
description: Load URL content as text or markdown with kabigon. Use this for extracting content from YouTube videos, social posts, news articles, PDFs, GitHub files, generic web pages, and audio/video URLs through kabigon's automatic Pipeline planning.
---

## How to load URL content

Use the automatic path unless you are debugging or intentionally comparing Loaders. Kabigon matches the URL to a source-specific Pipeline, builds an Execution plan from Targeted loaders plus allowed Fallback loaders, and returns the first successful Loader result.

```shell
# CLI usage
uvx kabigon https://www.youtube.com/watch?v=dQw4w9WgXcQ
uvx kabigon https://x.com/howie_serious/status/1917768568135115147
uvx kabigon https://reddit.com/r/python/comments/xyz/...
uvx kabigon https://github.com/user/repo/blob/main/README.md
uvx kabigon https://example.com/document.pdf
```

```python
import kabigon

text = kabigon.load_url_sync("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
```

```python
import asyncio
import kabigon

text = await kabigon.load_url("https://x.com/user/status/123")
```

```shell
# List supported loader names.
uvx kabigon --list
```

```python
import kabigon

# Inspect the Pipeline, Targeted loaders, Execution plan, and requirements.
plan = kabigon.explain_plan("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
loaders = kabigon.available_loaders()
```

## Advanced loader selection

Use `--loader` only when debugging, comparing Loaders, or intentionally bypassing automatic Pipeline planning. A comma-separated loader list runs in the exact order provided.

```shell
uvx kabigon --loader playwright https://example.com
uvx kabigon --loader httpx https://example.com
uvx kabigon --loader firecrawl https://example.com
uvx kabigon --loader bbc https://www.bbc.com/news/articles/example
uvx kabigon --loader cnn https://www.cnn.com/2025/01/01/world/example/index.html
uvx kabigon --loader youtube https://www.youtube.com/watch?v=dQw4w9WgXcQ
uvx kabigon --loader youtube-ytdlp https://www.youtube.com/watch?v=dQw4w9WgXcQ
uvx kabigon --loader ytdlp https://www.youtube.com/watch?v=dQw4w9WgXcQ
uvx kabigon --loader twitter https://x.com/howie_serious/status/1917768568135115147
uvx kabigon --loader truthsocial https://truthsocial.com/@realDonaldTrump/posts/115830428767897167
uvx kabigon --loader reddit https://reddit.com/r/confession/comments/1q1mzej/im_a_developer_for_a_major_food_delivery_app_the/
uvx kabigon --loader ptt https://www.ptt.cc/bbs/Gossiping/M.1746078381.A.FFC.html
uvx kabigon --loader reel https://www.instagram.com/reel/CuA0XYZ1234/
uvx kabigon --loader github https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md
uvx kabigon --loader pdf https://example.com/document.pdf
```

```shell
# Run loaders in explicit order. Example: try YouTube transcripts first,
# then fall back to `youtube-ytdlp` audio transcription if captions are missing.
uvx kabigon --loader youtube,youtube-ytdlp https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Supported sources

- YouTube videos: `youtube`, then `youtube-ytdlp` audio transcription when needed.
- Social posts: `twitter`, `truthsocial`, `reddit`, `ptt`, and `reel`.
- News articles: `bbc` and `cnn` article-aware extraction.
- Code and documents: `github` file/page content and `pdf` text extraction.
- Generic web pages: `playwright`, `httpx`, or `firecrawl`.
- Audio/video URLs: `ytdlp` generic audio transcription.

## Failure behavior

- A Loader that cannot handle the input raises a not-applicable attempt so the Load chain can continue.
- Content extraction, timeout, and configuration failures are reported in the Load chain failure details.
- Prefer `kabigon.explain_plan(url)` when you need to understand why a URL will use a specific Pipeline or Loader order.

## Configuration notes

- `FIRECRAWL_API_KEY` is required for the `firecrawl` loader.
- `FFMPEG_PATH` can point to a custom FFmpeg binary for Whisper and yt-dlp transcription loaders.

## Troubleshooting

- Install `uv` if `uvx` is not found:
  ```text
  https://docs.astral.sh/uv/getting-started/installation/
  ```
