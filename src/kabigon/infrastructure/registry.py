from __future__ import annotations

from collections.abc import Callable
from collections.abc import Sequence

import kabigon.loaders as loaders
from kabigon.application import loader_names
from kabigon.domain.loader import Loader

LoaderFactory = Callable[[], Loader]
LoaderDef = tuple[str, str, LoaderFactory]

LOADER_DEFS: tuple[LoaderDef, ...] = (
    (loader_names.PTT, "Taiwan PTT forum posts", lambda: loaders.PttLoader()),
    (loader_names.TWITTER, "Extracts Twitter/X post content", lambda: loaders.TwitterLoader()),
    (loader_names.TRUTHSOCIAL, "Extracts Truth Social posts", lambda: loaders.TruthSocialLoader()),
    (loader_names.REDDIT, "Extracts Reddit posts and comments", lambda: loaders.RedditLoader()),
    (loader_names.YOUTUBE, "Extracts YouTube video transcripts", lambda: loaders.YoutubeLoader()),
    (loader_names.REEL, "Instagram Reels audio transcription + metadata", lambda: loaders.ReelLoader()),
    (
        loader_names.YOUTUBE_YTDLP,
        "YouTube audio transcription via yt-dlp + Whisper",
        lambda: loaders.YoutubeYtdlpLoader(),
    ),
    (loader_names.PDF, "Extracts text from PDF files", lambda: loaders.PDFLoader()),
    (loader_names.GITHUB, "Fetches GitHub pages and file content", lambda: loaders.GitHubLoader()),
    (loader_names.BBC, "BBC article extraction with article-aware parsing", lambda: loaders.BBCLoader()),
    (loader_names.CNN, "CNN article extraction with article-aware parsing", lambda: loaders.CNNLoader()),
    (
        loader_names.PLAYWRIGHT_NETWORKIDLE,
        "Browser-based scraping with networkidle wait",
        lambda: loaders.PlaywrightLoader(timeout=50_000, wait_until="networkidle"),
    ),
    (
        loader_names.PLAYWRIGHT_FAST,
        "Browser-based scraping with faster defaults",
        lambda: loaders.PlaywrightLoader(timeout=10_000),
    ),
    (loader_names.PLAYWRIGHT, "Browser-based scraping for any website", lambda: loaders.PlaywrightLoader()),
    (loader_names.HTTPX, "Simple HTTP fetch + HTML to markdown", lambda: loaders.HttpxLoader()),
    (
        loader_names.FIRECRAWL,
        "Firecrawl-based web extraction (requires FIRECRAWL_API_KEY)",
        lambda: loaders.FirecrawlLoader(),
    ),
    (loader_names.YTDLP, "Audio transcription via yt-dlp + Whisper", lambda: loaders.YtdlpLoader()),
)

_LOADER_FACTORY_BY_NAME: dict[str, LoaderFactory] = {name: factory for name, _description, factory in LOADER_DEFS}
_LOADER_DESCRIPTION_BY_NAME: dict[str, str] = {name: description for name, description, _factory in LOADER_DEFS}

CLI_VISIBLE_LOADER_NAMES = loader_names.CLI_VISIBLE_LOADERS


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
