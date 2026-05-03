import pytest

from kabigon.core.errors import LoaderNotApplicableError
from kabigon.core.loader import Loader
from kabigon.loaders.youtube_ytdlp import YoutubeYtdlpLoader


class UnexpectedLoader(Loader):
    def __init__(self) -> None:
        raise AssertionError("heavy loader should not be built")

    async def load(self, url: str) -> str:
        return "should not load"


def test_youtube_ytdlp_checks_source_applicability_before_heavy_setup() -> None:
    loader = YoutubeYtdlpLoader(ytdlp_loader_factory=UnexpectedLoader)

    with pytest.raises(LoaderNotApplicableError):
        loader.load_sync("https://example.com/not-youtube")
