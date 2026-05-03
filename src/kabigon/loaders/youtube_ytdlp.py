import asyncio
import logging
from collections.abc import Callable

from kabigon.core.loader import Loader
from kabigon.sources.applicability import parse_youtube_video_target
from kabigon.sources.applicability import require_loader_applicability

from .ytdlp import YtdlpLoader

type LoaderFactory = Callable[[], Loader]

logger = logging.getLogger(__name__)


class YoutubeYtdlpLoader(Loader):
    def __init__(self, ytdlp_loader_factory: LoaderFactory = YtdlpLoader) -> None:
        self.ytdlp_loader_factory = ytdlp_loader_factory

    def load_sync(self, url: str) -> str:
        logger.info("[YoutubeYtdlpLoader] Processing URL: %s", url)
        require_loader_applicability("YoutubeYtdlpLoader", url, parse_youtube_video_target)
        logger.info("[YoutubeYtdlpLoader] Loading YouTube audio transcript with YtdlpLoader")
        result = self.ytdlp_loader_factory().load_sync(url)
        logger.info("[YoutubeYtdlpLoader] Extracted transcript content (%s chars)", len(result))
        return result

    async def load(self, url: str) -> str:
        return await asyncio.to_thread(self.load_sync, url)
