import asyncio

import pytest

from kabigon.core.errors import LoaderContentError
from kabigon.core.errors import LoaderError
from kabigon.core.loader import Loader
from kabigon.core.results import AttemptRecord
from kabigon.core.results import AttemptStatus
from kabigon.core.results import LoadResult
from kabigon.core.retrieval import RetrievedHtml
from kabigon.load_chain import resolve_explicit_load_chain
from kabigon.loaders import curl_cffi as curl_module
from kabigon.loaders import news_article as news_module
from kabigon.loaders.bbc import BBCLoader


class EmptyLoader(Loader):
    async def load(self, url: str) -> str:
        return "   "


class SuccessLoader(Loader):
    async def load(self, url: str) -> str:
        return "content"


def test_result_serialization_is_stable_and_credential_free() -> None:
    result = LoadResult(
        content="body",
        loader_id="httpx",
        content_type="generic_web",
        downgraded=False,
        attempts=(AttemptRecord("httpx", AttemptStatus.SUCCESS, 0.25),),
    )

    assert result.to_dict() == {
        "content": "body",
        "loader_id": "httpx",
        "content_type": "generic_web",
        "downgraded": False,
        "attempts": [
            {
                "loader_id": "httpx",
                "status": "success",
                "elapsed_seconds": 0.25,
                "error_type": None,
                "message": None,
            }
        ],
    }
    assert "header" not in str(result.to_dict()).lower()


def test_detailed_chain_preserves_partial_failures_and_registry_id() -> None:
    chain = resolve_explicit_load_chain(
        "https://example.com",
        ("empty", "playwright-fast"),
        {"empty": EmptyLoader, "playwright-fast": SuccessLoader}.__getitem__,
        get_content_type=lambda _name: "generic_web",
    )

    result = asyncio.run(chain.load_detailed())

    assert result.content == "content"
    assert result.loader_id == "playwright-fast"
    assert [attempt.loader_id for attempt in result.attempts] == ["empty", "playwright-fast"]
    assert [attempt.status for attempt in result.attempts] == [AttemptStatus.EMPTY, AttemptStatus.SUCCESS]


def test_news_transport_subattempts_use_stable_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail_httpx(*_args, **_kwargs) -> str:
        raise LoaderContentError("BBCLoader", "https://www.bbc.com/news/article", "failed")

    async def curl_success(*_args, **_kwargs) -> RetrievedHtml:
        return RetrievedHtml("<article><p>BBC body</p></article>", "text/html")

    monkeypatch.setattr(news_module, "fetch_news_article_html", fail_httpx)
    monkeypatch.setattr(curl_module, "fetch_curl_html", curl_success)
    chain = resolve_explicit_load_chain(
        "https://www.bbc.com/news/article",
        ("bbc",),
        {"bbc": BBCLoader}.__getitem__,
        get_content_type=lambda _name: "news_article",
    )

    result = asyncio.run(chain.load_detailed())

    assert [attempt.loader_id for attempt in result.attempts] == ["bbc:httpx", "bbc:curl-cffi", "bbc"]
    assert result.content_type == "news_article"


def test_all_failed_error_retains_structured_attempts() -> None:
    chain = resolve_explicit_load_chain(
        "https://example.com",
        ("playwright-networkidle", "playwright-fast"),
        {"playwright-networkidle": EmptyLoader, "playwright-fast": EmptyLoader}.__getitem__,
        get_content_type=lambda _name: "generic_web",
    )

    with pytest.raises(LoaderError) as exc_info:
        asyncio.run(chain.load_detailed())

    attempts = exc_info.value.attempts
    assert [attempt.loader_id for attempt in attempts] == ["playwright-networkidle", "playwright-fast"]
