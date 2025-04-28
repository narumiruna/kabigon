class LoaderError(Exception):
    pass


class FirecrawlKeyError(LoaderError):
    def __init__(self) -> None:
        super().__init__("FIRECRAWL_API_KEY is not set.")


class FirecrawlError(LoaderError):
    def __init__(self, url: str, error: str) -> None:
        msg = f"Failed to load URL: {url}, got: {error}"
        super().__init__(msg)


class NotPDFError(LoaderError):
    def __init__(self, url: str) -> None:
        super().__init__(f"URL is not a PDF: {url}")


class NotReelURLError(LoaderError):
    def __init__(self, url: str):
        super().__init__(f"URL is not an Instagram Reel: {url}")
