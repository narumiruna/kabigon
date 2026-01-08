class KabigonError(Exception):
    """Base exception for all Kabigon errors."""


class LoaderError(KabigonError):
    """Raised when all loaders fail to load a URL."""

    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"Failed to load URL: {url}")


class InvalidURLError(KabigonError, ValueError):
    """Raised when a URL is not valid for a specific loader."""

    def __init__(self, url: str, expected: str) -> None:
        self.url = url
        self.expected = expected
        super().__init__(f"URL is not a {expected} URL: {url}")


class ConfigurationError(KabigonError):
    """Raised when required configuration is missing."""


class FirecrawlAPIKeyNotSetError(ConfigurationError):
    """Raised when FIRECRAWL_API_KEY environment variable is not set."""

    def __init__(self) -> None:
        super().__init__("FIRECRAWL_API_KEY is not set.")


class MissingDependencyError(KabigonError):
    """Raised when a required dependency is not installed."""


class WhisperNotInstalledError(MissingDependencyError):
    """Raised when OpenAI Whisper is not installed."""

    def __init__(self) -> None:
        super().__init__("OpenAI Whisper not installed. Please install it with `pip install openai-whisper`.")
