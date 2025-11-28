# charts/horizontal_bar.py
"""
Horizontal Bar Chart para BESTLIB
"""
from .base import ChartBase
from ..data.preparators import prepare_horizontal_bar_data
from ..data.validators import validate_horizontal_bar_data
from ..core.exceptions import ChartError, DataError
from ..utils.figsize import process_figsize_in_kwargs

class HorizontalBarChart(ChartBase):
    """Gráfico de Barras Horizontales con soporte para tooltips y selección"""
    
    @property
    def chart_type(self):
        return 'horizontal_bar'
    
    def validate_data(self, data, category_col=None, **kwargs):
        """Valida datos para horizontal bar chart"""
        if not category_col:
            raise ChartError("category_col es requerido para horizontal_bar chart")
        
        try:
            validate_horizontal_bar_data(
                data, 
                category_col=category_col, 
                value_col=kwargs.get('value_col')
            )
        except DataError as e:
            raise ChartError(f"Datos inválidos para horizontal_bar chart: {e}")
    
    def prepare_data(self, data, category_col=None, value_col=None, **kwargs):
        """Prepara datos para horizontal bar chart"""
        return prepare_horizontal_bar_data(
            data, 
            category_col=category_col, 
            value_col=value_col,
            **kwargs
        )
    
    def get_spec(self, data, category_col=None, value_col=None, **kwargs):
        """Genera spec para horizontal bar chart"""
        self.validate_data(data, category_col=category_col, **kwargs)
        bar_data = self.prepare_data(
            data, 
            category_col=category_col, 
            value_col=value_col, 
            **kwargs
        )
        
        process_figsize_in_kwargs(kwargs)
        
        # Configuración por defecto
        if 'xLabel' not in kwargs and value_col:
            kwargs['xLabel'] = value_col
        if 'yLabel' not in kwargs and category_col:
            kwargs['yLabel'] = category_col
        
        # Configuración específica para barras horizontales
        bar_height = kwargs.pop('bar_height', 25)
        bar_gap = kwargs.pop('bar_gap', 5)
        
        spec = {
            'type': self.chart_type,
            'data': bar_data,
            'options': {
                'category_col': category_col,
                'value_col': value_col,
                'bar_height': bar_height,
                'gap': bar_gap,
                'interactive': kwargs.pop('interactive', True),
                'tooltip': kwargs.pop('tooltip', True),
                'hover': kwargs.pop('hover', True)
            }
        }
        
        # Añadir opciones adicionales
        for key in ['color', 'colorMap', 'title', 'xLabel', 'yLabel', 'figsize']:
            if key in kwargs:
                spec['options'][key] = kwargs[key]
        
        # Mantener compatibilidad con opciones adicionales
        spec['options'].update({
            k: v for k, v in kwargs.items() 
            if k not in spec['options'] and not k.startswith('_')
        })
        
        return spec