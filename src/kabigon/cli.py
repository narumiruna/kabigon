from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import typer

from kabigon import loaders
from kabigon.api import load_url_sync
from kabigon.core.loader import Loader


@dataclass(frozen=True)
class LoaderSpec:
    name: str
    description: str
    factory: Callable[[], Loader]


LOADER_SPECS: list[LoaderSpec] = [
    LoaderSpec("playwright", "Browser-based scraping for any website", lambda: loaders.PlaywrightLoader()),
    LoaderSpec("httpx", "Simple HTTP fetch + HTML to markdown", lambda: loaders.HttpxLoader()),
    LoaderSpec("firecrawl", "Firecrawl-based web extraction", lambda: loaders.FirecrawlLoader()),
    LoaderSpec("youtube", "Extracts YouTube video transcripts", lambda: loaders.YoutubeLoader()),
    LoaderSpec("youtube-ytdlp", "YouTube audio transcription via yt-dlp + Whisper", lambda: loaders.YoutubeYtdlpLoader()),
    LoaderSpec("ytdlp", "Audio transcription via yt-dlp + Whisper", lambda: loaders.YtdlpLoader()),
    LoaderSpec("twitter", "Extracts Twitter/X post content", lambda: loaders.TwitterLoader()),
    LoaderSpec("truthsocial", "Extracts Truth Social posts", lambda: loaders.TruthSocialLoader()),
    LoaderSpec("reddit", "Extracts Reddit posts and comments", lambda: loaders.RedditLoader()),
    LoaderSpec("ptt", "Taiwan PTT forum posts", lambda: loaders.PttLoader()),
    LoaderSpec("reel", "Instagram Reels audio transcription + metadata", lambda: loaders.ReelLoader()),
    LoaderSpec("github", "Fetches GitHub pages and file content", lambda: loaders.GitHubLoader()),
    LoaderSpec("pdf", "Extracts text from PDF files", lambda: loaders.PDFLoader()),
]

app = typer.Typer(add_completion=False)


def _loader_registry() -> dict[str, LoaderSpec]:
    return {spec.name: spec for spec in LOADER_SPECS}


def _parse_loader_names(raw: str) -> list[str]:
    names = [name.strip() for name in raw.split(",") if name.strip()]
    if not names:
        raise typer.BadParameter("Loader list cannot be empty.")
    registry = _loader_registry()
    unknown = [name for name in names if name not in registry]
    if unknown:
        hint = ", ".join(unknown)
        raise typer.BadParameter(f"Unknown loader(s): {hint}. Use --list to see supported loaders.")
    return names


def _load_with_loader_names(names: list[str], url: str) -> str:
    registry = _loader_registry()
    loaders_chain = [registry[name].factory() for name in names]
    if len(loaders_chain) == 1:
        return loaders_chain[0].load_sync(url)
    return loaders.Compose(loaders_chain).load_sync(url)


def _print_loader_list() -> None:
    for spec in LOADER_SPECS:
        typer.echo(f"{spec.name} - {spec.description}")


@app.callback(invoke_without_command=True)
def main(
    url: str | None = typer.Argument(None, metavar="URL"),
    loader: str | None = typer.Option(None, "--loader", help="Comma-separated loader names"),
    list_: bool = typer.Option(False, "--list", help="List supported loaders"),
) -> None:
    if list_:
        if url is not None or loader is not None:
            raise typer.BadParameter("--list cannot be combined with URL or --loader.")
        _print_loader_list()
        return

    if url is None:
        raise typer.BadParameter("URL is required unless --list is used.")

    if loader is None:
        result = load_url_sync(url)
        typer.echo(result)
        return

    names = _parse_loader_names(loader)
    result = _load_with_loader_names(names, url)
    typer.echo(result)


def run(url: str) -> None:
    result = load_url_sync(url)
    typer.echo(result)
