# ============================================================================
# BESTLIB - Public API
# ============================================================================
"""
BESTLIB - Beautiful & Efficient Visualization Library

API pública para crear visualizaciones interactivas en Jupyter Notebooks.
Ver docs/API_PUBLICA.md para documentación completa.
"""
import warnings

__version__ = "0.1.0"
__author__ = "BESTLIB Team"

# ============================================================================
# Core: Layouts
# ============================================================================
# SIEMPRE usar la versión modular, sin fallbacks a legacy
from .layouts.matrix import MatrixLayout
from .layouts.reactive import ReactiveMatrixLayout

# ============================================================================
# Core: Sistema Reactivo
# ============================================================================
from .reactive.selection import SelectionModel, ReactiveData
from .reactive.engine import ReactiveEngine
from .reactive.linking import LinkManager

# ============================================================================
# Core: Excepciones
# ============================================================================
from .core.exceptions import (
    BestlibError,
    LayoutError,
    ChartError,
    DataError,
    RenderError,
    CommunicationError
)

# ============================================================================
# Core: Comunicación y Eventos
# ============================================================================
from .core.comm import CommManager, get_comm_engine
from .core.events import EventManager
from .core.layout import LayoutEngine
from .core.registry import Registry

# ============================================================================
# Charts: Sistema de Gráficos
# ============================================================================
from .charts.base import ChartBase
from .charts.registry import ChartRegistry

# Importar gráficos principales (disponibles públicamente)
from .charts.scatter import ScatterChart
from .charts.bar import BarChart
from .charts.histogram import HistogramChart
from .charts.boxplot import BoxplotChart
from .charts.heatmap import HeatmapChart
from .charts.line import LineChart
from .charts.pie import PieChart
from .charts.grouped_bar import GroupedBarChart

# ============================================================================
# Legacy/Deprecated: LinkedViews
# ============================================================================
# Mantener por compatibilidad pero marcar como deprecated
try:
    from .linked import LinkedViews
    
    # Añadir warning de deprecation
    class LinkedViewsDeprecated(LinkedViews):
        """
        LinkedViews está deprecated y será eliminado en v0.2.0.
        
        Migración recomendada:
            from BESTLIB import ReactiveMatrixLayout, SelectionModel
            
            # En lugar de LinkedViews()
            layout = ReactiveMatrixLayout("SB", selection_model=SelectionModel())
            layout.set_data(df)
            layout.add_scatter('S', x_col='x', y_col='y', interactive=True)
            layout.add_barchart('B', category_col='category', linked_to='S')
            layout.display()
        """
        def __init__(self, *args, **kwargs):
            warnings.warn(
                "LinkedViews está deprecated y será eliminado en v0.2.0. "
                "Usa ReactiveMatrixLayout en su lugar. "
                "Ver docs/API_PUBLICA.md para ejemplos de migración.",
                DeprecationWarning,
                stacklevel=2
            )
            super().__init__(*args, **kwargs)
    
    LinkedViews = LinkedViewsDeprecated
    
except ImportError:
    # Si linked.py no existe, crear un stub que lance error informativo
    class LinkedViews:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "LinkedViews no está disponible. "
                "Usa ReactiveMatrixLayout en su lugar:\n"
                "  from BESTLIB import ReactiveMatrixLayout, SelectionModel\n"
                "  layout = ReactiveMatrixLayout('SB', selection_model=SelectionModel())\n"
                "Ver docs/API_PUBLICA.md para ejemplos completos."
            )

# ============================================================================
# Data: Funciones de Preparación y Validación
# ============================================================================
# Exponer las funciones principales de data/ para usuarios avanzados
from .data.preparators import (
    prepare_scatter_data,
    prepare_bar_data,
    prepare_histogram_data,
    prepare_boxplot_data,
    prepare_heatmap_data,
    prepare_line_data,
    prepare_pie_data
)
from .data.validators import (
    validate_scatter_data,
    validate_bar_data
)
from .data.transformers import (
    dataframe_to_dicts,
    dicts_to_dataframe
)

# ============================================================================
# Utils: Funciones de Utilidad
# ============================================================================
from .utils.json import sanitize_for_json
from .utils.figsize import figsize_to_pixels

# ============================================================================
# Compat: Funciones Legacy map_* (thin wrappers)
# ============================================================================
# Estas funciones mantienen compatibilidad hacia atrás pero internamente
# delegan a la implementación modular
try:
    from .compat.chart_wrappers import (
        map_scatter,
        map_barchart,
        map_histogram,
        map_boxplot,
        map_heatmap,
        map_line,
        map_pie,
        map_grouped_barchart
    )
except ImportError:
    # Si compat no está disponible, no exponer map_*
    # Los usuarios deben usar MatrixLayout.map_* en su lugar
    pass

# ============================================================================
# Inicialización Automática
# ============================================================================
# Registrar comm automáticamente al importar (solo si estamos en Jupyter)
try:
    CommManager.register_comm()
    # También intentar registrar en MatrixLayout para compatibilidad
    try:
        MatrixLayout.register_comm()
    except Exception:
        # Silenciar si no estamos en Jupyter
        pass
except Exception:
    # Silenciar si no estamos en Jupyter (scripts, tests, etc.)
    pass

# ============================================================================
# Public API (__all__)
# ============================================================================
__all__ = [
    # Layouts
    "MatrixLayout",
    "ReactiveMatrixLayout",
    
    # Sistema Reactivo
    "SelectionModel",
    "ReactiveData",
    "ReactiveEngine",
    "LinkManager",
    
    # Legacy/Deprecated
    "LinkedViews",  # DEPRECATED
    
    # Excepciones
    "BestlibError",
    "LayoutError",
    "ChartError",
    "DataError",
    "RenderError",
    "CommunicationError",
    
    # Core (para usuarios avanzados)
    "CommManager",
    "EventManager",
    "LayoutEngine",
    "Registry",
    "get_comm_engine",
    
    # Charts
    "ChartBase",
    "ChartRegistry",
    "ScatterChart",
    "BarChart",
    "HistogramChart",
    "BoxplotChart",
    "HeatmapChart",
    "LineChart",
    "PieChart",
    "GroupedBarChart",
    
    # Data (para usuarios avanzados)
    "prepare_scatter_data",
    "prepare_bar_data",
    "prepare_histogram_data",
    "prepare_boxplot_data",
    "prepare_heatmap_data",
    "prepare_line_data",
    "prepare_pie_data",
    "validate_scatter_data",
    "validate_bar_data",
    "dataframe_to_dicts",
    "dicts_to_dataframe",
    
    # Utils (para usuarios avanzados)
    "sanitize_for_json",
    "figsize_to_pixels",
]

# Añadir funciones compat si están disponibles
try:
    __all__.extend([
        "map_scatter",
        "map_barchart",
        "map_histogram",
        "map_boxplot",
        "map_heatmap",
        "map_line",
        "map_pie",
        "map_grouped_barchart",
    ])
except NameError:
    # map_* no están disponibles, no es crítico
    pass

# ============================================================================
# Helper Functions para Compatibilidad
# ============================================================================
def _ensure_reactive_imported():
    """
    Función helper para compatibilidad hacia atrás.
    Ya no es necesaria con la nueva estructura, pero se mantiene por compatibilidad.
    """
    return True

def get_selection_model():
    """
    Función helper para obtener una instancia de SelectionModel.
    
    Returns:
        SelectionModel: Nueva instancia de SelectionModel
    """
    return SelectionModel()

__all__.extend(["_ensure_reactive_imported", "get_selection_model"])
