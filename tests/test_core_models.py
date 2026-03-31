from kabigon.core import ContentType
from kabigon.core import LoaderPlan
from kabigon.core import RetrievalContext
from kabigon.core import RetrievalStrategy
from kabigon.retrieval.models import LoaderPlan as LoaderPlanCompat
from kabigon.retrieval.models import RetrievalContext as RetrievalContextCompat


def test_core_models_exported() -> None:
    assert RetrievalContext.__name__ == "RetrievalContext"
    assert RetrievalStrategy.__name__ == "RetrievalStrategy"
    assert LoaderPlan.__name__ == "LoaderPlan"
    assert ContentType.__name__ == "ContentType"


def test_compat_reexports_still_work() -> None:
    assert RetrievalContextCompat is RetrievalContext
    assert LoaderPlanCompat is LoaderPlan
