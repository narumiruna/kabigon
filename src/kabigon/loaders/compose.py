import logging

from kabigon.core.exception import LoaderContentError
from kabigon.core.exception import LoaderError
from kabigon.core.exception import LoaderNotApplicableError
from kabigon.core.exception import LoaderTimeoutError
from kabigon.core.loader import Loader

logger = logging.getLogger(__name__)


class Compose(Loader):
    def __init__(self, loaders: list[Loader]) -> None:
        self.loaders = loaders

    async def load(self, url: str) -> str:
        errors = []

        for loader in self.loaders:
            loader_name = loader.__class__.__name__
            logger.debug(f"[{loader_name}] Attempting to load URL: {url}")

            try:
                result = await loader.load(url)
            except LoaderNotApplicableError as e:
                # This is expected - loader doesn't handle this URL type
                logger.debug(f"[{loader_name}] Not applicable: {e.reason}")
                errors.append(f"{loader_name}: Not applicable ({e.reason})")
                continue
            except LoaderTimeoutError as e:
                # Timeout - may want to retry or try next loader
                logger.warning(f"[{loader_name}] Timeout after {e.timeout}s: {e.url}")
                errors.append(f"{loader_name}: Timeout after {e.timeout}s")
                continue
            except LoaderContentError as e:
                # Content extraction failed
                logger.warning(f"[{loader_name}] Content extraction failed: {e.reason}")
                errors.append(f"{loader_name}: Content extraction failed - {e.reason}")
                continue
            except Exception as e:  # noqa: BLE001
                # We intentionally catch all exceptions to try the next loader in the chain
                logger.info(f"[{loader_name}] Failed with error: {type(e).__name__}: {e}")
                errors.append(f"{loader_name}: {type(e).__name__}: {e!s}")
                continue

            if not result:
                logger.info(f"[{loader_name}] Got empty result")
                errors.append(f"{loader_name}: Empty result")
                continue

            logger.info(f"[{loader_name}] Successfully loaded URL: {url}")
            return result

        # All loaders failed - create detailed error message
        error_details = "\n  - ".join(errors)
        detailed_message = f"Failed to load URL: {url}\n\nAttempted loaders:\n  - {error_details}"
        logger.error(detailed_message)

        raise LoaderError(url)
