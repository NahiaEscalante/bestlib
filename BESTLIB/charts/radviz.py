"""Radviz Chart - Placeholder"""
from .base import ChartBase


class RadvizChart(ChartBase):
    @property
    def chart_type(self):
        return 'radviz'
    
    def validate_data(self, data, **kwargs):
        pass
    
    def prepare_data(self, data, **kwargs):
        return []
    
    def get_spec(self, data, **kwargs):
        return {'type': self.chart_type, 'data': [], **kwargs}

