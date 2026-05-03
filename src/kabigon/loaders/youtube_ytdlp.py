import asyncio
from collections.abc import Callable

from kabigon.core.errors import LoaderNotApplicableError
from kabigon.core.loader import Loader

from .youtube import NoVideoIDFoundError
from .youtube import UnsupportedURLNetlocError
from .youtube import UnsupportedURLSchemeError
from .youtube import VideoIDError
from .youtube import parse_video_id
from .ytdlp import YtdlpLoader

type LoaderFactory = Callable[[], Loader]


class YoutubeYtdlpLoader(Loader):
    def __init__(self, ytdlp_loader_factory: LoaderFactory = YtdlpLoader) -> None:
        self.ytdlp_loader_factory = ytdlp_loader_factory

    def load_sync(self, url: str) -> str:
        try:
            parse_video_id(url)
        except (UnsupportedURLSchemeError, UnsupportedURLNetlocError, NoVideoIDFoundError, VideoIDError) as e:
            raise LoaderNotApplicableError("YoutubeYtdlpLoader", url, str(e)) from e
        return self.ytdlp_loader_factory().load_sync(url)

    async def load(self, url: str) -> str:
        return await asyncio.to_thread(self.load_sync, url)
