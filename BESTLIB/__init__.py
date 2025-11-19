# ============================================================================
# BESTLIB - Modularized Version
# ============================================================================
# Mantener compatibilidad hacia atrás con API original
# Intentar usar versión refactorizada, fallback a original
try:
    from .layouts.matrix import MatrixLayout
except ImportError:
    from .matrix import MatrixLayout  # Fallback a versión legacy

# Intentar importar módulo reactivo (opcional)
try:
    # Intentar usar versión modular primero
    from .reactive import SelectionModel, ReactiveData, ReactiveEngine, LinkManager
    HAS_REACTIVE = True
except ImportError:
    HAS_REACTIVE = False
    SelectionModel = None
    ReactiveData = None
    ReactiveEngine = None
    LinkManager = None

# Intentar importar ReactiveMatrixLayout (legacy - todavía en reactive.py)
# ReactiveMatrixLayout es una clase grande en reactive.py legacy
# Por ahora mantenemos compatibilidad importándolo directamente
try:
    # Importar desde el módulo legacy reactive.py (si existe)
    import importlib.util
    from pathlib import Path
    reactive_py = Path(__file__).parent / "reactive.py"
    if reactive_py.exists():
        spec = importlib.util.spec_from_file_location("reactive_legacy", str(reactive_py))
        if spec and spec.loader:
            reactive_legacy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(reactive_legacy)
            ReactiveMatrixLayout = getattr(reactive_legacy, 'ReactiveMatrixLayout', None)
        else:
            ReactiveMatrixLayout = None
    else:
        ReactiveMatrixLayout = None
except Exception:
    ReactiveMatrixLayout = None

# Importar sistema de vistas enlazadas
try:
    from .linked import LinkedViews
    HAS_LINKED = True
except ImportError:
    HAS_LINKED = False
    LinkedViews = None

# ============================================================================
# Nueva API Modular (Fase 1)
# ============================================================================
# Core module
from .core import (
    BestlibError,
    LayoutError,
    ChartError,
    DataError,
    RenderError,
    CommunicationError,
    Registry,
    LayoutEngine,
    CommManager,
    EventManager,
    get_comm_engine
)

# Charts module - Nueva API para gráficos
from .charts import ChartBase, ChartRegistry
from .charts import (
    ScatterChart,
    BarChart,
    HistogramChart,
    BoxplotChart,
    HeatmapChart,
    LineChart,
    PieChart,
    GroupedBarChart
)

# Data module - Procesamiento de datos
from .data import (
    prepare_scatter_data,
    prepare_bar_data,
    prepare_histogram_data,
    prepare_boxplot_data,
    prepare_heatmap_data,
    prepare_line_data,
    prepare_pie_data,
    validate_scatter_data,
    validate_bar_data,
    dataframe_to_dicts,
    dicts_to_dataframe
)

# Utils module
from .utils import sanitize_for_json, figsize_to_pixels

# ============================================================================
# Compatibilidad hacia atrás
# ============================================================================
# Wrappers de compatibilidad para métodos map_*
try:
    from .compat import (
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
    # Si compat module no está disponible, usar métodos originales
    pass

# ============================================================================
# Construir __all__ dinámicamente
# ============================================================================
__all__ = [
    # API Original (compatibilidad hacia atrás)
    "MatrixLayout",
    
    # Excepciones
    "BestlibError",
    "LayoutError",
    "ChartError",
    "DataError",
    "RenderError",
    "CommunicationError",
    
    # Core
    "Registry",
    "LayoutEngine",
    "CommManager",
    "EventManager",
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
    
    # Data
    "prepare_scatter_data",
    "prepare_bar_data",
    "prepare_histogram_data",
    "validate_scatter_data",
    "validate_bar_data",
    "dataframe_to_dicts",
    "dicts_to_dataframe",
    
    # Utils
    "sanitize_for_json",
    "figsize_to_pixels",
    
    # Reactive
    "ReactiveData",
    "ReactiveEngine",
    "LinkManager",
    
    # Render
    "HTMLGenerator",
    "JSBuilder",
    "AssetManager",
]

if HAS_REACTIVE:
    __all__.extend(["ReactiveMatrixLayout", "SelectionModel"])

if HAS_LINKED:
    __all__.append("LinkedViews")

# ============================================================================
# Inicialización automática
# ============================================================================
# Registrar automáticamente el comm al importar
# Esto asegura que la comunicación bidireccional funcione sin configuración extra
try:
    CommManager.register_comm()
    # También registrar en MatrixLayout para compatibilidad
    MatrixLayout.register_comm()
except Exception:
    # Silenciar errores si no estamos en Jupyter
    # (ej: al importar en scripts, tests, etc.)
    pass

# ============================================================================
# Metadata
# ============================================================================
__version__ = "0.1.0-modular"
__author__ = "BESTLIB Team"
__status__ = "Modularization in Progress"
