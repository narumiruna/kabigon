---
name: kabigon
description: Load URL content as text or markdown with kabigon. Use this for extracting content from YouTube videos, social posts, news articles, PDFs, GitHub files, generic web pages, and audio/video URLs.
---

## How to load URL content

```shell
# Prefer automatic pipeline planning. Kabigon selects targeted loaders first,
# then falls back to generic loaders when policy allows it.
uvx kabigon https://www.youtube.com/watch?v=dQw4w9WgXcQ
uvx kabigon https://x.com/howie_serious/status/1917768568135115147
uvx kabigon https://reddit.com/r/python/comments/xyz/...
uvx kabigon https://github.com/user/repo/blob/main/README.md
uvx kabigon https://example.com/document.pdf
```

```shell
# List supported loader names.
uvx kabigon --list
```

## Advanced loader selection

Use `--loader` only when debugging, comparing loaders, or intentionally bypassing automatic pipeline planning.

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

- YouTube videos: transcript extraction, then optional yt-dlp + Whisper audio transcription.
- Social posts: Twitter/X, Truth Social, Reddit, PTT, and Instagram Reels.
- News articles: BBC and CNN article-aware extraction.
- Code and documents: GitHub file/page content and PDF text extraction.
- Generic web pages: Playwright browser rendering, HTTPX HTML-to-markdown, or Firecrawl.
- Audio/video URLs: generic yt-dlp + Whisper transcription.

## Configuration notes

- `FIRECRAWL_API_KEY` is required for the `firecrawl` loader.
- `FFMPEG_PATH` can point to a custom FFmpeg binary for Whisper and yt-dlp transcription loaders.

## Troubleshooting

- Install `uv` if `uvx` is not found:
  ```text
  https://docs.astral.sh/uv/getting-started/installation/
  ```
