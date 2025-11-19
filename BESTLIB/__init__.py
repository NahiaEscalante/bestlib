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
# Estructura modular: reactive/ (SelectionModel, ReactiveEngine, etc.) y layouts/reactive.py (ReactiveMatrixLayout)
SelectionModel = None
ReactiveData = None
ReactiveEngine = None
LinkManager = None
ReactiveMatrixLayout = None
HAS_REACTIVE = False

# Importar desde reactive/ (versión modular)
try:
    from .reactive import SelectionModel as SM_modular, ReactiveData as RD_modular, ReactiveEngine, LinkManager
    SelectionModel = SM_modular
    ReactiveData = RD_modular
    HAS_REACTIVE = True
except (ImportError, AttributeError, ModuleNotFoundError) as e:
    # Si falla el import desde .reactive, intentar import directo desde .reactive.selection
    try:
        from .reactive.selection import SelectionModel as SM_direct, ReactiveData as RD_direct
        SelectionModel = SM_direct
        ReactiveData = RD_direct
        HAS_REACTIVE = True
        # Intentar importar ReactiveEngine y LinkManager por separado
        try:
            from .reactive.engine import ReactiveEngine
        except ImportError:
            ReactiveEngine = None
        try:
            from .reactive.linking import LinkManager
        except ImportError:
            LinkManager = None
    except (ImportError, AttributeError, ModuleNotFoundError):
        # Si también falla, mantener None
        SelectionModel = None
        ReactiveData = None
        ReactiveEngine = None
        LinkManager = None
        HAS_REACTIVE = False
except Exception as e:
    # Capturar cualquier otro error inesperado
    import sys
    if hasattr(sys, '_getframe'):  # Solo en entornos interactivos
        print(f"⚠️ Error inesperado al importar módulo reactivo: {e}")
        import traceback
        traceback.print_exc()
    # Intentar fallback directo
    try:
        from .reactive.selection import SelectionModel as SM_direct, ReactiveData as RD_direct
        SelectionModel = SM_direct
        ReactiveData = RD_direct
        HAS_REACTIVE = True
    except:
        SelectionModel = None
        ReactiveData = None
        HAS_REACTIVE = False

# Importar ReactiveMatrixLayout desde layouts/reactive.py (estructura modular)
try:
    from .layouts.reactive import ReactiveMatrixLayout
    if ReactiveMatrixLayout is not None:
        HAS_REACTIVE = True
except ImportError:
    # Fallback: intentar desde reactive.py legacy (si existe)
    try:
        import importlib.util
        from pathlib import Path
        reactive_py = Path(__file__).parent / "reactive.py"
        if reactive_py.exists():
            spec = importlib.util.spec_from_file_location("reactive_legacy", str(reactive_py))
            if spec and spec.loader:
                reactive_legacy = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(reactive_legacy)
                ReactiveMatrixLayout = getattr(reactive_legacy, 'ReactiveMatrixLayout', None)
                if ReactiveMatrixLayout is not None:
                    HAS_REACTIVE = True
    except Exception:
        pass

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
# Core module - OPCIONAL (para compatibilidad con versiones sin estructura modular)
try:
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
    HAS_CORE = True
except ImportError:
    # Si no hay módulo core, crear clases base para compatibilidad
    HAS_CORE = False
    class BestlibError(Exception):
        """Excepción base para BESTLIB"""
        pass
    class LayoutError(BestlibError):
        """Error relacionado con layouts"""
        pass
    class ChartError(BestlibError):
        """Error relacionado con gráficos"""
        pass
    class DataError(BestlibError):
        """Error relacionado con datos"""
        pass
    class RenderError(BestlibError):
        """Error relacionado con renderizado"""
        pass
    class CommunicationError(BestlibError):
        """Error relacionado con comunicación"""
        pass
    Registry = None
    LayoutEngine = None
    CommManager = None
    EventManager = None
    get_comm_engine = None

# Charts module - Nueva API para gráficos
# Importar ChartRegistry de forma robusta (puede usarse independientemente)
try:
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
    HAS_CHARTS = True
except ImportError as e:
    # Si falla la importación de charts, ChartRegistry no estará disponible
    HAS_CHARTS = False
    ChartBase = None
    ChartRegistry = None
    ScatterChart = None
    BarChart = None
    HistogramChart = None
    BoxplotChart = None
    HeatmapChart = None
    LineChart = None
    PieChart = None
    GroupedBarChart = None

# Data module - OPCIONAL (para compatibilidad con versiones sin estructura modular)
try:
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
    HAS_DATA = True
except ImportError:
    # Si no hay módulo data, crear funciones stub básicas
    HAS_DATA = False
    def prepare_scatter_data(*args, **kwargs):
        """Stub: retorna los datos sin procesar"""
        return kwargs.get('data') or args[0] if args else None
    def prepare_bar_data(*args, **kwargs):
        return kwargs.get('data') or args[0] if args else None
    def prepare_histogram_data(*args, **kwargs):
        return kwargs.get('data') or args[0] if args else None
    def prepare_boxplot_data(*args, **kwargs):
        return kwargs.get('data') or args[0] if args else None
    def prepare_heatmap_data(*args, **kwargs):
        return kwargs.get('data') or args[0] if args else None
    def prepare_line_data(*args, **kwargs):
        return kwargs.get('data') or args[0] if args else None
    def prepare_pie_data(*args, **kwargs):
        return kwargs.get('data') or args[0] if args else None
    def validate_scatter_data(*args, **kwargs):
        return True  # Stub: siempre válido
    def validate_bar_data(*args, **kwargs):
        return True
    def dataframe_to_dicts(df):
        """Stub básico: convierte DataFrame a lista de dicts"""
        try:
            import pandas as pd
            if isinstance(df, pd.DataFrame):
                return df.to_dict('records')
        except:
            pass
        return df if isinstance(df, list) else []
    def dicts_to_dataframe(dicts):
        """Stub básico: convierte lista de dicts a DataFrame"""
        try:
            import pandas as pd
            if isinstance(dicts, list):
                return pd.DataFrame(dicts)
        except:
            pass
        return dicts

# Utils module - OPCIONAL (para compatibilidad con versiones sin estructura modular)
try:
    from .utils import sanitize_for_json, figsize_to_pixels
    HAS_UTILS = True
except ImportError:
    # Si no hay módulo utils, crear funciones stub básicas
    HAS_UTILS = False
    def sanitize_for_json(obj):
        """
        Stub básico: convierte tipos numpy a tipos Python nativos para JSON.
        Versión simplificada si el módulo utils no está disponible.
        """
        import json
        # Manejar tipos numpy básicos
        if hasattr(obj, 'item'):  # numpy.int64, numpy.float64, etc.
            return obj.item()
        if hasattr(obj, 'tolist'):  # numpy arrays
            return obj.tolist()
        # Manejar dicts y listas recursivamente
        if isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [sanitize_for_json(item) for item in obj]
        return obj
    
    def figsize_to_pixels(figsize):
        """
        Stub básico: convierte figsize de pulgadas a píxeles.
        Versión simplificada si el módulo utils no está disponible.
        """
        if figsize is None:
            return None
        if isinstance(figsize, (tuple, list)) and len(figsize) == 2:
            width, height = figsize
            # Si valores son <= 50, asumir pulgadas; si > 50, asumir píxeles
            if width <= 50 and height <= 50:
                return (int(width * 96), int(height * 96))  # 96 DPI
            else:
                return (int(width), int(height))
        return figsize

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
    
    # Excepciones (siempre disponibles, incluso si core no está)
    "BestlibError",
    "LayoutError",
    "ChartError",
    "DataError",
    "RenderError",
    "CommunicationError",
    
    # Reactive (agregados condicionalmente más abajo)
    
    # Render (agregados condicionalmente más abajo)
]

if HAS_CORE:
    __all__.extend([
        "Registry",
        "LayoutEngine",
        "CommManager",
        "EventManager",
        "get_comm_engine"
    ])

if HAS_DATA:
    __all__.extend([
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
        "dicts_to_dataframe"
    ])

if HAS_UTILS:
    __all__.extend([
        "sanitize_for_json",
        "figsize_to_pixels"
    ])

if HAS_REACTIVE:
    __all__.extend(["ReactiveMatrixLayout", "SelectionModel", "ReactiveData", "ReactiveEngine", "LinkManager"])

if HAS_LINKED:
    __all__.append("LinkedViews")

if HAS_CHARTS:
    __all__.extend([
        "ChartBase",
        "ChartRegistry",
        "ScatterChart",
        "BarChart",
        "HistogramChart",
        "BoxplotChart",
        "HeatmapChart",
        "LineChart",
        "PieChart",
        "GroupedBarChart"
    ])

# ============================================================================
# Inicialización automática
# ============================================================================
# Registrar automáticamente el comm al importar
# Esto asegura que la comunicación bidireccional funcione sin configuración extra
try:
    if HAS_CORE and CommManager is not None:
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
