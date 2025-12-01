"""
BESTLIB - Beautiful & Efficient Visualization Library
=====================================================

Una librería de visualización interactiva para Jupyter Notebooks
con dashboards ASCII y gráficos D3.js.

Características principales:
- 30+ tipos de gráficos interactivos
- Sistema reactivo con vistas enlazadas
- Layouts ASCII para dashboards
- Comunicación bidireccional Python ↔ JavaScript

Uso básico:
    >>> from bestlib import MatrixLayout
    >>> layout = MatrixLayout('''
    ...     scatter | bar
    ...     --------+----
    ...     heatmap | pie
    ... ''')
    >>> layout.render()

Documentación: https://github.com/NahiaEscalante/bestlib
"""

__version__ = "2.0.0"
__author__ = "Nahia Escalante"

# Core exports
from .layouts.matrix import MatrixLayout
from .layouts.reactive import ReactiveMatrixLayout
from .charts.registry import ChartRegistry
from .reactive.selection import SelectionModel, ReactiveData
from .reactive.engine import ReactiveEngine
from .reactive.linking import LinkManager
from .core.exceptions import ChartError, DataError, LayoutError

# Public API
__all__ = [
    # Layouts
    "MatrixLayout",
    "ReactiveMatrixLayout",
    
    # Charts
    "ChartRegistry",
    
    # Reactive system
    "SelectionModel",
    "ReactiveData",
    "ReactiveEngine",
    "LinkManager",
    
    # Exceptions
    "ChartError",
    "DataError",
    "LayoutError",
    
    # Metadata
    "__version__",
]


def get_version():
    """Retorna la versión de BESTLIB."""
    return __version__


def list_chart_types():
    """
    Lista todos los tipos de gráficos disponibles.
    
    Returns:
        list: Lista de nombres de tipos de gráficos
        
    Example:
        >>> import bestlib
        >>> bestlib.list_chart_types()
        ['scatter', 'bar', 'line', 'histogram', ...]
    """
    return ChartRegistry.list_types()


# Configuración de logging (opcional)
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
