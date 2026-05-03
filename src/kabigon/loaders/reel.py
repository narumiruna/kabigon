import logging
from collections.abc import Callable

from kabigon.core.loader import Loader
from kabigon.sources.applicability import parse_reel_target

from .httpx import HttpxLoader
from .ytdlp import YtdlpLoader

type LoaderFactory = Callable[[], Loader]

logger = logging.getLogger(__name__)


def check_reel_url(url: str) -> None:
    parse_reel_target(url)


class ReelLoader(Loader):
    def __init__(
        self,
        ytdlp_loader_factory: LoaderFactory = YtdlpLoader,
        httpx_loader_factory: LoaderFactory = HttpxLoader,
    ) -> None:
        self.ytdlp_loader_factory = ytdlp_loader_factory
        self.httpx_loader_factory = httpx_loader_factory

    async def load(self, url: str) -> str:
        logger.info("[ReelLoader] Processing URL: %s", url)
        parse_reel_target(url)

        logger.info("[ReelLoader] Loading audio with YtdlpLoader")
        audio_content = await self.ytdlp_loader_factory().load(url)
        logger.info("[ReelLoader] Loading HTML with HttpxLoader")
        html_content = await self.httpx_loader_factory().load(url)

        result = f"{audio_content}\n\n{html_content}"
        logger.info("[ReelLoader] Extracted combined reel content (%s chars)", len(result))
        return result
