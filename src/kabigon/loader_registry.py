from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from . import loaders
from .core.loader import Loader


@dataclass(frozen=True)
class LoaderSpec:
    name: str
    description: str
    factory: Callable[[], Loader]


LOADER_SPECS_BY_NAME: dict[str, LoaderSpec] = {
    "ptt": LoaderSpec("ptt", "Taiwan PTT forum posts", lambda: loaders.PttLoader()),
    "twitter": LoaderSpec("twitter", "Extracts Twitter/X post content", lambda: loaders.TwitterLoader()),
    "truthsocial": LoaderSpec("truthsocial", "Extracts Truth Social posts", lambda: loaders.TruthSocialLoader()),
    "reddit": LoaderSpec("reddit", "Extracts Reddit posts and comments", lambda: loaders.RedditLoader()),
    "youtube": LoaderSpec("youtube", "Extracts YouTube video transcripts", lambda: loaders.YoutubeLoader()),
    "reel": LoaderSpec("reel", "Instagram Reels audio transcription + metadata", lambda: loaders.ReelLoader()),
    "youtube-ytdlp": LoaderSpec(
        "youtube-ytdlp",
        "YouTube audio transcription via yt-dlp + Whisper",
        lambda: loaders.YoutubeYtdlpLoader(),
    ),
    "pdf": LoaderSpec("pdf", "Extracts text from PDF files", lambda: loaders.PDFLoader()),
    "github": LoaderSpec("github", "Fetches GitHub pages and file content", lambda: loaders.GitHubLoader()),
    "bbc": LoaderSpec("bbc", "BBC article extraction with article-aware parsing", lambda: loaders.BBCLoader()),
    "cnn": LoaderSpec("cnn", "CNN article extraction with article-aware parsing", lambda: loaders.CNNLoader()),
    "playwright-networkidle": LoaderSpec(
        "playwright-networkidle",
        "Browser-based scraping with networkidle wait",
        lambda: loaders.PlaywrightLoader(timeout=50_000, wait_until="networkidle"),
    ),
    "playwright-fast": LoaderSpec(
        "playwright-fast",
        "Browser-based scraping with faster defaults",
        lambda: loaders.PlaywrightLoader(timeout=10_000),
    ),
    "playwright": LoaderSpec(
        "playwright", "Browser-based scraping for any website", lambda: loaders.PlaywrightLoader()
    ),
    "httpx": LoaderSpec("httpx", "Simple HTTP fetch + HTML to markdown", lambda: loaders.HttpxLoader()),
    "firecrawl": LoaderSpec("firecrawl", "Firecrawl-based web extraction", lambda: loaders.FirecrawlLoader()),
    "ytdlp": LoaderSpec("ytdlp", "Audio transcription via yt-dlp + Whisper", lambda: loaders.YtdlpLoader()),
}

DEFAULT_PIPELINE_STEP_NAMES: list[str] = [
    "ptt",
    "twitter",
    "truthsocial",
    "reddit",
    "youtube",
    "reel",
    "youtube-ytdlp",
    "pdf",
    "github",
    "bbc",
    "cnn",
    "playwright-networkidle",
    "playwright-fast",
]

CLI_LOADER_STEP_NAMES: list[str] = [
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
]


def get_loader_specs_by_name(names: list[str]) -> list[LoaderSpec]:
    return [LOADER_SPECS_BY_NAME[name] for name in names]


def get_default_loader_specs() -> list[LoaderSpec]:
    return get_loader_specs_by_name(DEFAULT_PIPELINE_STEP_NAMES)


def get_cli_loader_specs() -> list[LoaderSpec]:
    return get_loader_specs_by_name(CLI_LOADER_STEP_NAMES)
