import pytest

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderError
from kabigon.core.errors import LoaderNotApplicableError
from kabigon.core.errors import LoaderTimeoutError
from kabigon.core.errors import MissingRequirementError
from kabigon.core.loader import Loader
from kabigon.load_chain import DEFAULT_FALLBACK_LOADERS
from kabigon.load_chain import explain_load_chain
from kabigon.load_chain import resolve_explicit_load_chain
from kabigon.load_chain import resolve_load_chain
from kabigon.pipelines.catalog import ContentType


class EmptyLoader(Loader):
    async def load(self, url: str) -> str:
        return ""


class SuccessLoader(Loader):
    async def load(self, url: str) -> str:
        return f"loaded {url}"


class NotApplicableLoader(Loader):
    async def load(self, url: str) -> str:
        raise LoaderNotApplicableError("NotApplicableLoader", url, "unsupported domain")


class TimeoutLoader(Loader):
    async def load(self, url: str) -> str:
        raise LoaderTimeoutError("TimeoutLoader", url, 3.0)


class ContentFailLoader(Loader):
    async def load(self, url: str) -> str:
        raise LoaderContentError("ContentFailLoader", url, "parse failed")


class ConstructorFailLoader(Loader):
    def __init__(self) -> None:
        raise RuntimeError("constructor failed")

    async def load(self, url: str) -> str:
        return "should not load"


def test_load_chain_explains_youtube_decision() -> None:
    explanation = explain_load_chain("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert explanation.pipeline == "youtube"
    assert explanation.content_type == ContentType.YOUTUBE_VIDEO
    assert explanation.targeted_loaders == ("youtube", "youtube-ytdlp")
    assert explanation.execution_plan[:2] == ("youtube", "youtube-ytdlp")
    assert explanation.requirements == ()


def test_load_chain_explains_generic_web_default_order() -> None:
    explanation = explain_load_chain("https://example.com/some-page")

    assert explanation.pipeline is None
    assert explanation.content_type == ContentType.GENERIC_WEB
    assert explanation.targeted_loaders == ()
    assert explanation.execution_plan == DEFAULT_FALLBACK_LOADERS


def test_load_chain_deduplicates_targeted_loaders_from_fallback() -> None:
    explanation = explain_load_chain("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert explanation.execution_plan.count("youtube") == 1
    assert explanation.execution_plan.count("youtube-ytdlp") == 1


def test_load_chain_for_no_fallback_pipeline_builds_single_loader(monkeypatch) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")

    chain = resolve_load_chain("https://openai.com/pricing")

    assert chain.explanation.pipeline == "openai_web"
    assert chain.explanation.execution_plan == ("firecrawl",)
    assert chain.explanation.requirements == ("FIRECRAWL_API_KEY",)
    assert chain.explanation.missing_requirements == ()


def test_load_chain_runs_explanation_url() -> None:
    chain = resolve_explicit_load_chain("https://example.com", ("success",), {"success": SuccessLoader}.__getitem__)

    assert chain.load_sync() == "loaded https://example.com"


def test_explicit_load_chain_uses_shared_attempt_runtime() -> None:
    chain = resolve_explicit_load_chain(
        "https://example.com",
        ("empty", "success"),
        {"empty": EmptyLoader, "success": SuccessLoader}.__getitem__,
    )

    assert chain.explanation.execution_plan == ("empty", "success")
    assert chain.load_sync() == "loaded https://example.com"


def test_load_chain_builds_loaders_only_when_attempted() -> None:
    built: list[str] = []

    def factory(name: str) -> type[Loader]:
        built.append(name)
        if name == "success":
            return SuccessLoader
        raise AssertionError(f"unexpected loader build: {name}")

    chain = resolve_explicit_load_chain("https://example.com", ("success", "heavy-fallback"), factory)

    assert chain.load_sync() == "loaded https://example.com"
    assert built == ["success"]


def test_load_chain_records_constructor_failure_and_continues() -> None:
    chain = resolve_explicit_load_chain(
        "https://example.com",
        ("constructor-fail", "success"),
        {"constructor-fail": ConstructorFailLoader, "success": SuccessLoader}.__getitem__,
    )

    assert chain.load_sync() == "loaded https://example.com"


def test_load_chain_records_failed_attempt_details() -> None:
    chain = resolve_explicit_load_chain(
        "https://example.com",
        ("not-applicable", "timeout", "content-fail", "empty"),
        {
            "not-applicable": NotApplicableLoader,
            "timeout": TimeoutLoader,
            "content-fail": ContentFailLoader,
            "empty": EmptyLoader,
        }.__getitem__,
    )

    with pytest.raises(LoaderError) as exc_info:
        chain.load_sync()

    error = exc_info.value
    assert error.url == "https://example.com"
    assert error.details
    assert "NotApplicableLoader: Not applicable (unsupported domain)" in error.details
    assert "TimeoutLoader: Timeout after 3.0s" in error.details
    assert "ContentFailLoader: Content extraction failed - parse failed" in error.details
    assert "EmptyLoader: Empty result" in error.details
    assert "Attempted loaders:" in str(error)


def test_explain_load_chain_does_not_build_loader_for_missing_requirement(monkeypatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    explanation = explain_load_chain("https://openai.com/pricing")

    assert explanation.pipeline == "openai_web"
    assert explanation.execution_plan == ("firecrawl",)
    assert explanation.requirements == ("FIRECRAWL_API_KEY",)
    assert explanation.missing_requirements == ("FIRECRAWL_API_KEY",)


def test_resolve_load_chain_checks_requirements_before_building_loader(monkeypatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    with pytest.raises(MissingRequirementError, match="FIRECRAWL_API_KEY"):
        resolve_load_chain("https://openai.com/pricing")


def test_load_chain_explanation_as_dict_uses_public_shapes() -> None:
    explanation = explain_load_chain("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert explanation.as_dict() == {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "pipeline": "youtube",
        "content_type": ContentType.YOUTUBE_VIDEO,
        "targeted_loaders": ["youtube", "youtube-ytdlp"],
        "execution_plan": list(explanation.execution_plan),
        "requirements": [],
        "missing_requirements": [],
    }
