from __future__ import annotations

from collections.abc import Callable
from collections.abc import Sequence

import kabigon.loaders as loaders
from kabigon.domain.loader import Loader

LoaderFactory = Callable[[], Loader]
LoaderDef = tuple[str, str, LoaderFactory]

LOADER_DEFS: tuple[LoaderDef, ...] = (
    ("ptt", "Taiwan PTT forum posts", lambda: loaders.PttLoader()),
    ("twitter", "Extracts Twitter/X post content", lambda: loaders.TwitterLoader()),
    ("truthsocial", "Extracts Truth Social posts", lambda: loaders.TruthSocialLoader()),
    ("reddit", "Extracts Reddit posts and comments", lambda: loaders.RedditLoader()),
    ("youtube", "Extracts YouTube video transcripts", lambda: loaders.YoutubeLoader()),
    ("reel", "Instagram Reels audio transcription + metadata", lambda: loaders.ReelLoader()),
    (
        "youtube-ytdlp",
        "YouTube audio transcription via yt-dlp + Whisper",
        lambda: loaders.YoutubeYtdlpLoader(),
    ),
    ("pdf", "Extracts text from PDF files", lambda: loaders.PDFLoader()),
    ("github", "Fetches GitHub pages and file content", lambda: loaders.GitHubLoader()),
    ("bbc", "BBC article extraction with article-aware parsing", lambda: loaders.BBCLoader()),
    ("cnn", "CNN article extraction with article-aware parsing", lambda: loaders.CNNLoader()),
    (
        "playwright-networkidle",
        "Browser-based scraping with networkidle wait",
        lambda: loaders.PlaywrightLoader(timeout=50_000, wait_until="networkidle"),
    ),
    (
        "playwright-fast",
        "Browser-based scraping with faster defaults",
        lambda: loaders.PlaywrightLoader(timeout=10_000),
    ),
    ("playwright", "Browser-based scraping for any website", lambda: loaders.PlaywrightLoader()),
    ("httpx", "Simple HTTP fetch + HTML to markdown", lambda: loaders.HttpxLoader()),
    ("firecrawl", "Firecrawl-based web extraction (requires FIRECRAWL_API_KEY)", lambda: loaders.FirecrawlLoader()),
    ("ytdlp", "Audio transcription via yt-dlp + Whisper", lambda: loaders.YtdlpLoader()),
)

_LOADER_FACTORY_BY_NAME: dict[str, LoaderFactory] = {name: factory for name, _description, factory in LOADER_DEFS}
_LOADER_DESCRIPTION_BY_NAME: dict[str, str] = {name: description for name, description, _factory in LOADER_DEFS}

CLI_VISIBLE_LOADER_NAMES: tuple[str, ...] = (
    "playwright",
    "httpx",
    "bbc",
    "cnn",
    "firecrawl",
    "youtube",
    "youtube-ytdlp",
    "ytdlp",
    "twitter",
    "truthsocial",
    "reddit",
    "ptt",
    "reel",
    "github",
    "pdf",
)


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
