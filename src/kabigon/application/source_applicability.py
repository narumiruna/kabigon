from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlparse

from kabigon.domain.errors import InvalidURLError
from kabigon.domain.errors import KabigonError

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
RAW_GITHUB_HOST = "raw.githubusercontent.com"


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
        if not parsed.path.lower().endswith(".pdf"):
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


__all__ = [
    "GitHubTarget",
    "NoVideoIDFoundError",
    "PDFTarget",
    "UnsupportedURLNetlocError",
    "UnsupportedURLSchemeError",
    "VideoIDError",
    "YouTubeVideoTarget",
    "is_github_url",
    "is_pdf_target",
    "is_youtube_video_url",
    "parse_github_raw_content_target",
    "parse_github_target",
    "parse_pdf_target",
    "parse_youtube_video_target",
]
