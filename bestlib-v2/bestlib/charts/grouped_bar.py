"""Grouped Bar Chart"""
from .base import ChartBase
from ..data.preparators import prepare_grouped_bar_data
from ..core.exceptions import ChartError


class GroupedBarChart(ChartBase):
    @property
    def chart_type(self):
        return 'grouped_bar'
    
    def validate_data(self, data, main_col=None, sub_col=None, **kwargs):
        if not main_col or not sub_col:
            raise ChartError("main_col y sub_col son requeridos para grouped bar")
    
    def prepare_data(self, data, main_col=None, sub_col=None, value_col=None, **kwargs):
        rows, groups, series = prepare_grouped_bar_data(data, main_col=main_col, sub_col=sub_col, value_col=value_col)
        return {'rows': rows, 'groups': groups, 'series': series}
    
    def get_spec(self, data, main_col=None, sub_col=None, value_col=None, **kwargs):
        self.validate_data(data, main_col=main_col, sub_col=sub_col, **kwargs)
        prepared = self.prepare_data(data, main_col=main_col, sub_col=sub_col, value_col=value_col, **kwargs)
        return {'type': self.chart_type, 'grouped': True, **prepared, **kwargs}

