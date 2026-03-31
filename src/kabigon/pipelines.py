from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlparse

Matcher = Callable[[str], bool]
PipelineDef = tuple[str, Matcher, tuple[str, ...]]


def _host(url: str) -> str:
    return urlparse(url).netloc.lower()


def _is_http_url(url: str) -> bool:
    return url.startswith(("http://", "https://"))


def _is_pdf_path(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".pdf")


def _is_ptt_url(url: str) -> bool:
    return _host(url) == "www.ptt.cc"


def _is_twitter_url(url: str) -> bool:
    return _host(url) in {
        "twitter.com",
        "x.com",
        "fxtwitter.com",
        "vxtwitter.com",
        "fixvx.com",
        "twittpr.com",
        "api.fxtwitter.com",
        "fixupx.com",
    }


def _is_truthsocial_url(url: str) -> bool:
    return _host(url) in {"truthsocial.com", "www.truthsocial.com"}


def _is_reddit_url(url: str) -> bool:
    return _host(url) in {"reddit.com", "www.reddit.com", "old.reddit.com"}


def _is_youtube_url(url: str) -> bool:
    return _host(url) in {
        "youtu.be",
        "m.youtube.com",
        "music.youtube.com",
        "youtube.com",
        "www.youtube.com",
        "www.youtube-nocookie.com",
        "vid.plus",
    }


def _is_reel_url(url: str) -> bool:
    return url.startswith("https://www.instagram.com/reel")


def _is_github_url(url: str) -> bool:
    return _host(url) in {"github.com", "raw.githubusercontent.com"}


def _is_bbc_url(url: str) -> bool:
    host = _host(url)
    return host == "bbc.com" or host.endswith(".bbc.com")


def _is_cnn_url(url: str) -> bool:
    host = _host(url)
    return host == "cnn.com" or host.endswith(".cnn.com")


def _is_pdf_url(url: str) -> bool:
    if not _is_http_url(url):
        return True
    return _is_pdf_path(url)


PIPELINES: tuple[PipelineDef, ...] = (
    ("ptt", _is_ptt_url, ("ptt",)),
    ("twitter", _is_twitter_url, ("twitter",)),
    ("truthsocial", _is_truthsocial_url, ("truthsocial",)),
    ("reddit", _is_reddit_url, ("reddit",)),
    ("youtube", _is_youtube_url, ("youtube", "youtube-ytdlp")),
    ("reel", _is_reel_url, ("reel",)),
    ("github", _is_github_url, ("github",)),
    ("bbc", _is_bbc_url, ("bbc",)),
    ("cnn", _is_cnn_url, ("cnn",)),
    ("pdf", _is_pdf_url, ("pdf",)),
)


DEFAULT_FALLBACK_LOADERS: tuple[str, ...] = (
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
)


def resolve_pipeline_name(url: str) -> str | None:
    for pipeline_name, matcher, _loaders in PIPELINES:
        if matcher(url):
            return pipeline_name
    return None


def resolve_targeted_loader_names(url: str) -> list[str]:
    for _pipeline_name, matcher, loaders in PIPELINES:
        if matcher(url):
            return list(loaders)
    return []
