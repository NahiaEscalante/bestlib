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
    'GroupedBarChart'
]

