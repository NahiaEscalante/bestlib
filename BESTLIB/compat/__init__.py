"""
Compat module - Wrappers de compatibilidad hacia atrás
"""
from .matrix_wrapper import MatrixLayoutCompat
from .chart_wrappers import (
    map_scatter,
    map_barchart,
    map_histogram,
    map_boxplot,
    map_heatmap,
    map_line,
    map_pie,
    map_grouped_barchart
)

__all__ = [
    'MatrixLayoutCompat',
    'map_scatter',
    'map_barchart',
    'map_histogram',
    'map_boxplot',
    'map_heatmap',
    'map_line',
    'map_pie',
    'map_grouped_barchart'
]

