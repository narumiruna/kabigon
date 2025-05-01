class KabigonError(Exception):
    pass


class FirecrawlKeyError(KabigonError):
    def __init__(self) -> None:
        super().__init__("FIRECRAWL_API_KEY is not set.")


class FirecrawlError(KabigonError):
    def __init__(self, url: str, error: str) -> None:
        msg = f"Failed to load URL: {url}, got: {error}"
        super().__init__(msg)


class NotPDFError(KabigonError):
    def __init__(self, url: str) -> None:
        super().__init__(f"URL is not a PDF: {url}")


class NotReelURLError(KabigonError):
    def __init__(self, url: str):
        super().__init__(f"URL is not an Instagram Reel: {url}")


class NotTwitterURLError(KabigonError):
    def __init__(self, url: str):
        super().__init__(f"URL is not a Twitter URL: {url}")
