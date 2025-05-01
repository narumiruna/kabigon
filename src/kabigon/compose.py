from loguru import logger

from .loader import Loader


class Compose(Loader):
    def __init__(self, loaders: list[Loader]) -> None:
        self.loaders = loaders

    def load(self, url: str) -> str:
        for loader in self.loaders:
            try:
                content = loader.load(url)

                if not content:
                    logger.info("[{}] Failed to load URL: {}, got empty result", loader.__class__.__name__, url)
                    continue

                logger.info("[{}] Successfully loaded URL: {}", loader.__class__.__name__, url)
                return content

            except Exception as e:
                logger.info("[{}] Failed to load URL: {}, got error: {}", loader.__class__.__name__, url, e)

        raise Exception(f"Failed to load URL: {url}")

    async def async_load(self, url: str) -> str:
        for loader in self.loaders:
            try:
                content = await loader.async_load(url)

                if not content:
                    logger.info("[{}] Failed to load URL: {}, got empty result", loader.__class__.__name__, url)
                    continue

                logger.info("[{}] Successfully loaded URL: {}", loader.__class__.__name__, url)
                return content

            except Exception as e:
                logger.info("[{}] Failed to load URL: {}, got error: {}", loader.__class__.__name__, url, e)

        raise Exception(f"Failed to load URL: {url}")
