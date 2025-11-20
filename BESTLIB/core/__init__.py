"""
Core module - Fundamentos del sistema BESTLIB
"""
from .exceptions import BestlibError, LayoutError, ChartError, DataError, RenderError, CommunicationError
from .registry import Registry
from .layout import LayoutEngine
from .comm import CommManager, get_comm_engine
from .events import EventManager

# Importar funciones de DeepNote (opcional)
try:
    from .deepnote import is_deepnote, initialize_deepnote, ensure_deepnote_ready, set_debug as set_deepnote_debug
    __all__ = [
        'BestlibError', 'LayoutError', 'ChartError', 'DataError', 'RenderError', 'CommunicationError',
        'Registry', 'LayoutEngine', 'CommManager', 'get_comm_engine', 'EventManager',
        'is_deepnote', 'initialize_deepnote', 'ensure_deepnote_ready', 'set_deepnote_debug'
    ]
except ImportError:
    __all__ = [
        'BestlibError', 'LayoutError', 'ChartError', 'DataError', 'RenderError', 'CommunicationError',
        'Registry', 'LayoutEngine', 'CommManager', 'get_comm_engine', 'EventManager'
    ]

