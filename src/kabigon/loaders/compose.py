from loguru import logger

from kabigon.core.exception import LoaderError
from kabigon.core.loader import Loader


class Compose(Loader):
    def __init__(self, loaders: list[Loader]) -> None:
        self.loaders = loaders

    async def load(self, url: str) -> str:
        for loader in self.loaders:
            try:
                result = await loader.load(url)
            except Exception as e:  # noqa: BLE001
                # We intentionally catch all exceptions to try the next loader in the chain
                logger.info("[{}] Failed to load URL: {}, got error: {}", loader.__class__.__name__, url, e)
            else:
                if not result:
                    logger.info("[{}] Failed to load URL: {}, got empty result", loader.__class__.__name__, url)
                    continue

                logger.info("[{}] Successfully loaded URL: {}", loader.__class__.__name__, url)
                return result

        raise LoaderError(url)
