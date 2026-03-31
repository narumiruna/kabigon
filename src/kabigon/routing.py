from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlparse

from kabigon.core.exception import KabigonError
from kabigon.loaders.bbc import check_bbc_url
from kabigon.loaders.cnn import check_cnn_url
from kabigon.loaders.github import check_github_url
from kabigon.loaders.ptt import check_ptt_url
from kabigon.loaders.reddit import check_reddit_url
from kabigon.loaders.reel import check_reel_url
from kabigon.loaders.truthsocial import check_truthsocial_url
from kabigon.loaders.twitter import check_x_url
from kabigon.loaders.youtube import check_youtube_url

ROUTE_MATCHERS: list[tuple[Callable[[str], None], list[str]]] = [
    (check_ptt_url, ["ptt"]),
    (check_x_url, ["twitter"]),
    (check_truthsocial_url, ["truthsocial"]),
    (check_reddit_url, ["reddit"]),
    (check_youtube_url, ["youtube", "youtube-ytdlp"]),
    (check_reel_url, ["reel"]),
    (check_github_url, ["github"]),
    (check_bbc_url, ["bbc"]),
    (check_cnn_url, ["cnn"]),
]


def _is_pdf_path(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.path.lower().endswith(".pdf")


def _matches(checker: Callable[[str], None], url: str) -> bool:
    try:
        checker(url)
    except (KabigonError, ValueError):
        return False
    return True


def route_url_to_pipeline_names(url: str) -> list[str]:
    if not url.startswith(("http://", "https://")):
        return ["pdf"]

    for checker, pipeline_names in ROUTE_MATCHERS:
        if _matches(checker, url):
            return pipeline_names

    if _is_pdf_path(url):
        return ["pdf"]

    return []
