from __future__ import annotations

import logging
from collections.abc import Awaitable
from collections.abc import Callable

from kabigon.core.loader import Loader
from kabigon.sources.applicability import parse_youtube_video_target
from kabigon.sources.applicability import require_loader_applicability

from .ytdlp import ModelProvider
from .ytdlp import YtdlpLoader

type LoaderFactory = Callable[[], Loader]
logger = logging.getLogger(__name__)


class YoutubeYtdlpLoader(Loader):
    def __init__(
        self,
        ytdlp_loader_factory: LoaderFactory = YtdlpLoader,
        run_blocking: Callable[[Callable[[], str]], Awaitable[str]] | None = None,
        model_provider: ModelProvider | None = None,
    ) -> None:
        self.ytdlp_loader_factory = ytdlp_loader_factory
        self.run_blocking = run_blocking
        self.model_provider = model_provider

    def _loader(self) -> Loader:
        if self.ytdlp_loader_factory is YtdlpLoader:
            return YtdlpLoader(run_blocking=self.run_blocking, model_provider=self.model_provider)
        return self.ytdlp_loader_factory()

    def load_sync(self, url: str) -> str:
        require_loader_applicability("YoutubeYtdlpLoader", url, parse_youtube_video_target)
        loader = self._loader()
        return loader.load_sync(url)

    async def load(self, url: str) -> str:
        require_loader_applicability("YoutubeYtdlpLoader", url, parse_youtube_video_target)
        return await self._loader().load(url)
