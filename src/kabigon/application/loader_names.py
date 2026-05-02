PTT = "ptt"
TWITTER = "twitter"
TRUTHSOCIAL = "truthsocial"
REDDIT = "reddit"
YOUTUBE = "youtube"
REEL = "reel"
YOUTUBE_YTDLP = "youtube-ytdlp"
PDF = "pdf"
GITHUB = "github"
BBC = "bbc"
CNN = "cnn"
PLAYWRIGHT_NETWORKIDLE = "playwright-networkidle"
PLAYWRIGHT_FAST = "playwright-fast"
PLAYWRIGHT = "playwright"
HTTPX = "httpx"
FIRECRAWL = "firecrawl"
YTDLP = "ytdlp"

DEFAULT_FALLBACK_LOADERS = (
    PTT,
    TWITTER,
    TRUTHSOCIAL,
    REDDIT,
    YOUTUBE,
    REEL,
    YOUTUBE_YTDLP,
    PDF,
    GITHUB,
    BBC,
    CNN,
    PLAYWRIGHT_NETWORKIDLE,
    PLAYWRIGHT_FAST,
)

CLI_VISIBLE_LOADERS = (
    PLAYWRIGHT,
    HTTPX,
    BBC,
    CNN,
    FIRECRAWL,
    YOUTUBE,
    YOUTUBE_YTDLP,
    YTDLP,
    TWITTER,
    TRUTHSOCIAL,
    REDDIT,
    PTT,
    REEL,
    GITHUB,
    PDF,
)

__all__ = [
    "BBC",
    "CLI_VISIBLE_LOADERS",
    "CNN",
    "DEFAULT_FALLBACK_LOADERS",
    "FIRECRAWL",
    "GITHUB",
    "HTTPX",
    "PDF",
    "PLAYWRIGHT",
    "PLAYWRIGHT_FAST",
    "PLAYWRIGHT_NETWORKIDLE",
    "PTT",
    "REDDIT",
    "REEL",
    "TRUTHSOCIAL",
    "TWITTER",
    "YOUTUBE",
    "YOUTUBE_YTDLP",
    "YTDLP",
]
