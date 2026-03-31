from kabigon.application.routing import DEFAULT_FALLBACK_LOADERS
from kabigon.application.routing import ROUTES
from kabigon.infrastructure.registry import list_loader_names


def test_default_fallback_loaders_registered():
    registered = set(list_loader_names())
    missing = [name for name in DEFAULT_FALLBACK_LOADERS if name not in registered]
    assert missing == []


def test_route_targeted_loaders_registered():
    registered = set(list_loader_names())
    missing = []
    for _pipeline_name, _matcher, loaders in ROUTES:
        missing.extend(name for name in loaders if name not in registered)
    assert missing == []
