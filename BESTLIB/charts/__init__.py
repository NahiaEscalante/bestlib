"""
Charts module - Sistema extensible de gráficos para BESTLIB
"""
from .base import ChartBase
from .registry import ChartRegistry

# Importar gráficos para registro automático (con manejo defensivo de errores)
# Esto permite que BESTLIB se importe incluso si pandas está corrupto
ScatterChart = None
BarChart = None
HistogramChart = None
BoxplotChart = None
HeatmapChart = None
LineChart = None
PieChart = None
ViolinChart = None
RadvizChart = None
StarCoordinatesChart = None
ParallelCoordinatesChart = None
GroupedBarChart = None
LinePlotChart = None
HorizontalBarChart = None
HexbinChart = None
ErrorbarsChart = None
FillBetweenChart = None
StepPlotChart = None
KdeChart = None
DistplotChart = None
RugChart = None
QqplotChart = None
EcdfChart = None
RidgelineChart = None
RibbonChart = None
Hist2dChart = None
PolarChart = None
FunnelChart = None

# Función helper para importar charts de forma defensiva
def _safe_import_chart(module_name, chart_name):
    """Importa un chart de forma segura, manejando errores de importación"""
    try:
        module = __import__(f'.{module_name}', fromlist=[chart_name], level=1)
        return getattr(module, chart_name, None)
    except (ImportError, AttributeError, Exception) as e:
        # Silenciar errores de importación para permitir que otros charts se importen
        return None

# Importar gráficos básicos
try:
    from .scatter import ScatterChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .bar import BarChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .histogram import HistogramChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .boxplot import BoxplotChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .heatmap import HeatmapChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .line import LineChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .pie import PieChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .violin import ViolinChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .radviz import RadvizChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .star_coordinates import StarCoordinatesChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .parallel_coordinates import ParallelCoordinatesChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .grouped_bar import GroupedBarChart
except (ImportError, AttributeError, Exception):
    pass

# Nuevos gráficos
try:
    from .line_plot import LinePlotChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .horizontal_bar import HorizontalBarChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .hexbin import HexbinChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .errorbars import ErrorbarsChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .fill_between import FillBetweenChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .step_plot import StepPlotChart
except (ImportError, AttributeError, Exception):
    pass

# Gráficos avanzados
try:
    from .kde import KdeChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .distplot import DistplotChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .rug import RugChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .qqplot import QqplotChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .ecdf import EcdfChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .ridgeline import RidgelineChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .ribbon import RibbonChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .hist2d import Hist2dChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .polar import PolarChart
except (ImportError, AttributeError, Exception):
    pass

try:
    from .funnel import FunnelChart
except (ImportError, AttributeError, Exception):
    pass

# Registrar todos los gráficos automáticamente (solo los que se importaron correctamente)
if ScatterChart is not None:
    ChartRegistry.register(ScatterChart)
if BarChart is not None:
    ChartRegistry.register(BarChart)
if HistogramChart is not None:
    ChartRegistry.register(HistogramChart)
if BoxplotChart is not None:
    ChartRegistry.register(BoxplotChart)
if HeatmapChart is not None:
    ChartRegistry.register(HeatmapChart)
if LineChart is not None:
    ChartRegistry.register(LineChart)
if PieChart is not None:
    ChartRegistry.register(PieChart)
if ViolinChart is not None:
    ChartRegistry.register(ViolinChart)
if RadvizChart is not None:
    ChartRegistry.register(RadvizChart)
if StarCoordinatesChart is not None:
    ChartRegistry.register(StarCoordinatesChart)
if ParallelCoordinatesChart is not None:
    ChartRegistry.register(ParallelCoordinatesChart)
if GroupedBarChart is not None:
    ChartRegistry.register(GroupedBarChart)

# Registrar nuevos gráficos
if LinePlotChart is not None:
    ChartRegistry.register(LinePlotChart)
if HorizontalBarChart is not None:
    ChartRegistry.register(HorizontalBarChart)
if HexbinChart is not None:
    ChartRegistry.register(HexbinChart)
if ErrorbarsChart is not None:
    ChartRegistry.register(ErrorbarsChart)
if FillBetweenChart is not None:
    ChartRegistry.register(FillBetweenChart)
if StepPlotChart is not None:
    ChartRegistry.register(StepPlotChart)

# Registrar gráficos avanzados
if KdeChart is not None:
    ChartRegistry.register(KdeChart)
if DistplotChart is not None:
    ChartRegistry.register(DistplotChart)
if RugChart is not None:
    ChartRegistry.register(RugChart)
if QqplotChart is not None:
    ChartRegistry.register(QqplotChart)
if EcdfChart is not None:
    ChartRegistry.register(EcdfChart)
if RidgelineChart is not None:
    ChartRegistry.register(RidgelineChart)
if RibbonChart is not None:
    ChartRegistry.register(RibbonChart)
if Hist2dChart is not None:
    ChartRegistry.register(Hist2dChart)
if PolarChart is not None:
    ChartRegistry.register(PolarChart)
if FunnelChart is not None:
    ChartRegistry.register(FunnelChart)

__all__ = [
    'ChartBase',
    'ChartRegistry',
    'ScatterChart',
    'BarChart',
    'HistogramChart',
    'BoxplotChart',
    'HeatmapChart',
    'LineChart',
    'PieChart',
    'ViolinChart',
    'RadvizChart',
    'StarCoordinatesChart',
    'ParallelCoordinatesChart',
    'GroupedBarChart',
    'LinePlotChart',
    'HorizontalBarChart',
    'HexbinChart',
    'ErrorbarsChart',
    'FillBetweenChart',
    'StepPlotChart',
    'KdeChart',
    'DistplotChart',
    'RugChart',
    'QqplotChart',
    'EcdfChart',
    'RidgelineChart',
    'RibbonChart',
    'Hist2dChart',
    'PolarChart',
    'FunnelChart'
]

