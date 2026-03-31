from urllib.parse import urlparse

from kabigon.domain.errors import LoaderNotApplicableError


def host_in(url: str, hosts: list[str] | tuple[str, ...]) -> bool:
    return urlparse(url).netloc.lower() in {host.lower() for host in hosts}


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


def ensure_host_in(url: str, hosts: list[str] | tuple[str, ...], *, loader_name: str, source_name: str) -> None:
    if host_in(url, hosts):
        return
    expected = ", ".join(hosts)
    raise LoaderNotApplicableError(loader_name, url, f"Not a {source_name} URL. Expected domains: {expected}")
