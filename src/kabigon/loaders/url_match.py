from urllib.parse import urlparse

from kabigon.domain.errors import LoaderNotApplicableError


def host_matches_domain_suffix(url: str, domain_suffix: str) -> bool:
    host = urlparse(url).netloc.lower()
    normalized_suffix = domain_suffix.lower().lstrip(".")
    return host == normalized_suffix or host.endswith(f".{normalized_suffix}")


def ensure_domain_suffix(url: str, domain_suffix: str, *, loader_name: str, source_name: str) -> None:
    if host_matches_domain_suffix(url, domain_suffix):
        return
    raise LoaderNotApplicableError(
        loader_name,
        url,
        f"Not a {source_name} URL. Expected domain ending with {domain_suffix.lstrip('.').lower()}",
    )
