from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from typing import Protocol

from kabigon.core.errors import MissingDependencyError
from kabigon.core.loader import Loader

LoaderFactory = Callable[[], Loader]

PTT = "ptt"
TWITTER = "twitter"
TRUTHSOCIAL = "truthsocial"
REDDIT = "reddit"
YOUTUBE = "youtube"
REEL = "reel"
YOUTUBE_YTDLP = "youtube-ytdlp"
PDF = "pdf"
PI_SESSION = "pi-session"
GITHUB = "github"
BBC = "bbc"
CNN = "cnn"
LTN = "ltn"
PLAYWRIGHT_NETWORKIDLE = "playwright-networkidle"
PLAYWRIGHT_FAST = "playwright-fast"
PLAYWRIGHT = "playwright"
CURL_CFFI = "curl-cffi"
HTTPX = "httpx"
FIRECRAWL = "firecrawl"
YTDLP = "ytdlp"


@dataclass(frozen=True)
class LoaderDef:
    name: str
    description: str
    module: str
    class_name: str
    content_type: str
    requirements: tuple[str, ...] = ()
    cli_visible: bool = True
    kwargs: tuple[tuple[str, object], ...] = ()
    optional_dependencies: tuple[str, ...] = ()
    installation_hint: str = "Install kabigon with its default dependencies."
    resource_kind: str = "request"

    @property
    def factory(self) -> LoaderFactory:
        return _LazyFactory(self)


class _ClientFactoryProvider(Protocol):
    def loader_kwargs(self, loader_def: LoaderDef) -> dict[str, Any]: ...


class _LazyFactory:
    def __init__(self, loader_def: LoaderDef, client: _ClientFactoryProvider | None = None) -> None:
        self.loader_def = loader_def
        self.client = client

    def __call__(self) -> Loader:
        definition = self.loader_def
        try:
            module = importlib.import_module(definition.module)
        except ModuleNotFoundError as error:
            missing_root = (error.name or "").split(".", maxsplit=1)[0]
            if missing_root in definition.optional_dependencies:
                raise MissingDependencyError(
                    definition.name, error.name or missing_root, definition.installation_hint
                ) from error
            raise

        loader_class = getattr(module, definition.class_name)
        kwargs = dict(definition.kwargs)
        if self.client is not None:
            kwargs.update(self.client.loader_kwargs(definition))
        return loader_class(**kwargs)


_BROWSER_HINT = "Install the Playwright dependency and run `playwright install chromium`."
_TRANSCRIPTION_HINT = "Install yt-dlp, OpenAI Whisper, NumPy, and FFmpeg."

LOADER_DEFS: tuple[LoaderDef, ...] = (
    LoaderDef(PTT, "Taiwan PTT forum posts", "kabigon.loaders.ptt", "PttLoader", "social_post"),
    LoaderDef(
        TWITTER,
        "Extracts Twitter/X post content",
        "kabigon.loaders.twitter",
        "TwitterLoader",
        "social_post",
        optional_dependencies=("playwright",),
        installation_hint=_BROWSER_HINT,
        resource_kind="browser",
    ),
    LoaderDef(
        TRUTHSOCIAL,
        "Extracts Truth Social posts",
        "kabigon.loaders.truthsocial",
        "TruthSocialLoader",
        "social_post",
        optional_dependencies=("playwright",),
        installation_hint=_BROWSER_HINT,
        resource_kind="browser",
    ),
    LoaderDef(
        REDDIT,
        "Extracts Reddit posts and comments",
        "kabigon.loaders.reddit",
        "RedditLoader",
        "social_post",
        optional_dependencies=("playwright",),
        installation_hint=_BROWSER_HINT,
    ),
    LoaderDef(
        YOUTUBE,
        "Extracts YouTube video transcripts",
        "kabigon.loaders.youtube",
        "YoutubeLoader",
        "youtube_video",
        optional_dependencies=("youtube_transcript_api",),
        installation_hint="Install youtube-transcript-api.",
        resource_kind="worker",
    ),
    LoaderDef(
        REEL,
        "Instagram Reels audio transcription + metadata",
        "kabigon.loaders.reel",
        "ReelLoader",
        "social_post",
        optional_dependencies=("yt_dlp", "whisper", "numpy"),
        installation_hint=_TRANSCRIPTION_HINT,
    ),
    LoaderDef(
        YOUTUBE_YTDLP,
        "YouTube audio transcription via yt-dlp + Whisper",
        "kabigon.loaders.youtube_ytdlp",
        "YoutubeYtdlpLoader",
        "youtube_video",
        optional_dependencies=("yt_dlp", "whisper", "numpy"),
        installation_hint=_TRANSCRIPTION_HINT,
        resource_kind="worker",
    ),
    LoaderDef(
        PDF,
        "Extracts text from PDF files",
        "kabigon.loaders.pdf",
        "PDFLoader",
        "document_pdf",
        optional_dependencies=("pypdf", "curl_cffi"),
        installation_hint="Install pypdf and curl-cffi.",
    ),
    LoaderDef(
        PI_SESSION,
        "Extracts pi.dev shared session transcripts",
        "kabigon.loaders.pi_session",
        "PiSessionLoader",
        "ai_session",
    ),
    LoaderDef(
        GITHUB, "Fetches GitHub pages and file content", "kabigon.loaders.github", "GitHubLoader", "code_content"
    ),
    LoaderDef(
        BBC,
        "BBC article extraction with article-aware parsing",
        "kabigon.loaders.bbc",
        "BBCLoader",
        "news_article",
        optional_dependencies=("curl_cffi", "playwright"),
        installation_hint=_BROWSER_HINT,
    ),
    LoaderDef(
        CNN,
        "CNN article extraction with article-aware parsing",
        "kabigon.loaders.cnn",
        "CNNLoader",
        "news_article",
        optional_dependencies=("curl_cffi", "playwright"),
        installation_hint=_BROWSER_HINT,
    ),
    LoaderDef(
        LTN,
        "Liberty Times Net article extraction",
        "kabigon.loaders.ltn",
        "LTNLoader",
        "news_article",
        optional_dependencies=("curl_cffi", "playwright"),
        installation_hint=_BROWSER_HINT,
    ),
    LoaderDef(
        PLAYWRIGHT_NETWORKIDLE,
        "Browser-based scraping with networkidle wait",
        "kabigon.loaders.playwright",
        "PlaywrightLoader",
        "generic_web",
        cli_visible=False,
        kwargs=(("timeout", 50_000), ("wait_until", "networkidle")),
        optional_dependencies=("playwright",),
        installation_hint=_BROWSER_HINT,
        resource_kind="browser",
    ),
    LoaderDef(
        PLAYWRIGHT_FAST,
        "Browser-based scraping with faster defaults",
        "kabigon.loaders.playwright",
        "PlaywrightLoader",
        "generic_web",
        cli_visible=False,
        kwargs=(("timeout", 15_000), ("wait_until", "domcontentloaded")),
        optional_dependencies=("playwright",),
        installation_hint=_BROWSER_HINT,
        resource_kind="browser",
    ),
    LoaderDef(
        PLAYWRIGHT,
        "Browser-based scraping for any website",
        "kabigon.loaders.playwright",
        "PlaywrightLoader",
        "generic_web",
        optional_dependencies=("playwright",),
        installation_hint=_BROWSER_HINT,
        resource_kind="browser",
    ),
    LoaderDef(
        CURL_CFFI,
        "HTTP fetch with browser TLS fingerprint via curl_cffi",
        "kabigon.loaders.curl_cffi",
        "CurlCffiLoader",
        "generic_web",
        optional_dependencies=("curl_cffi",),
        installation_hint="Install curl-cffi.",
    ),
    LoaderDef(HTTPX, "Simple HTTP fetch + HTML to markdown", "kabigon.loaders.httpx", "HttpxLoader", "generic_web"),
    LoaderDef(
        FIRECRAWL,
        "Firecrawl-based web extraction (requires FIRECRAWL_API_KEY)",
        "kabigon.loaders.firecrawl",
        "FirecrawlLoader",
        "generic_web",
        requirements=("FIRECRAWL_API_KEY",),
        optional_dependencies=("firecrawl",),
        installation_hint="Install firecrawl-py and set FIRECRAWL_API_KEY.",
        resource_kind="worker",
    ),
    LoaderDef(
        YTDLP,
        "Audio transcription via yt-dlp + Whisper",
        "kabigon.loaders.ytdlp",
        "YtdlpLoader",
        "generic_web",
        optional_dependencies=("yt_dlp", "whisper", "numpy"),
        installation_hint=_TRANSCRIPTION_HINT,
        resource_kind="worker",
    ),
)

_LOADER_DEF_BY_NAME = {loader_def.name: loader_def for loader_def in LOADER_DEFS}


def get_loader_def(name: str) -> LoaderDef:
    return _LOADER_DEF_BY_NAME[name]


def get_loader_factory(name: str, client: _ClientFactoryProvider | None = None) -> LoaderFactory:
    return _LazyFactory(get_loader_def(name), client)


def get_loader_description(name: str) -> str:
    return get_loader_def(name).description


def get_loader_requirements(name: str) -> tuple[str, ...]:
    return get_loader_def(name).requirements


def get_loader_content_type(name: str) -> str:
    return get_loader_def(name).content_type


def list_loader_defs(*, cli_visible: bool | None = None) -> tuple[LoaderDef, ...]:
    if cli_visible is None:
        return LOADER_DEFS
    return tuple(definition for definition in LOADER_DEFS if definition.cli_visible is cli_visible)


def list_loader_names(*, cli_visible: bool | None = None) -> list[str]:
    return [definition.name for definition in list_loader_defs(cli_visible=cli_visible)]


__all__ = [
    "BBC",
    "CNN",
    "CURL_CFFI",
    "FIRECRAWL",
    "GITHUB",
    "HTTPX",
    "LOADER_DEFS",
    "LTN",
    "PDF",
    "PI_SESSION",
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
    "get_loader_content_type",
    "get_loader_def",
    "get_loader_description",
    "get_loader_factory",
    "get_loader_requirements",
    "list_loader_defs",
    "list_loader_names",
]
