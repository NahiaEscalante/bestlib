"""Star Coordinates Chart - Placeholder"""
from .base import ChartBase


class StarCoordinatesChart(ChartBase):
    @property
    def chart_type(self):
        return 'star_coordinates'
    
    def validate_data(self, data, **kwargs):
        pass
    
    def prepare_data(self, data, **kwargs):
        return []
    
    def get_spec(self, data, **kwargs):
        return {'type': self.chart_type, 'data': [], **kwargs}

