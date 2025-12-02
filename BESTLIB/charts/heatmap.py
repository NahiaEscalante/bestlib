"""Heatmap Chart"""
from .base import ChartBase
from ..data.preparators import prepare_heatmap_data
from ..core.exceptions import ChartError


class HeatmapChart(ChartBase):
    @property
    def chart_type(self):
        return 'heatmap'
    
    def validate_data(self, data, **kwargs):
        pass
    
    def prepare_data(self, data, x_col=None, y_col=None, value_col=None, **kwargs):
        cells, x_labels, y_labels = prepare_heatmap_data(data, x_col=x_col, y_col=y_col, value_col=value_col)
        return {'cells': cells, 'x_labels': x_labels, 'y_labels': y_labels}
    
    def get_spec(self, data, x_col=None, y_col=None, value_col=None, **kwargs):
        prepared = self.prepare_data(data, x_col=x_col, y_col=y_col, value_col=value_col, **kwargs)
        # Agregar 'data' para compatibilidad con validate_spec
        return {'type': self.chart_type, 'data': prepared['cells'], **prepared, **kwargs}

