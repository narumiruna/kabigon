import os
import sys
from typing import Final

from loguru import logger

from .api import load_url as load_url
from .api import load_url_sync as load_url_sync

LOGURU_LEVEL: Final[str] = os.getenv("LOGURU_LEVEL", "INFO")
logger.remove()
logger.add(sys.stderr, level=LOGURU_LEVEL)
