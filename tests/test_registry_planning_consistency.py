from kabigon.application.pipeline_catalog import list_pipelines
from kabigon.application.planning import DEFAULT_FALLBACK_LOADERS
from kabigon.infrastructure.registry import list_loader_names


def test_default_fallback_loaders_registered() -> None:
    registered = set(list_loader_names())
    missing = [name for name in DEFAULT_FALLBACK_LOADERS if name not in registered]
    assert missing == []


def test_pipeline_targeted_loaders_registered() -> None:
    registered = set(list_loader_names())
    missing = []

    for pipeline in list_pipelines():
        missing.extend(name for name in pipeline.targeted_loaders if name not in registered)

    assert missing == []
