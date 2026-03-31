from kabigon.domain.models import ContentType
from kabigon.domain.models import LoaderPlan
from kabigon.domain.models import RetrievalContext
from kabigon.domain.models import RetrievalStrategy


def test_core_models_exported() -> None:
    assert RetrievalContext.__name__ == "RetrievalContext"
    assert RetrievalStrategy.__name__ == "RetrievalStrategy"
    assert LoaderPlan.__name__ == "LoaderPlan"
    assert ContentType.__name__ == "ContentType"
