from __future__ import annotations

from collections.abc import Callable
from collections.abc import Sequence

import kabigon.loaders as loaders
from kabigon.core.loader import Loader

LoaderFactory = Callable[[], Loader]
LoaderDef = tuple[str, str, LoaderFactory]

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

LOADER_DEFS: tuple[LoaderDef, ...] = (
    (PTT, "Taiwan PTT forum posts", lambda: loaders.PttLoader()),
    (TWITTER, "Extracts Twitter/X post content", lambda: loaders.TwitterLoader()),
    (TRUTHSOCIAL, "Extracts Truth Social posts", lambda: loaders.TruthSocialLoader()),
    (REDDIT, "Extracts Reddit posts and comments", lambda: loaders.RedditLoader()),
    (YOUTUBE, "Extracts YouTube video transcripts", lambda: loaders.YoutubeLoader()),
    (REEL, "Instagram Reels audio transcription + metadata", lambda: loaders.ReelLoader()),
    (
        YOUTUBE_YTDLP,
        "YouTube audio transcription via yt-dlp + Whisper",
        lambda: loaders.YoutubeYtdlpLoader(),
    ),
    (PDF, "Extracts text from PDF files", lambda: loaders.PDFLoader()),
    (GITHUB, "Fetches GitHub pages and file content", lambda: loaders.GitHubLoader()),
    (BBC, "BBC article extraction with article-aware parsing", lambda: loaders.BBCLoader()),
    (CNN, "CNN article extraction with article-aware parsing", lambda: loaders.CNNLoader()),
    (
        PLAYWRIGHT_NETWORKIDLE,
        "Browser-based scraping with networkidle wait",
        lambda: loaders.PlaywrightLoader(timeout=50_000, wait_until="networkidle"),
    ),
    (
        PLAYWRIGHT_FAST,
        "Browser-based scraping with faster defaults",
        lambda: loaders.PlaywrightLoader(timeout=10_000),
    ),
    (PLAYWRIGHT, "Browser-based scraping for any website", lambda: loaders.PlaywrightLoader()),
    (HTTPX, "Simple HTTP fetch + HTML to markdown", lambda: loaders.HttpxLoader()),
    (
        FIRECRAWL,
        "Firecrawl-based web extraction (requires FIRECRAWL_API_KEY)",
        lambda: loaders.FirecrawlLoader(),
    ),
    (YTDLP, "Audio transcription via yt-dlp + Whisper", lambda: loaders.YtdlpLoader()),
)

_LOADER_FACTORY_BY_NAME: dict[str, LoaderFactory] = {name: factory for name, _description, factory in LOADER_DEFS}
_LOADER_DESCRIPTION_BY_NAME: dict[str, str] = {name: description for name, description, _factory in LOADER_DEFS}

CLI_VISIBLE_LOADER_NAMES = CLI_VISIBLE_LOADERS


def get_loader_factory(name: str) -> LoaderFactory:
    return _LOADER_FACTORY_BY_NAME[name]


def get_loader_descriptions(names: Sequence[str]) -> list[tuple[str, str]]:
    return [(name, _LOADER_DESCRIPTION_BY_NAME[name]) for name in names]


def get_cli_loader_defs() -> list[LoaderDef]:
    return [
        (name, _LOADER_DESCRIPTION_BY_NAME[name], _LOADER_FACTORY_BY_NAME[name]) for name in CLI_VISIBLE_LOADER_NAMES
    ]


def list_loader_names() -> list[str]:
    return [name for name, _description, _factory in LOADER_DEFS]


__all__ = [
    "BBC",
    "CLI_VISIBLE_LOADERS",
    "CLI_VISIBLE_LOADER_NAMES",
    "CNN",
    "DEFAULT_FALLBACK_LOADERS",
    "FIRECRAWL",
    "GITHUB",
    "HTTPX",
    "LOADER_DEFS",
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
    "LoaderDef",
    "LoaderFactory",
    "get_cli_loader_defs",
    "get_loader_descriptions",
    "get_loader_factory",
    "list_loader_names",
]
