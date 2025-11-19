"""Parallel Coordinates Chart - Placeholder"""
from .base import ChartBase


class ParallelCoordinatesChart(ChartBase):
    @property
    def chart_type(self):
        return 'parallel_coordinates'
    
    def validate_data(self, data, **kwargs):
        pass
    
    def prepare_data(self, data, **kwargs):
        return []
    
    def get_spec(self, data, **kwargs):
        return {'type': self.chart_type, 'data': [], **kwargs}

