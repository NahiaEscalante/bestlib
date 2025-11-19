"""Boxplot Chart"""
from .base import ChartBase
from ..data.preparators import prepare_boxplot_data
from ..core.exceptions import ChartError


class BoxplotChart(ChartBase):
    @property
    def chart_type(self):
        return 'boxplot'
    
    def validate_data(self, data, value_col=None, **kwargs):
        if not value_col:
            raise ChartError("value_col es requerido para boxplot")
    
    def prepare_data(self, data, category_col=None, value_col=None, **kwargs):
        return prepare_boxplot_data(data, category_col=category_col, value_col=value_col)
    
    def get_spec(self, data, category_col=None, value_col=None, **kwargs):
        self.validate_data(data, value_col=value_col, **kwargs)
        box_data = self.prepare_data(data, category_col=category_col, value_col=value_col, **kwargs)
        return {'type': self.chart_type, 'data': box_data, **kwargs}

