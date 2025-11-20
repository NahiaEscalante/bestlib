"""
Charts module - Sistema extensible de gráficos para BESTLIB
"""
from .base import ChartBase
from .registry import ChartRegistry

# Importar gráficos para registro automático
from .scatter import ScatterChart
from .bar import BarChart
from .histogram import HistogramChart
from .boxplot import BoxplotChart
from .heatmap import HeatmapChart
from .line import LineChart
from .pie import PieChart
from .violin import ViolinChart
from .radviz import RadvizChart
from .star_coordinates import StarCoordinatesChart
from .parallel_coordinates import ParallelCoordinatesChart
from .grouped_bar import GroupedBarChart

# Nuevos gráficos
from .line_plot import LinePlotChart
from .horizontal_bar import HorizontalBarChart
from .hexbin import HexbinChart
from .errorbars import ErrorbarsChart
from .fill_between import FillBetweenChart
from .step_plot import StepPlotChart

# Gráficos avanzados
from .kde import KdeChart
from .distplot import DistplotChart
from .rug import RugChart
from .qqplot import QqplotChart
from .ecdf import EcdfChart
from .ridgeline import RidgelineChart
from .ribbon import RibbonChart
from .hist2d import Hist2dChart
from .polar import PolarChart
from .funnel import FunnelChart

# Registrar todos los gráficos automáticamente
ChartRegistry.register(ScatterChart)
ChartRegistry.register(BarChart)
ChartRegistry.register(HistogramChart)
ChartRegistry.register(BoxplotChart)
ChartRegistry.register(HeatmapChart)
ChartRegistry.register(LineChart)
ChartRegistry.register(PieChart)
ChartRegistry.register(ViolinChart)
ChartRegistry.register(RadvizChart)
ChartRegistry.register(StarCoordinatesChart)
ChartRegistry.register(ParallelCoordinatesChart)
ChartRegistry.register(GroupedBarChart)

# Registrar nuevos gráficos
ChartRegistry.register(LinePlotChart)
ChartRegistry.register(HorizontalBarChart)
ChartRegistry.register(HexbinChart)
ChartRegistry.register(ErrorbarsChart)
ChartRegistry.register(FillBetweenChart)
ChartRegistry.register(StepPlotChart)

# Registrar gráficos avanzados
ChartRegistry.register(KdeChart)
ChartRegistry.register(DistplotChart)
ChartRegistry.register(RugChart)
ChartRegistry.register(QqplotChart)
ChartRegistry.register(EcdfChart)
ChartRegistry.register(RidgelineChart)
ChartRegistry.register(RibbonChart)
ChartRegistry.register(Hist2dChart)
ChartRegistry.register(PolarChart)
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

