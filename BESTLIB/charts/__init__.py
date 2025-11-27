"""
Charts module - Sistema extensible de gráficos para BESTLIB
"""
from .base import ChartBase
from .registry import ChartRegistry

# ============================================================
# IMPORTACIÓN PRIORITARIA — Scatter y Boxplot
# ============================================================

ScatterChart = None
BoxplotChart = None

try:
    from .scatter import ScatterChart as _ScatterChart
    ScatterChart = _ScatterChart
except Exception as e:
    print("❌ Error al importar ScatterChart:", e)
    ScatterChart = None

try:
    from .boxplot import BoxplotChart as _BoxplotChart
    BoxplotChart = _BoxplotChart
except Exception as e:
    print("❌ Error al importar BoxplotChart:", e)
    BoxplotChart = None

# Registrar primero estos dos
if ScatterChart is not None:
    ChartRegistry.register(ScatterChart)
if BoxplotChart is not None:
    ChartRegistry.register(BoxplotChart)



# ============================================================
# IMPORTACIÓN SEGURA DEL RESTO DE GRÁFICOS
# ============================================================

def _safe(name, attr):
    """Evita que errores de otros charts rompan scatter y boxplot."""
    try:
        module = __import__(f'.{name}', fromlist=[attr], level=1)
        return getattr(module, attr, None)
    except Exception:
        return None

BarChart = _safe("bar", "BarChart")
HistogramChart = _safe("histogram", "HistogramChart")
HeatmapChart = _safe("heatmap", "HeatmapChart")
LineChart = _safe("line", "LineChart")
PieChart = _safe("pie", "PieChart")
ViolinChart = _safe("violin", "ViolinChart")
RadvizChart = _safe("radviz", "RadvizChart")
StarCoordinatesChart = _safe("star_coordinates", "StarCoordinatesChart")
ParallelCoordinatesChart = _safe("parallel_coordinates", "ParallelCoordinatesChart")
GroupedBarChart = _safe("grouped_bar", "GroupedBarChart")
LinePlotChart = _safe("line_plot", "LinePlotChart")
HorizontalBarChart = _safe("horizontal_bar", "HorizontalBarChart")
HexbinChart = _safe("hexbin", "HexbinChart")
ErrorbarsChart = _safe("errorbars", "ErrorbarsChart")
FillBetweenChart = _safe("fill_between", "FillBetweenChart")
StepPlotChart = _safe("step_plot", "StepPlotChart")
KdeChart = _safe("kde", "KdeChart")
DistplotChart = _safe("distplot", "DistplotChart")
RugChart = _safe("rug", "RugChart")
QqplotChart = _safe("qqplot", "QqplotChart")
EcdfChart = _safe("ecdf", "EcdfChart")
RidgelineChart = _safe("ridgeline", "RidgelineChart")
RibbonChart = _safe("ribbon", "RibbonChart")
Hist2dChart = _safe("hist2d", "Hist2dChart")
PolarChart = _safe("polar", "PolarChart")
FunnelChart = _safe("funnel", "FunnelChart")

# Registrar solo los que se importaron bien (sin afectar scatter/boxplot)
for chart in [
    BarChart, HistogramChart, HeatmapChart, LineChart, PieChart, ViolinChart,
    RadvizChart, StarCoordinatesChart, ParallelCoordinatesChart, GroupedBarChart,
    LinePlotChart, HorizontalBarChart, HexbinChart, ErrorbarsChart, FillBetweenChart,
    StepPlotChart, KdeChart, DistplotChart, RugChart, QqplotChart, EcdfChart,
    RidgelineChart, RibbonChart, Hist2dChart, PolarChart, FunnelChart
]:
    if chart is not None:
        ChartRegistry.register(chart)


__all__ = [
    'ChartBase',
    'ChartRegistry',
    'ScatterChart',
    'BoxplotChart',
    'BarChart',
    'HistogramChart',
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
    'FunnelChart',
]
