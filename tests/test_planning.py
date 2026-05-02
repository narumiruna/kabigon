from kabigon.application.pipeline_catalog import ContentType
from kabigon.application.pipeline_catalog import FallbackPolicy
from kabigon.application.planning import DEFAULT_FALLBACK_LOADERS
from kabigon.application.planning import RetrievalContext
from kabigon.application.planning import build_loader_plan
from kabigon.application.planning import build_retrieval_context


def test_build_retrieval_context_youtube() -> None:
    context = build_retrieval_context("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert context.pipeline_name == "youtube"
    assert context.content_type == ContentType.YOUTUBE_VIDEO
    assert context.targeted_loaders == ("youtube", "youtube-ytdlp")
    assert context.requirements == ()
    assert context.fallback_policy == FallbackPolicy.REMAINING_DEFAULT


def test_build_retrieval_context_unknown_is_generic_web() -> None:
    context = build_retrieval_context("https://example.com/some-page")

    assert context.pipeline_name is None
    assert context.content_type == ContentType.GENERIC_WEB
    assert context.targeted_loaders == ()
    assert context.requirements == ()
    assert context.fallback_policy == FallbackPolicy.REMAINING_DEFAULT


def test_build_retrieval_context_openai_web_disables_fallback() -> None:
    context = build_retrieval_context("https://openai.com/pricing")

    assert context.pipeline_name == "openai_web"
    assert context.content_type == ContentType.GENERIC_WEB
    assert context.targeted_loaders == ("firecrawl",)
    assert context.requirements == ("FIRECRAWL_API_KEY",)
    assert context.fallback_policy == FallbackPolicy.NO_FALLBACK


def test_build_loader_plan_deduplicates_targeted_and_fallback() -> None:
    context = RetrievalContext(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        pipeline_name="youtube",
        targeted_loaders=("youtube", "youtube-ytdlp"),
        content_type=ContentType.YOUTUBE_VIDEO,
    )

    plan = build_loader_plan(
        context=context,
        default_fallback=("youtube", "youtube-ytdlp", "playwright-fast"),
    )

    assert plan.loader_names == ("youtube", "youtube-ytdlp", "playwright-fast")


def test_build_loader_plan_for_generic_web_uses_default_order() -> None:
    context = build_retrieval_context("https://example.com/hello")
    plan = build_loader_plan(context)

    assert plan.loader_names == DEFAULT_FALLBACK_LOADERS


def test_build_loader_plan_for_no_fallback_pipeline_uses_targeted_only() -> None:
    context = build_retrieval_context("https://openai.com/pricing")
    plan = build_loader_plan(context)

    assert plan.loader_names == ("firecrawl",)
