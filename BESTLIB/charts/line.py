"""Line Chart"""
from .base import ChartBase
from ..data.preparators import prepare_line_data
from ..core.exceptions import ChartError


class LineChart(ChartBase):
    @property
    def chart_type(self):
        return 'line'
    
    def validate_data(self, data, x_col=None, y_col=None, **kwargs):
        if not x_col or not y_col:
            raise ChartError("x_col e y_col son requeridos para line plot")
    
    def prepare_data(self, data, x_col=None, y_col=None, series_col=None, **kwargs):
        return prepare_line_data(data, x_col=x_col, y_col=y_col, series_col=series_col)
    
    def get_spec(self, data, x_col=None, y_col=None, series_col=None, **kwargs):
        self.validate_data(data, x_col=x_col, y_col=y_col, **kwargs)
        line_data = self.prepare_data(data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
        return {'type': self.chart_type, **line_data, **kwargs}

