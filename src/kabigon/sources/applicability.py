from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from pathlib import PureWindowsPath
from urllib.parse import parse_qs
from urllib.parse import unquote
from urllib.parse import urlparse
from urllib.parse import urlunparse

from kabigon.core.errors import InvalidURLError
from kabigon.core.errors import KabigonError
from kabigon.core.errors import LoaderNotApplicableError

BBC_DOMAIN_SUFFIX = "bbc.com"
CNN_DOMAIN_SUFFIX = "cnn.com"
LTN_DOMAIN_SUFFIX = "ltn.com.tw"
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
PI_SESSION_HOST = "pi.dev"
PI_SESSION_PATH = "/session"
PTT_HOSTS = ("www.ptt.cc",)
RAW_GITHUB_HOST = "raw.githubusercontent.com"
REDDIT_DOMAINS = (
    "reddit.com",
    "www.reddit.com",
    "old.reddit.com",
    "new.reddit.com",
    "np.reddit.com",
    "m.reddit.com",
    "sh.reddit.com",
    "redd.it",
    "www.redd.it",
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
class PiSessionTarget:
    url: str
    gist_id: str
    file_name: str
    leaf_id: str | None = None
    target_id: str | None = None


@dataclass(frozen=True)
class TwitterTarget:
    url: str
    normalized_url: str
    status_id: str | None = None


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


def parse_pi_session_target(url: str) -> PiSessionTarget:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != PI_SESSION_HOST:
        raise LoaderNotApplicableError("PiSessionLoader", url, "Not a pi.dev shared session URL")
    if parsed.path.rstrip("/") != PI_SESSION_PATH:
        raise LoaderNotApplicableError("PiSessionLoader", url, "Not a pi.dev shared session path")

    shared_path = parsed.fragment or parsed.query
    session_path, _, raw_params = shared_path.partition("&")
    gist_id, separator, encoded_file_name = session_path.partition("/")
    if not gist_id or any(character not in "0123456789abcdefABCDEF" for character in gist_id):
        raise LoaderNotApplicableError("PiSessionLoader", url, "Missing or invalid shared session ID")

    file_name = unquote(encoded_file_name) if separator and encoded_file_name else "session.html"
    params = parse_qs(raw_params, keep_blank_values=True)
    return PiSessionTarget(
        url=url,
        gist_id=gist_id,
        file_name=file_name,
        leaf_id=params.get("leafId", [None])[0],
        target_id=params.get("targetId", [None])[0],
    )


def is_pi_session_url(url: str) -> bool:
    try:
        parse_pi_session_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_pdf_target(target: str) -> str:
    parsed = urlparse(target)
    if parsed.scheme in {"http", "https"}:
        path = parsed.path.lower()
        if not path.endswith(".pdf") and not (parsed.netloc.lower() in ARXIV_HOSTS and path.startswith("/pdf/")):
            raise InvalidURLError(target, "PDF")
        return target

    if parsed.scheme and not PureWindowsPath(target).is_absolute():
        raise InvalidURLError(target, "PDF")
    if Path(target).suffix.lower() != ".pdf":
        raise InvalidURLError(target, "PDF")
    return target


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


def parse_bbc_target(url: str) -> str:
    if not _host_matches_domain_suffix(url, BBC_DOMAIN_SUFFIX):
        raise LoaderNotApplicableError(
            "BBCLoader",
            url,
            f"Not a BBC URL. Expected domain ending with {BBC_DOMAIN_SUFFIX}",
        )
    return url


def is_bbc_url(url: str) -> bool:
    try:
        parse_bbc_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_cnn_target(url: str) -> str:
    if not _host_matches_domain_suffix(url, CNN_DOMAIN_SUFFIX):
        raise LoaderNotApplicableError(
            "CNNLoader",
            url,
            f"Not a CNN URL. Expected domain ending with {CNN_DOMAIN_SUFFIX}",
        )
    return url


def is_cnn_url(url: str) -> bool:
    try:
        parse_cnn_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_ltn_target(url: str) -> str:
    if not _host_matches_domain_suffix(url, LTN_DOMAIN_SUFFIX):
        raise LoaderNotApplicableError(
            "LTNLoader",
            url,
            f"Not an LTN URL. Expected domain ending with {LTN_DOMAIN_SUFFIX}",
        )
    return url


def is_ltn_url(url: str) -> bool:
    try:
        parse_ltn_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def is_openai_web_url(url: str) -> bool:
    return _host_in(url, OPENAI_WEB_HOSTS)


def parse_ptt_target(url: str) -> str:
    if not _host_in(url, PTT_HOSTS):
        expected = ", ".join(PTT_HOSTS)
        raise LoaderNotApplicableError("PttLoader", url, f"Not a PTT URL. Expected domains: {expected}")
    return url


def is_ptt_url(url: str) -> bool:
    try:
        parse_ptt_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_reddit_target(url: str) -> str:
    if not _host_in(url, REDDIT_DOMAINS):
        expected = ", ".join(REDDIT_DOMAINS)
        raise LoaderNotApplicableError("RedditLoader", url, f"Not a Reddit URL. Expected domains: {expected}")
    return url


def is_reddit_url(url: str) -> bool:
    try:
        parse_reddit_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_reel_target(url: str) -> str:
    if not url.startswith(REEL_PREFIX):
        raise LoaderNotApplicableError("ReelLoader", url, "Not an Instagram Reel URL")
    return url


def is_reel_url(url: str) -> bool:
    try:
        parse_reel_target(url)
    except LoaderNotApplicableError:
        return False
    return True


def parse_truthsocial_target(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.lower() not in TRUTHSOCIAL_DOMAINS:
        raise LoaderNotApplicableError("TruthSocialLoader", url, "Not a Truth Social URL")
    return url


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
    match = re.search(r"/status/([0-9]+)(?:/|$)", parsed.path)
    return TwitterTarget(
        url=url,
        normalized_url=str(urlunparse(parsed._replace(netloc="x.com"))),
        status_id=match.group(1) if match else None,
    )


def is_twitter_status_url(url: str) -> bool:
    try:
        return parse_twitter_target(url).status_id is not None
    except LoaderNotApplicableError:
        return False


def is_twitter_url(url: str) -> bool:
    try:
        parse_twitter_target(url)
    except LoaderNotApplicableError:
        return False
    return True


__all__ = [
    "BBC_DOMAIN_SUFFIX",
    "CNN_DOMAIN_SUFFIX",
    "LTN_DOMAIN_SUFFIX",
    "OPENAI_WEB_HOSTS",
    "PI_SESSION_HOST",
    "PI_SESSION_PATH",
    "PTT_HOSTS",
    "REDDIT_DOMAINS",
    "REEL_PREFIX",
    "TRUTHSOCIAL_DOMAINS",
    "TWITTER_DOMAINS",
    "GitHubTarget",
    "NoVideoIDFoundError",
    "PiSessionTarget",
    "TwitterTarget",
    "UnsupportedURLNetlocError",
    "UnsupportedURLSchemeError",
    "VideoIDError",
    "YouTubeVideoTarget",
    "is_bbc_url",
    "is_cnn_url",
    "is_github_url",
    "is_ltn_url",
    "is_openai_web_url",
    "is_pdf_target",
    "is_pi_session_url",
    "is_ptt_url",
    "is_reddit_url",
    "is_reel_url",
    "is_truthsocial_url",
    "is_twitter_status_url",
    "is_twitter_url",
    "is_youtube_video_url",
    "parse_bbc_target",
    "parse_cnn_target",
    "parse_github_raw_content_target",
    "parse_github_target",
    "parse_ltn_target",
    "parse_pdf_target",
    "parse_pi_session_target",
    "parse_ptt_target",
    "parse_reddit_target",
    "parse_reel_target",
    "parse_truthsocial_target",
    "parse_twitter_target",
    "parse_youtube_video_target",
    "require_loader_applicability",
]
