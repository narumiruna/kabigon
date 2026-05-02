from kabigon.application.pipeline_catalog import _PIPELINE_ENTRIES
from kabigon.application.planning import DEFAULT_FALLBACK_LOADERS
from kabigon.infrastructure.registry import list_loader_names


def test_default_fallback_loaders_registered() -> None:
    registered = set(list_loader_names())
    missing = [name for name in DEFAULT_FALLBACK_LOADERS if name not in registered]
    assert missing == []


def test_pipeline_targeted_loaders_registered() -> None:
    registered = set(list_loader_names())
    missing = []

    for entry in _PIPELINE_ENTRIES:
        missing.extend(name for name in entry.pipeline.targeted_loaders if name not in registered)

    assert missing == []
