from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from enum import StrEnum


class AttemptStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"
    TIMEOUT = "timeout"
    EMPTY = "empty"
    REJECTED = "rejected"


@dataclass(frozen=True)
class AttemptRecord:
    loader_id: str
    status: AttemptStatus
    elapsed_seconds: float
    error_type: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class LoadResult:
    content: str
    loader_id: str
    content_type: str
    downgraded: bool
    attempts: tuple[AttemptRecord, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "content": self.content,
            "loader_id": self.loader_id,
            "content_type": self.content_type,
            "downgraded": self.downgraded,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


__all__ = ["AttemptRecord", "AttemptStatus", "LoadResult"]
