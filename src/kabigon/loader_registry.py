from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import kabigon.loaders as loaders
from kabigon.core.loader import Loader

LoaderFactory = Callable[[], Loader]


@dataclass(frozen=True)
class LoaderDef:
    name: str
    description: str
    factory: LoaderFactory
    requirements: tuple[str, ...] = ()


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
LTN = "ltn"
PLAYWRIGHT_NETWORKIDLE = "playwright-networkidle"
PLAYWRIGHT_FAST = "playwright-fast"
PLAYWRIGHT = "playwright"
HTTPX = "httpx"
FIRECRAWL = "firecrawl"
YTDLP = "ytdlp"

LOADER_DEFS: tuple[LoaderDef, ...] = (
    LoaderDef(PTT, "Taiwan PTT forum posts", lambda: loaders.PttLoader()),
    LoaderDef(TWITTER, "Extracts Twitter/X post content", lambda: loaders.TwitterLoader()),
    LoaderDef(TRUTHSOCIAL, "Extracts Truth Social posts", lambda: loaders.TruthSocialLoader()),
    LoaderDef(REDDIT, "Extracts Reddit posts and comments", lambda: loaders.RedditLoader()),
    LoaderDef(YOUTUBE, "Extracts YouTube video transcripts", lambda: loaders.YoutubeLoader()),
    LoaderDef(REEL, "Instagram Reels audio transcription + metadata", lambda: loaders.ReelLoader()),
    LoaderDef(
        YOUTUBE_YTDLP,
        "YouTube audio transcription via yt-dlp + Whisper",
        lambda: loaders.YoutubeYtdlpLoader(),
    ),
    LoaderDef(PDF, "Extracts text from PDF files", lambda: loaders.PDFLoader()),
    LoaderDef(GITHUB, "Fetches GitHub pages and file content", lambda: loaders.GitHubLoader()),
    LoaderDef(BBC, "BBC article extraction with article-aware parsing", lambda: loaders.BBCLoader()),
    LoaderDef(CNN, "CNN article extraction with article-aware parsing", lambda: loaders.CNNLoader()),
    LoaderDef(LTN, "Liberty Times Net article extraction", lambda: loaders.LTNLoader()),
    LoaderDef(
        PLAYWRIGHT_NETWORKIDLE,
        "Browser-based scraping with networkidle wait",
        lambda: loaders.PlaywrightLoader(timeout=50_000, wait_until="networkidle"),
    ),
    LoaderDef(
        PLAYWRIGHT_FAST,
        "Browser-based scraping with faster defaults",
        lambda: loaders.PlaywrightLoader(timeout=15_000, wait_until="domcontentloaded"),
    ),
    LoaderDef(PLAYWRIGHT, "Browser-based scraping for any website", lambda: loaders.PlaywrightLoader()),
    LoaderDef(HTTPX, "Simple HTTP fetch + HTML to markdown", lambda: loaders.HttpxLoader()),
    LoaderDef(
        FIRECRAWL,
        "Firecrawl-based web extraction (requires FIRECRAWL_API_KEY)",
        lambda: loaders.FirecrawlLoader(),
        requirements=("FIRECRAWL_API_KEY",),
    ),
    LoaderDef(YTDLP, "Audio transcription via yt-dlp + Whisper", lambda: loaders.YtdlpLoader()),
)

_LOADER_DEF_BY_NAME: dict[str, LoaderDef] = {loader_def.name: loader_def for loader_def in LOADER_DEFS}


def get_loader_factory(name: str) -> LoaderFactory:
    return _LOADER_DEF_BY_NAME[name].factory


def get_loader_description(name: str) -> str:
    return _LOADER_DEF_BY_NAME[name].description


def get_loader_requirements(name: str) -> tuple[str, ...]:
    return _LOADER_DEF_BY_NAME[name].requirements


def list_loader_names() -> list[str]:
    return [loader_def.name for loader_def in LOADER_DEFS]


__all__ = [
    "BBC",
    "CNN",
    "FIRECRAWL",
    "GITHUB",
    "HTTPX",
    "LOADER_DEFS",
    "LTN",
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
    "get_loader_description",
    "get_loader_factory",
    "get_loader_requirements",
    "list_loader_names",
]
