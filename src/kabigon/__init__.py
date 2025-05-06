import os
import sys
from typing import Final

from loguru import logger

from .compose import Compose
from .firecrawl import FirecrawlLoader
from .httpx import HttpxLoader
from .loader import Loader
from .pdf import PDFLoader
from .playwright import PlaywrightLoader
from .ptt import PttLoader
from .reel import ReelLoader
from .twitter import TwitterLoader
from .youtube import YoutubeLoader
from .youtube_ytdlp import YoutubeYtdlpLoader
from .ytdlp import YtdlpLoader

LOGURU_LEVEL: Final[str] = os.getenv("LOGURU_LEVEL", "INFO")
logger.configure(handlers=[{"sink": sys.stderr, "level": LOGURU_LEVEL}])
