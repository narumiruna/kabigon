import inspect

from kabigon.core.loader import Loader
from kabigon.loaders import BBCLoader
from kabigon.loaders import CNNLoader
from kabigon.loaders import FirecrawlLoader
from kabigon.loaders import GitHubLoader
from kabigon.loaders import HttpxLoader
from kabigon.loaders import LTNLoader
from kabigon.loaders import PDFLoader
from kabigon.loaders import PlaywrightLoader
from kabigon.loaders import PttLoader
from kabigon.loaders import RedditLoader
from kabigon.loaders import ReelLoader
from kabigon.loaders import TruthSocialLoader
from kabigon.loaders import TwitterLoader
from kabigon.loaders import YoutubeLoader
from kabigon.loaders import YoutubeYtdlpLoader
from kabigon.loaders import YtdlpLoader

LOADER_CLASSES = [
    BBCLoader,
    CNNLoader,
    FirecrawlLoader,
    GitHubLoader,
    HttpxLoader,
    LTNLoader,
    PDFLoader,
    PlaywrightLoader,
    PttLoader,
    RedditLoader,
    ReelLoader,
    TruthSocialLoader,
    TwitterLoader,
    YoutubeLoader,
    YoutubeYtdlpLoader,
    YtdlpLoader,
]


def test_loader_base_is_abstract():
    assert inspect.isabstract(Loader)


def test_all_loader_classes_implement_async_load():
    for loader_class in LOADER_CLASSES:
        assert issubclass(loader_class, Loader)
        assert "load" in loader_class.__dict__
        assert inspect.iscoroutinefunction(loader_class.load)
