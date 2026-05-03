from kabigon.load_chain import DEFAULT_FALLBACK_LOADERS
from kabigon.loader_registry import list_loader_names
from kabigon.pipelines.catalog import list_pipelines


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
