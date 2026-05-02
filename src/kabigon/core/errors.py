class KabigonError(Exception):
    """Base exception for all Kabigon errors."""


class LoaderError(KabigonError):
    """Raised when all loaders fail to load a URL."""

    def __init__(self, url: str, details: list[str] | None = None) -> None:
        self.url = url
        self.details = details or []

        message = f"Failed to load URL: {url}"
        if self.details:
            joined = "\n  - ".join(self.details)
            message = f"{message}\n\nAttempted loaders:\n  - {joined}"
        super().__init__(message)


class InvalidURLError(KabigonError, ValueError):
    """Raised when a URL is not valid for a specific loader."""

    def __init__(self, url: str, expected: str) -> None:
        self.url = url
        self.expected = expected
        super().__init__(f"URL is not a {expected} URL: {url}")


class ConfigurationError(KabigonError):
    """Raised when required configuration is missing."""


class MissingRequirementError(ConfigurationError):
    """Raised when a Load chain requirement is missing."""

    def __init__(self, requirements: tuple[str, ...]) -> None:
        self.requirements = requirements
        missing = ", ".join(requirements)
        super().__init__(f"Missing required environment variable(s): {missing}")


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


class LoaderNotApplicableError(KabigonError):
    """Raised when a URL is not applicable to a specific loader."""

    def __init__(self, loader_name: str, url: str, reason: str | None = None) -> None:
        self.loader_name = loader_name
        self.url = url
        self.reason = reason

        message = f"{loader_name} cannot handle URL: {url}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class LoaderTimeoutError(KabigonError):
    """Raised when a loader operation times out."""

    def __init__(self, loader_name: str, url: str, timeout: float, suggestion: str | None = None) -> None:
        self.loader_name = loader_name
        self.url = url
        self.timeout = timeout
        self.suggestion = suggestion

        message = f"{loader_name} timed out after {timeout}s while loading: {url}"
        if suggestion:
            message += f"\nSuggestion: {suggestion}"
        else:
            message += "\nSuggestion: Try increasing the timeout or check your network connection."
        super().__init__(message)


class LoaderContentError(KabigonError):
    """Raised when content extraction fails."""

    def __init__(self, loader_name: str, url: str, reason: str, suggestion: str | None = None) -> None:
        self.loader_name = loader_name
        self.url = url
        self.reason = reason
        self.suggestion = suggestion

        message = f"{loader_name} failed to extract content from: {url} - {reason}"
        if suggestion:
            message += f"\nSuggestion: {suggestion}"
        super().__init__(message)
