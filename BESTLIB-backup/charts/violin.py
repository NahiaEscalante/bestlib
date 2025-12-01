"""Violin Chart - Placeholder"""
from .base import ChartBase
from ..core.exceptions import ChartError


class ViolinChart(ChartBase):
    @property
    def chart_type(self):
        return 'violin'
    
    def validate_data(self, data, **kwargs):
        pass
    
    def prepare_data(self, data, **kwargs):
        return []
    
    def get_spec(self, data, **kwargs):
        return {'type': self.chart_type, 'data': [], **kwargs}

