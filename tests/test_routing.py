from kabigon.application.routing import resolve_targeted_loader_names


def test_route_url_to_pipeline_names_youtube() -> None:
    names = resolve_targeted_loader_names("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert names == ["youtube", "youtube-ytdlp"]


def test_route_url_to_pipeline_names_reddit() -> None:
    names = resolve_targeted_loader_names("https://www.reddit.com/r/python/comments/abc/example/")
    assert names == ["reddit"]


def test_route_url_to_pipeline_names_unknown() -> None:
    names = resolve_targeted_loader_names("https://example.com/path")
    assert names == []


def test_route_url_to_pipeline_names_non_http_is_pdf() -> None:
    names = resolve_targeted_loader_names("/tmp/demo.pdf")
    assert names == ["pdf"]


def test_route_url_to_pipeline_names_github_pdf_prefers_github_rule() -> None:
    names = resolve_targeted_loader_names("https://github.com/a/b/blob/main/demo.pdf")
    assert names == ["github"]


def test_route_url_to_pipeline_names_openai_web() -> None:
    names = resolve_targeted_loader_names("https://openai.com/pricing")
    assert names == ["firecrawl", "playwright-fast"]


def test_route_url_to_pipeline_names_platform_openai_web() -> None:
    names = resolve_targeted_loader_names("https://platform.openai.com/docs/pricing")
    assert names == ["firecrawl", "playwright-fast"]


def test_route_url_to_pipeline_names_help_openai_web() -> None:
    names = resolve_targeted_loader_names("https://help.openai.com/en/articles/20001106-codex-rate-card")
    assert names == ["firecrawl", "playwright-fast"]


def test_route_url_to_pipeline_names_developers_openai_is_not_openai_web() -> None:
    names = resolve_targeted_loader_names("https://developers.openai.com/codex/pricing")
    assert names == []
