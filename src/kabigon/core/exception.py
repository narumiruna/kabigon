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

    def __init__(self, message: str) -> None:
        super().__init__(message)


class MissingDependencyError(KabigonError):
    """Raised when a required dependency is not installed."""

    def __init__(self, package: str, install_command: str) -> None:
        self.package = package
        self.install_command = install_command
        super().__init__(f"{package} not installed. Please install it with `{install_command}`.")
