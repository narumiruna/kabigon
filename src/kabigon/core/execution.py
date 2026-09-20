from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from contextvars import Token

from .results import AttemptRecord

type BlockingRunner = Callable[[Callable[[], str]], Awaitable[str]]

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


async def run_blocking_operation(operation: Callable[[], str], runner: BlockingRunner | None = None) -> str:
    if runner is not None:
        return await runner(operation)
    return await asyncio.to_thread(operation)


@contextmanager
def capture_attempts(value: list[AttemptRecord]) -> Iterator[None]:
    token = _attempts.set(value)
    try:
        yield
    finally:
        _attempts.reset(token)


def record_attempt(record: AttemptRecord) -> None:
    sink = _attempts.get()
    if sink is not None:
        sink.append(record)


__all__ = [
    "BlockingRunner",
    "capture_attempts",
    "record_attempt",
    "remaining_seconds",
    "reset_deadline",
    "run_blocking_operation",
    "set_deadline",
]
