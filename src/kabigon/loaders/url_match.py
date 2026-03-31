from urllib.parse import urlparse


def host_matches_domain_suffix(url: str, domain_suffix: str) -> bool:
    host = urlparse(url).netloc.lower()
    normalized_suffix = domain_suffix.lower().lstrip(".")
    return host == normalized_suffix or host.endswith(f".{normalized_suffix}")
