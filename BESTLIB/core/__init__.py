"""
Core module - Fundamentos del sistema BESTLIB
"""
from .exceptions import BestlibError, LayoutError, ChartError, DataError, RenderError, CommunicationError
from .registry import Registry
from .layout import LayoutEngine
from .comm import CommManager, get_comm_engine
from .events import EventManager

__all__ = [
    'BestlibError', 'LayoutError', 'ChartError', 'DataError', 'RenderError', 'CommunicationError',
    'Registry', 'LayoutEngine', 'CommManager', 'get_comm_engine', 'EventManager'
]

