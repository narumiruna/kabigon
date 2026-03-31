from kabigon.routing import route_url_to_pipeline_names


def test_route_url_to_pipeline_names_youtube() -> None:
    names = route_url_to_pipeline_names("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert names == ["youtube", "youtube-ytdlp"]


def test_route_url_to_pipeline_names_reddit() -> None:
    names = route_url_to_pipeline_names("https://www.reddit.com/r/python/comments/abc/example/")
    assert names == ["reddit"]


def test_route_url_to_pipeline_names_unknown() -> None:
    names = route_url_to_pipeline_names("https://example.com/path")
    assert names == []
