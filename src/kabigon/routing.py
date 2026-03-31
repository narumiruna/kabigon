from __future__ import annotations

from .pipelines import resolve_targeted_loader_names


def route_url_to_pipeline_names(url: str) -> list[str]:
    """Backward-compatible wrapper around pipeline routing."""
    return resolve_targeted_loader_names(url)
