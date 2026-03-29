"""UI package for GhostDav desktop client"""

from .gui import GhostDavGUI
from .main_window import MainWindow
from .widgets import *

__all__ = [
    'GhostDavGUI',
    'MainWindow'
]