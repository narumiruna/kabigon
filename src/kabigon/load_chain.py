from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderError
from kabigon.core.errors import LoaderNotApplicableError
from kabigon.core.errors import LoaderTimeoutError
from kabigon.core.errors import MissingRequirementError
from kabigon.core.execution import capture_attempts
from kabigon.core.execution import record_attempt
from kabigon.core.execution import remaining_seconds
from kabigon.core.loader import Loader
from kabigon.core.results import AttemptRecord
from kabigon.core.results import AttemptStatus
from kabigon.core.results import LoadResult
from kabigon.loader_registry import get_loader_content_type
from kabigon.loader_registry import get_loader_factory
from kabigon.loader_registry import get_loader_requirements
from kabigon.pipelines.catalog import GENERIC_HTML_LOADERS
from kabigon.pipelines.catalog import ContentContract
from kabigon.pipelines.catalog import ContentType
from kabigon.pipelines.catalog import plan_for_url

LoaderFactory = Callable[[], Loader]
Admission = Callable[[str, Callable[[], Awaitable[str]]], Awaitable[str]]
_EMPTY_EXECUTION_PLAN = "Load chain execution plan cannot be empty."
DEFAULT_FALLBACK_LOADERS = GENERIC_HTML_LOADERS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoadChainExplanation:
    url: str
    pipeline: str | None
    content_type: ContentType
    targeted_loaders: tuple[str, ...]
    fallback_loaders: tuple[str, ...]
    execution_plan: tuple[str, ...]
    requirements: tuple[str, ...] = ()
    missing_requirements: tuple[str, ...] = ()
    eligible_loaders: tuple[str, ...] = ()
    unavailable_loaders: tuple[str, ...] = ()
    content_contract: ContentContract = ContentContract.GENERIC_HTML

    def as_dict(self) -> dict[str, object]:
        return {
            "url": self.url,
            "pipeline": self.pipeline,
            "content_type": self.content_type,
            "targeted_loaders": list(self.targeted_loaders),
            "fallback_loaders": list(self.fallback_loaders),
            "execution_plan": list(self.execution_plan),
            "requirements": list(self.requirements),
            "missing_requirements": list(self.missing_requirements),
            "eligible_loaders": list(self.eligible_loaders),
            "unavailable_loaders": list(self.unavailable_loaders),
        }


@dataclass(frozen=True)
class LoadChain:
    get_factory: Callable[[str], LoaderFactory]
    explanation: LoadChainExplanation
    get_requirements: Callable[[str], tuple[str, ...]]
    get_content_type: Callable[[str], str]
    admit: Admission | None = None

    async def load_detailed(self) -> LoadResult:
        attempts: list[AttemptRecord] = []
        with capture_attempts(attempts):
            return await self._execute_detailed(attempts)

    async def _execute_detailed(self, attempts: list[AttemptRecord]) -> LoadResult:  # noqa: C901
        errors: list[str] = []

        for planned_loader_name in self.explanation.execution_plan:
            missing = _missing_requirements(self.get_requirements(planned_loader_name))
            if missing:
                message = f"Missing requirement(s): {', '.join(missing)}"
                errors.append(f"{planned_loader_name}: Skipped ({message})")
                attempt = AttemptRecord(
                    planned_loader_name, AttemptStatus.SKIPPED, 0.0, "MissingRequirementError", message
                )
                record_attempt(attempt)
                continue

            remaining = remaining_seconds()
            if remaining is not None and remaining <= 0:
                attempt = AttemptRecord(
                    planned_loader_name, AttemptStatus.TIMEOUT, 0.0, "TimeoutError", "Deadline expired"
                )
                record_attempt(attempt)
                errors.append(f"{planned_loader_name}: Deadline expired before attempt")
                break

            started = time.monotonic()
            try:
                loader = self.get_factory(planned_loader_name)()
                logger.debug("[%s] Attempting to load URL: %s", planned_loader_name, self.explanation.url)
                if self.admit is not None:
                    operation = self.admit(
                        planned_loader_name,
                        lambda active_loader=loader: active_loader.load(self.explanation.url),
                    )
                else:
                    operation = loader.load(self.explanation.url)
                if remaining is None:
                    result = await operation
                else:
                    async with asyncio.timeout(remaining):
                        result = await operation
            except LoaderNotApplicableError as error:
                message = error.reason or "not applicable"
                errors.append(f"{planned_loader_name}: Not applicable ({message})")
                self._append_attempt(planned_loader_name, AttemptStatus.NOT_APPLICABLE, started, error, message)
                continue
            except LoaderTimeoutError as error:
                errors.append(f"{planned_loader_name}: Timeout after {error.timeout}s")
                self._append_attempt(planned_loader_name, AttemptStatus.TIMEOUT, started, error, "Loader timed out")
                continue
            except TimeoutError as error:
                errors.append(f"{planned_loader_name}: Shared deadline expired")
                self._append_attempt(planned_loader_name, AttemptStatus.TIMEOUT, started, error, "Deadline expired")
                break
            except LoaderContentError as error:
                errors.append(f"{planned_loader_name}: Content extraction failed - {error.reason}")
                self._append_attempt(
                    planned_loader_name, AttemptStatus.FAILED, started, error, "Content extraction failed"
                )
                continue
            except asyncio.CancelledError:
                raise
            except Exception as error:  # noqa: BLE001
                errors.append(f"{planned_loader_name}: {type(error).__name__}: {error!s}")
                self._append_attempt(planned_loader_name, AttemptStatus.FAILED, started, error, "Loader failed")
                continue

            if not result or not result.strip():
                errors.append(f"{planned_loader_name}: Empty result")
                self._append_attempt(planned_loader_name, AttemptStatus.EMPTY, started, None, "Empty result")
                continue

            actual_type = ContentType(self.get_content_type(planned_loader_name))
            if (
                self.explanation.content_contract == ContentContract.SOURCE_REQUIRED
                and actual_type != self.explanation.content_type
            ):
                errors.append(f"{planned_loader_name}: Rejected content type {actual_type}")
                self._append_attempt(
                    planned_loader_name,
                    AttemptStatus.REJECTED,
                    started,
                    None,
                    "Result did not satisfy source content contract",
                )
                continue

            self._append_attempt(planned_loader_name, AttemptStatus.SUCCESS, started)
            return LoadResult(
                content=result,
                loader_id=planned_loader_name,
                content_type=actual_type,
                downgraded=(
                    self.explanation.content_type != ContentType.GENERIC_WEB and actual_type == ContentType.GENERIC_WEB
                ),
                attempts=tuple(attempts),
            )

        raise LoaderError(self.explanation.url, details=errors, attempts=tuple(attempts))

    @staticmethod
    def _append_attempt(
        loader_id: str,
        status: AttemptStatus,
        started: float,
        error: BaseException | None = None,
        message: str | None = None,
    ) -> None:
        attempt = AttemptRecord(
            loader_id=loader_id,
            status=status,
            elapsed_seconds=round(max(0.0, time.monotonic() - started), 6),
            error_type=type(error).__name__ if error is not None else None,
            message=message,
        )
        record_attempt(attempt)

    async def load(self) -> str:
        return (await self.load_detailed()).content

    def load_sync(self) -> str:
        return asyncio.run(self.load())


def _merge_unique_requirements(*requirement_groups: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(requirement for group in requirement_groups for requirement in group))


def _no_loader_requirements(_name: str) -> tuple[str, ...]:
    return ()


def _generic_content_type(_name: str) -> str:
    return ContentType.GENERIC_WEB


def _requirements_for_loaders(
    loader_names: tuple[str, ...], get_requirements: Callable[[str], tuple[str, ...]]
) -> tuple[str, ...]:
    return _merge_unique_requirements(*(get_requirements(name) for name in loader_names))


def _missing_requirements(requirements: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(name for name in requirements if not os.getenv(name))


def _build_explanation(
    url: str,
    *,
    pipeline_name: str | None,
    content_type: ContentType,
    content_contract: ContentContract,
    targeted_loaders: tuple[str, ...] = (),
    fallback_loaders: tuple[str, ...] = (),
    execution_plan: tuple[str, ...] | None = None,
    get_requirements: Callable[[str], tuple[str, ...]] = get_loader_requirements,
) -> LoadChainExplanation:
    loaders = (*targeted_loaders, *fallback_loaders) if execution_plan is None else execution_plan
    requirements = _requirements_for_loaders(loaders, get_requirements)
    eligible_loaders = tuple(name for name in loaders if not _missing_requirements(get_requirements(name)))
    unavailable_loaders = tuple(name for name in loaders if name not in eligible_loaders)
    return LoadChainExplanation(
        url=url,
        pipeline=pipeline_name,
        content_type=content_type,
        targeted_loaders=targeted_loaders,
        fallback_loaders=fallback_loaders,
        execution_plan=loaders,
        requirements=requirements,
        missing_requirements=_missing_requirements(requirements),
        eligible_loaders=eligible_loaders,
        unavailable_loaders=unavailable_loaders,
        content_contract=content_contract,
    )


def _ensure_any_eligible(explanation: LoadChainExplanation, get_requirements: Callable[[str], tuple[str, ...]]) -> None:
    if any(not _missing_requirements(get_requirements(name)) for name in explanation.execution_plan):
        return
    if explanation.missing_requirements:
        raise MissingRequirementError(explanation.missing_requirements)


def explain_load_chain(url: str) -> LoadChainExplanation:
    plan = plan_for_url(url)
    return _build_explanation(
        url,
        pipeline_name=plan.pipeline_name,
        content_type=plan.content_type,
        content_contract=plan.content_contract,
        targeted_loaders=plan.targeted_loaders,
        fallback_loaders=plan.fallback_loaders,
        execution_plan=plan.execution_plan,
    )


def resolve_load_chain(
    url: str,
    *,
    get_factory: Callable[[str], LoaderFactory] = get_loader_factory,
    get_requirements: Callable[[str], tuple[str, ...]] = get_loader_requirements,
    get_content_type: Callable[[str], str] = get_loader_content_type,
    admit: Admission | None = None,
) -> LoadChain:
    explanation = explain_load_chain(url)
    _ensure_any_eligible(explanation, get_requirements)
    return LoadChain(get_factory, explanation, get_requirements, get_content_type, admit)


def resolve_explicit_load_chain(
    url: str,
    loader_names: Sequence[str],
    get_factory: Callable[[str], LoaderFactory] = get_loader_factory,
    get_requirements: Callable[[str], tuple[str, ...]] | None = None,
    get_content_type: Callable[[str], str] | None = None,
    admit: Admission | None = None,
) -> LoadChain:
    execution_plan = tuple(loader_names)
    if not execution_plan:
        raise ValueError(_EMPTY_EXECUTION_PLAN)
    requirements_lookup = (
        (get_loader_requirements if get_factory is get_loader_factory else _no_loader_requirements)
        if get_requirements is None
        else get_requirements
    )
    content_type_lookup = (
        (get_loader_content_type if get_factory is get_loader_factory else _generic_content_type)
        if get_content_type is None
        else get_content_type
    )
    explanation = _build_explanation(
        url,
        pipeline_name=None,
        content_type=ContentType.GENERIC_WEB,
        content_contract=ContentContract.GENERIC_HTML,
        execution_plan=execution_plan,
        get_requirements=requirements_lookup,
    )
    _ensure_any_eligible(explanation, requirements_lookup)
    return LoadChain(get_factory, explanation, requirements_lookup, content_type_lookup, admit)


__all__ = [
    "DEFAULT_FALLBACK_LOADERS",
    "LoadChain",
    "LoadChainExplanation",
    "explain_load_chain",
    "resolve_explicit_load_chain",
    "resolve_load_chain",
]
