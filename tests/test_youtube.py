from kabigon.youtube import YoutubeLoader


def test_youtube_loader() -> None:
    url = "https://youtu.be/ZGEPXFDADm0"
    loader = YoutubeLoader()
    text = loader.load(url)
    assert isinstance(text, str)
    assert len(text) > 20
