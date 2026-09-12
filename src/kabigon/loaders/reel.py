import logging
from collections.abc import Awaitable
from collections.abc import Callable

from kabigon.core.loader import Loader
from kabigon.core.resources import ResourceProvider
from kabigon.sources.applicability import parse_reel_target

from .httpx import HttpxLoader
from .ytdlp import ModelProvider
from .ytdlp import YtdlpLoader

type LoaderFactory = Callable[[], Loader]

logger = logging.getLogger(__name__)


class ReelLoader(Loader):
    def __init__(
        self,
        ytdlp_loader_factory: LoaderFactory = YtdlpLoader,
        httpx_loader_factory: LoaderFactory = HttpxLoader,
        resource_provider: ResourceProvider | None = None,
        run_blocking: Callable[[Callable[[], str]], Awaitable[str]] | None = None,
        model_provider: ModelProvider | None = None,
    ) -> None:
        self.ytdlp_loader_factory = ytdlp_loader_factory
        self.httpx_loader_factory = httpx_loader_factory
        self.resource_provider = resource_provider
        self.run_blocking = run_blocking
        self.model_provider = model_provider

    async def load(self, url: str) -> str:
        logger.info("[ReelLoader] Processing URL: %s", url)
        parse_reel_target(url)

        logger.info("[ReelLoader] Loading audio with YtdlpLoader")
        ytdlp_loader = (
            YtdlpLoader(run_blocking=self.run_blocking, model_provider=self.model_provider)
            if self.ytdlp_loader_factory is YtdlpLoader
            else self.ytdlp_loader_factory()
        )
        audio_content = await ytdlp_loader.load(url)
        logger.info("[ReelLoader] Loading HTML with HttpxLoader")
        httpx_loader = (
            HttpxLoader(resource_provider=self.resource_provider)
            if self.httpx_loader_factory is HttpxLoader
            else self.httpx_loader_factory()
        )
        html_content = await httpx_loader.load(url)

        result = f"{audio_content}\n\n{html_content}"
        logger.info("[ReelLoader] Extracted combined reel content (%s chars)", len(result))
        return result
