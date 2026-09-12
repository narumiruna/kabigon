from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bbc import BBCLoader as BBCLoader
    from .cnn import CNNLoader as CNNLoader
    from .curl_cffi import CurlCffiLoader as CurlCffiLoader
    from .firecrawl import FirecrawlLoader as FirecrawlLoader
    from .github import GitHubLoader as GitHubLoader
    from .httpx import HttpxLoader as HttpxLoader
    from .ltn import LTNLoader as LTNLoader
    from .pdf import PDFLoader as PDFLoader
    from .pi_session import PiSessionLoader as PiSessionLoader
    from .playwright import PlaywrightLoader as PlaywrightLoader
    from .ptt import PttLoader as PttLoader
    from .reddit import RedditLoader as RedditLoader
    from .reel import ReelLoader as ReelLoader
    from .truthsocial import TruthSocialLoader as TruthSocialLoader
    from .twitter import TwitterLoader as TwitterLoader
    from .youtube import YoutubeLoader as YoutubeLoader
    from .youtube_ytdlp import YoutubeYtdlpLoader as YoutubeYtdlpLoader
    from .ytdlp import YtdlpLoader as YtdlpLoader

_EXPORTS = {
    "BBCLoader": "bbc",
    "CNNLoader": "cnn",
    "CurlCffiLoader": "curl_cffi",
    "FirecrawlLoader": "firecrawl",
    "GitHubLoader": "github",
    "HttpxLoader": "httpx",
    "LTNLoader": "ltn",
    "PDFLoader": "pdf",
    "PiSessionLoader": "pi_session",
    "PlaywrightLoader": "playwright",
    "PttLoader": "ptt",
    "RedditLoader": "reddit",
    "ReelLoader": "reel",
    "TruthSocialLoader": "truthsocial",
    "TwitterLoader": "twitter",
    "YoutubeLoader": "youtube",
    "YoutubeYtdlpLoader": "youtube_ytdlp",
    "YtdlpLoader": "ytdlp",
}


def __getattr__(name: str) -> object:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(name)
    value = getattr(importlib.import_module(f"{__name__}.{module_name}"), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted((*globals(), *_EXPORTS))


__all__ = list(_EXPORTS)
