from kabigon.application.load_chain import DEFAULT_FALLBACK_LOADERS
from kabigon.application.load_chain import resolve_load_chain
from kabigon.application.pipeline_catalog import ContentType
from kabigon.loaders.compose import Compose
from kabigon.loaders.firecrawl import FirecrawlLoader


def test_load_chain_explains_youtube_decision() -> None:
    chain = resolve_load_chain("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert isinstance(chain.loader, Compose)
    assert chain.explanation.pipeline == "youtube"
    assert chain.explanation.content_type == ContentType.YOUTUBE_VIDEO
    assert chain.explanation.targeted_loaders == ("youtube", "youtube-ytdlp")
    assert chain.explanation.execution_plan[:2] == ("youtube", "youtube-ytdlp")
    assert chain.explanation.requirements == ()


def test_load_chain_explains_generic_web_default_order() -> None:
    chain = resolve_load_chain("https://example.com/some-page")

    assert isinstance(chain.loader, Compose)
    assert chain.explanation.pipeline is None
    assert chain.explanation.content_type == ContentType.GENERIC_WEB
    assert chain.explanation.targeted_loaders == ()
    assert chain.explanation.execution_plan == DEFAULT_FALLBACK_LOADERS


def test_load_chain_deduplicates_targeted_loaders_from_fallback() -> None:
    chain = resolve_load_chain("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert chain.explanation.execution_plan.count("youtube") == 1
    assert chain.explanation.execution_plan.count("youtube-ytdlp") == 1


def test_load_chain_for_no_fallback_pipeline_builds_single_loader(monkeypatch) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")

    chain = resolve_load_chain("https://openai.com/pricing")

    assert isinstance(chain.loader, FirecrawlLoader)
    assert chain.explanation.pipeline == "openai_web"
    assert chain.explanation.execution_plan == ("firecrawl",)
    assert chain.explanation.requirements == ("FIRECRAWL_API_KEY",)


def test_load_chain_explanation_as_dict_uses_public_shapes() -> None:
    explanation = resolve_load_chain("https://www.youtube.com/watch?v=dQw4w9WgXcQ").explanation

    assert explanation.as_dict() == {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "pipeline": "youtube",
        "content_type": ContentType.YOUTUBE_VIDEO,
        "targeted_loaders": ["youtube", "youtube-ytdlp"],
        "execution_plan": list(explanation.execution_plan),
        "requirements": [],
    }
