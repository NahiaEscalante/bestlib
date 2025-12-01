"""
Histogram Chart para BESTLIB
"""
from .base import ChartBase
from ..data.preparators import prepare_histogram_data
from ..core.exceptions import ChartError


class HistogramChart(ChartBase):
    """Gráfico de Histograma"""
    
    @property
    def chart_type(self):
        return 'histogram'
    
    def validate_data(self, data, value_col=None, **kwargs):
        """Valida datos para histogram"""
        if not value_col:
            raise ChartError("value_col es requerido para histogram")
    
    def prepare_data(self, data, value_col=None, bins=10, **kwargs):
        """Prepara datos para histogram"""
        return prepare_histogram_data(data, value_col=value_col, bins=bins)
    
    def get_spec(self, data, value_col=None, bins=10, **kwargs):
        """Genera spec para histogram"""
        self.validate_data(data, value_col=value_col, **kwargs)
        hist_data = self.prepare_data(data, value_col=value_col, bins=bins, **kwargs)
        
        spec = {
            'type': self.chart_type,
            'data': hist_data,
            **kwargs
        }
        
        return spec

