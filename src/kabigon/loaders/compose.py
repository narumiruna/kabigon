import logging

from kabigon.domain.errors import LoaderContentError
from kabigon.domain.errors import LoaderError
from kabigon.domain.errors import LoaderNotApplicableError
from kabigon.domain.errors import LoaderTimeoutError
from kabigon.domain.loader import Loader

logger = logging.getLogger(__name__)


class Compose(Loader):
    def __init__(self, loaders: list[Loader]) -> None:
        self.loaders = loaders

    async def load(self, url: str) -> str:
        errors = []

        for loader in self.loaders:
            loader_name = loader.__class__.__name__
            logger.debug("[%s] Attempting to load URL: %s", loader_name, url)

            try:
                result = await loader.load(url)
            except LoaderNotApplicableError as e:
                # This is expected - loader doesn't handle this URL type
                logger.debug("[%s] Not applicable: %s", loader_name, e.reason)
                errors.append(f"{loader_name}: Not applicable ({e.reason})")
                continue
            except LoaderTimeoutError as e:
                # Timeout - may want to retry or try next loader
                logger.warning("[%s] Timeout after %ss: %s", loader_name, e.timeout, e.url)
                errors.append(f"{loader_name}: Timeout after {e.timeout}s")
                continue
            except LoaderContentError as e:
                # Content extraction failed
                logger.warning("[%s] Content extraction failed: %s", loader_name, e.reason)
                errors.append(f"{loader_name}: Content extraction failed - {e.reason}")
                continue
            except Exception as e:  # noqa: BLE001
                # We intentionally catch all exceptions to try the next loader in the chain
                logger.info("[%s] Failed with error: %s: %s", loader_name, type(e).__name__, e)
                errors.append(f"{loader_name}: {type(e).__name__}: {e!s}")
                continue

            if not result:
                logger.info("[%s] Got empty result", loader_name)
                errors.append(f"{loader_name}: Empty result")
                continue

            logger.info("[%s] Successfully loaded URL: %s", loader_name, url)
            return result

        # All loaders failed - create detailed error message
        if errors:
            error_details = "\n  - ".join(errors)
            logger.error("Failed to load URL: %s\n\nAttempted loaders:\n  - %s", url, error_details)
        else:
            logger.error("Failed to load URL: %s", url)

        raise LoaderError(url, details=errors)
