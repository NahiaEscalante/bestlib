"""
Bar Chart para BESTLIB
"""
from .base import ChartBase
from ..data.preparators import prepare_bar_data
from ..data.validators import validate_bar_data
from ..utils.figsize import process_figsize_in_kwargs
from ..core.exceptions import ChartError, DataError


class BarChart(ChartBase):
    """Gráfico de Barras"""
    
    @property
    def chart_type(self):
        return 'bar'
    
    def validate_data(self, data, category_col=None, **kwargs):
        """Valida datos para bar chart"""
        if not category_col:
            raise ChartError("category_col es requerido para bar chart")
        
        try:
            validate_bar_data(data, category_col, value_col=kwargs.get('value_col'))
        except DataError as e:
            raise ChartError(f"Datos inválidos para bar chart: {e}")
    
    def prepare_data(self, data, category_col=None, value_col=None, **kwargs):
        """Prepara datos para bar chart"""
        return prepare_bar_data(data, category_col=category_col, value_col=value_col)
    
    def get_spec(self, data, category_col=None, value_col=None, **kwargs):
        """Genera spec para bar chart"""
        self.validate_data(data, category_col=category_col, **kwargs)
        bar_data = self.prepare_data(data, category_col=category_col, value_col=value_col, **kwargs)
        
        process_figsize_in_kwargs(kwargs)
        
        if 'xLabel' not in kwargs and category_col:
            kwargs['xLabel'] = category_col
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = value_col if value_col else 'Count'
        
        spec = {
            'type': self.chart_type,
            'data': bar_data,
        }
        
        encoding = {}
        if category_col:
            encoding['x'] = {'field': category_col}
        if value_col:
            encoding['y'] = {'field': value_col}
        
        if encoding:
            spec['encoding'] = encoding
        
        options = {}
        for key in ['color', 'colorMap', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if options:
            spec['options'] = options
        
        spec.update(kwargs)
        return spec

