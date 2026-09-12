from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from contextvars import Token

from .results import AttemptRecord

_deadline: ContextVar[float | None] = ContextVar("kabigon_deadline", default=None)
_attempts: ContextVar[list[AttemptRecord] | None] = ContextVar("kabigon_attempts", default=None)


def set_deadline(value: float | None) -> Token[float | None]:
    return _deadline.set(value)


def reset_deadline(token: Token[float | None]) -> None:
    _deadline.reset(token)


def remaining_seconds() -> float | None:
    deadline = _deadline.get()
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


@contextmanager
def capture_attempts(value: list[AttemptRecord]) -> Iterator[None]:
    token = _attempts.set(value)
    try:
        yield
    finally:
        _attempts.reset(token)


def set_attempt_sink(value: list[AttemptRecord]) -> Token[list[AttemptRecord] | None]:
    return _attempts.set(value)


def reset_attempt_sink(token: Token[list[AttemptRecord] | None]) -> None:
    _attempts.reset(token)


def record_attempt(record: AttemptRecord) -> None:
    sink = _attempts.get()
    if sink is not None:
        sink.append(record)


__all__ = [
    "capture_attempts",
    "record_attempt",
    "remaining_seconds",
    "reset_attempt_sink",
    "reset_deadline",
    "set_attempt_sink",
    "set_deadline",
]
