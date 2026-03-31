# CLI Design Proposals

```shell
## Default pipeline
kabigon https://www.youtube.com/watch?v=dQw4w9WgXcQ

# List supported loaders
kabigon --list

# Explicit loader selection
kabigon --loader playwright https://example.com
kabigon --loader httpx https://example.com
kabigon --loader firecrawl https://example.com
kabigon --loader youtube https://www.youtube.com/watch?v=dQw4w9WgXcQ
kabigon --loader youtube-ytdlp https://www.youtube.com/watch?v=dQw4w9WgXcQ
kabigon --loader ytdlp https://www.youtube.com/watch?v=dQw4w9WgXcQ
kabigon --loader twitter https://x.com/howie_serious/status/1917768568135115147
kabigon --loader truthsocial https://truthsocial.com/@realDonaldTrump/posts/115830428767897167
kabigon --loader reddit https://reddit.com/r/confession/comments/1q1mzej/im_a_developer_for_a_major_food_delivery_app_the/
kabigon --loader ptt https://www.ptt.cc/bbs/Gossiping/M.1746078381.A.FFC.html
kabigon --loader reel https://www.instagram.com/reel/CuA0XYZ1234/
kabigon --loader github https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md
kabigon --loader pdf https://example.com/document.pdf

# Compose loaders in order
kabigon --loader youtube,playwright https://www.youtube.com/watch?v=dQw4w9WgXcQ
```
