from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedHtml:
    content: str
    content_type: str


__all__ = ["RetrievedHtml"]
