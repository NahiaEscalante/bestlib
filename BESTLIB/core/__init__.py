"""
Core module - Fundamentos del sistema BESTLIB
"""
from .exceptions import (
    BestlibError, LayoutError, ChartError, DataError, RenderError, CommunicationError,
    get_logger
)
from .registry import Registry
from .layout import LayoutEngine
from .comm import CommManager, get_comm_engine
from .events import EventManager
from .validation import (
    validate_dataframe, validate_list_of_dicts, validate_numeric_range,
    validate_string_param, safe_get_first_item, safe_dataframe
)

__all__ = [
    'BestlibError', 'LayoutError', 'ChartError', 'DataError', 'RenderError', 'CommunicationError',
    'Registry', 'LayoutEngine', 'CommManager', 'get_comm_engine', 'EventManager',
    'get_logger',
    'validate_dataframe', 'validate_list_of_dicts', 'validate_numeric_range',
    'validate_string_param', 'safe_get_first_item', 'safe_dataframe'
]

