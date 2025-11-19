"""Pie Chart"""
from .base import ChartBase
from ..data.preparators import prepare_pie_data
from ..core.exceptions import ChartError


class PieChart(ChartBase):
    @property
    def chart_type(self):
        return 'pie'
    
    def validate_data(self, data, category_col=None, **kwargs):
        if not category_col:
            raise ChartError("category_col es requerido para pie chart")
    
    def prepare_data(self, data, category_col=None, value_col=None, **kwargs):
        return prepare_pie_data(data, category_col=category_col, value_col=value_col)
    
    def get_spec(self, data, category_col=None, value_col=None, **kwargs):
        self.validate_data(data, category_col=category_col, **kwargs)
        pie_data = self.prepare_data(data, category_col=category_col, value_col=value_col, **kwargs)
        return {'type': self.chart_type, 'data': pie_data, **kwargs}

