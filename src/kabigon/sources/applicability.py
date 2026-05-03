from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlparse
from urllib.parse import urlunparse

from kabigon.core.errors import InvalidURLError
from kabigon.core.errors import KabigonError
from kabigon.core.errors import LoaderNotApplicableError

BBC_DOMAIN_SUFFIX = "bbc.com"
CNN_DOMAIN_SUFFIX = "cnn.com"
YOUTUBE_ALLOWED_SCHEMES = {
    "http",
    "https",
}
YOUTUBE_ALLOWED_NETLOCS = {
    "youtu.be",
    "m.youtube.com",
    "music.youtube.com",
    "youtube.com",
    "www.youtube.com",
    "www.youtube-nocookie.com",
    "vid.plus",
}
GITHUB_HOST = "github.com"
ARXIV_HOSTS = (
    "arxiv.org",
    "www.arxiv.org",
)
OPENAI_WEB_HOSTS = (
    "openai.com",
    "www.openai.com",
    "help.openai.com",
    "platform.openai.com",
)
PTT_HOSTS = ("www.ptt.cc",)
RAW_GITHUB_HOST = "raw.githubusercontent.com"
REDDIT_DOMAINS = (
    "reddit.com",
    "www.reddit.com",
    "old.reddit.com",
)
REEL_PREFIX = "https://www.instagram.com/reel"
TRUTHSOCIAL_DOMAINS = (
    "truthsocial.com",
    "www.truthsocial.com",
)
TWITTER_DOMAINS = (
    "twitter.com",
    "x.com",
    "fxtwitter.com",
    "vxtwitter.com",
    "fixvx.com",
    "twittpr.com",
    "api.fxtwitter.com",
    "fixupx.com",
)


class UnsupportedURLSchemeError(KabigonError):
    def __init__(self, scheme: str) -> None:
        super().__init__(f"unsupported URL scheme: {scheme}")


class UnsupportedURLNetlocError(KabigonError):
    def __init__(self, netloc: str) -> None:
        super().__init__(f"unsupported URL netloc: {netloc}")


class VideoIDError(KabigonError):
    def __init__(self, video_id: str) -> None:
        super().__init__(f"invalid video ID: {video_id}")


class NoVideoIDFoundError(KabigonError):
    def __init__(self, url: str) -> None:
        super().__init__(f"no video found in URL: {url}")


_SOURCE_APPLICABILITY_ERRORS = (
    InvalidURLError,
    UnsupportedURLSchemeError,
    UnsupportedURLNetlocError,
    NoVideoIDFoundError,
    VideoIDError,
)


@dataclass(frozen=True)
class YouTubeVideoTarget:
    url: str
    video_id: str


@dataclass(frozen=True)
class GitHubTarget:
    url: str
    raw_url: str | None = None

    @property
    def is_raw_content(self) -> bool:
        return self.raw_url is not None


@dataclass(frozen=True)
class PDFTarget:
    target: str


@dataclass(frozen=True)
class BBCTarget:
    url: str


@dataclass(frozen=True)
class CNNTarget:
    url: str


@dataclass(frozen=True)
class PttTarget:
    url: str


@dataclass(frozen=True)
class RedditTarget:
    url: str


@dataclass(frozen=True)
class ReelTarget:
    url: str


@dataclass(frozen=True)
class TruthSocialTarget:
    url: str


@dataclass(frozen=True)
class TwitterTarget:
    url: str
    normalized_url: str


def require_loader_applicability[TargetT](
    loader_name: str,
    target: str,
    parse_target: Callable[[str], TargetT],
) -> TargetT:
    try:
        return parse_target(target)
    except LoaderNotApplicableError:
        raise
    except _SOURCE_APPLICABILITY_ERRORS as e:
        raise LoaderNotApplicableError(loader_name, target, str(e)) from e


def parse_youtube_video_target(url: str) -> YouTubeVideoTarget:
    parsed_url = urlparse(url)

    if parsed_url.scheme not in YOUTUBE_ALLOWED_SCHEMES:
        raise UnsupportedURLSchemeError(parsed_url.scheme)

    if parsed_url.netloc not in YOUTUBE_ALLOWED_NETLOCS:
        raise UnsupportedURLNetlocError(parsed_url.netloc)

    path = parsed_url.path
    if path.endswith("/watch"):
        parsed_query = parse_qs(parsed_url.query)
        if "v" not in parsed_query:
            raise NoVideoIDFoundError(url)
        video_id = parsed_query["v"][0]
    else:
        stripped_path = path.lstrip("/")
        if not stripped_path:
            raise NoVideoIDFoundError(url)
        video_id = stripped_path.split("/")[-1]

    if len(video_id) != 11:
        raise VideoIDError(video_id)

    return YouTubeVideoTarget(url=url, video_id=video_id)


def is_youtube_video_url(url: str) -> bool:
    try:
        parse_youtube_video_target(url)
    except (UnsupportedURLSchemeError, UnsupportedURLNetlocError, NoVideoIDFoundError, VideoIDError):
        return False
    return True


def parse_github_target(url: str) -> GitHubTarget:
    parsed = urlparse(url)
    if parsed.netloc == RAW_GITHUB_HOST:
        return GitHubTarget(url=url, raw_url=url)

    if parsed.netloc != GITHUB_HOST:
        raise InvalidURLError(url, "GitHub")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 5 and parts[2] == "blob":
        owner, repo, _, ref = parts[:4]
        path = "/".join(parts[4:])
        if not path:
            raise InvalidURLError(url, "GitHub blob file")
        return GitHubTarget(url=url, raw_url=f"https://{RAW_GITHUB_HOST}/{owner}/{repo}/{ref}/{path}")

    return GitHubTarget(url=url)


def parse_github_raw_content_target(url: str) -> GitHubTarget:
    target = parse_github_target(url)
    if target.raw_url is None:
        raise InvalidURLError(url, "GitHub blob")
    return target


def is_github_url(url: str) -> bool:
    try:
        parse_github_target(url)
    except InvalidURLError:
        return False
    return True


def parse_pdf_target(target: str) -> PDFTarget:
    parsed = urlparse(target)
    if parsed.scheme in {"http", "https"}:
        path = parsed.path.lower()
        if not path.endswith(".pdf") and not (parsed.netloc.lower() in ARXIV_HOSTS and path.startswith("/pdf/")):
            raise InvalidURLError(target, "PDF")
        return PDFTarget(target=target)

    if Path(target).suffix.lower() != ".pdf":
        raise InvalidURLError(target, "PDF")
    return PDFTarget(target=target)


def is_pdf_target(target: str) -> bool:
    try:
        parse_pdf_target(target)
    except InvalidURLError:
        return False
    return True


def _host(url: str) -> str:
    return urlparse(url).netloc.lower()


def _host_in(url: str, hosts: tuple[str, ...]) -> bool:
    return _host(url) in {host.lower() for host in hosts}


def _host_matches_domain_suffix(url: str, domain_suffix: str) -> bool:
    host = _host(url)
    normalized_suffix = domain_suffix.lower().lstrip(".")
    return host == normalized_suffix or host.endswith(f".{normalized_suffix}")


def parse_bbc_target(url: str) -> BBCTarget:
    if not _host_matches_domain_suffix(url, BBC_DOMAIN_SUFFIX):
        raise LoaderNotApplicableError(
            "BBCLoader",
            url,
            f"Not a BBC URL. Expected domain ending with {BBC_DOMAIN_SUFFIX}",
        )
    return BBCTarget(url=url)


def is_bbc_url(url: str) -> bool:
    try:
        parse_bbc_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_cnn_target(url: str) -> CNNTarget:
    if not _host_matches_domain_suffix(url, CNN_DOMAIN_SUFFIX):
        raise LoaderNotApplicableError(
            "CNNLoader",
            url,
            f"Not a CNN URL. Expected domain ending with {CNN_DOMAIN_SUFFIX}",
        )
    return CNNTarget(url=url)


def is_cnn_url(url: str) -> bool:
    try:
        parse_cnn_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def is_openai_web_url(url: str) -> bool:
    return _host_in(url, OPENAI_WEB_HOSTS)


def parse_ptt_target(url: str) -> PttTarget:
    if not _host_in(url, PTT_HOSTS):
        expected = ", ".join(PTT_HOSTS)
        raise LoaderNotApplicableError("PttLoader", url, f"Not a PTT URL. Expected domains: {expected}")
    return PttTarget(url=url)


def is_ptt_url(url: str) -> bool:
    try:
        parse_ptt_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_reddit_target(url: str) -> RedditTarget:
    if not _host_in(url, REDDIT_DOMAINS):
        expected = ", ".join(REDDIT_DOMAINS)
        raise LoaderNotApplicableError("RedditLoader", url, f"Not a Reddit URL. Expected domains: {expected}")
    return RedditTarget(url=url)


def is_reddit_url(url: str) -> bool:
    try:
        parse_reddit_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_reel_target(url: str) -> ReelTarget:
    if not url.startswith(REEL_PREFIX):
        raise LoaderNotApplicableError("ReelLoader", url, "Not an Instagram Reel URL")
    return ReelTarget(url=url)


def is_reel_url(url: str) -> bool:
    try:
        parse_reel_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_truthsocial_target(url: str) -> TruthSocialTarget:
    parsed = urlparse(url)
    if parsed.netloc.lower() not in TRUTHSOCIAL_DOMAINS:
        raise LoaderNotApplicableError("TruthSocialLoader", url, "Not a Truth Social URL")
    return TruthSocialTarget(url=url)


def is_truthsocial_url(url: str) -> bool:
    try:
        parse_truthsocial_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_twitter_target(url: str) -> TwitterTarget:
    parsed = urlparse(url)
    if parsed.netloc.lower() not in TWITTER_DOMAINS:
        raise LoaderNotApplicableError("TwitterLoader", url, "URL is not a Twitter/X URL")
    return TwitterTarget(url=url, normalized_url=str(urlunparse(parsed._replace(netloc="x.com"))))


def is_twitter_url(url: str) -> bool:
    try:
        parse_twitter_target(url)
    except LoaderNotApplicableError:
        return False
    return True


__all__ = [
    "BBC_DOMAIN_SUFFIX",
    "CNN_DOMAIN_SUFFIX",
    "OPENAI_WEB_HOSTS",
    "PTT_HOSTS",
    "REDDIT_DOMAINS",
    "REEL_PREFIX",
    "TRUTHSOCIAL_DOMAINS",
    "TWITTER_DOMAINS",
    "BBCTarget",
    "CNNTarget",
    "GitHubTarget",
    "NoVideoIDFoundError",
    "PDFTarget",
    "PttTarget",
    "RedditTarget",
    "ReelTarget",
    "TruthSocialTarget",
    "TwitterTarget",
    "UnsupportedURLNetlocError",
    "UnsupportedURLSchemeError",
    "VideoIDError",
    "YouTubeVideoTarget",
    "is_bbc_url",
    "is_cnn_url",
    "is_github_url",
    "is_openai_web_url",
    "is_pdf_target",
    "is_ptt_url",
    "is_reddit_url",
    "is_reel_url",
    "is_truthsocial_url",
    "is_twitter_url",
    "is_youtube_video_url",
    "parse_bbc_target",
    "parse_cnn_target",
    "parse_github_raw_content_target",
    "parse_github_target",
    "parse_pdf_target",
    "parse_ptt_target",
    "parse_reddit_target",
    "parse_reel_target",
    "parse_truthsocial_target",
    "parse_twitter_target",
    "parse_youtube_video_target",
    "require_loader_applicability",
]
