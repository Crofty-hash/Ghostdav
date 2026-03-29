"""Backend package initialization"""

from .config.settings import config, AppConfig
from .config.constants import *

__all__ = [
    'config',
    'AppConfig',
]
