import os
import sys
from typing import Final

from loguru import logger

from .compose import Compose
from .httpx import HttpxLoader
from .loader import Loader
from .pdf import PDFLoader
from .playwright import PlaywrightLoader
from .reel import ReelLoader
from .singlefile import SinglefileLoader
from .youtube import YoutubeLoader
from .ytdlp import YtdlpLoader

LOGURU_LEVEL: Final[str] = os.getenv("LOGURU_LEVEL", "INFO")
logger.configure(handlers=[{"sink": sys.stderr, "level": LOGURU_LEVEL}])
