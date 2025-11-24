"""
Rug Plot Chart para BESTLIB
Marcadores en el eje para mostrar distribución de datos
"""
from .base import ChartBase
from ..utils.figsize import process_figsize_in_kwargs
from ..core.exceptions import ChartError

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
    HAS_NUMPY = True
except ImportError:
    HAS_PANDAS = False
    HAS_NUMPY = False
    pd = None
    np = None


class RugChart(ChartBase):
    """Gráfico rug plot (marcadores en el eje)"""
    
    @property
    def chart_type(self):
        return 'rug'
    
    def validate_data(self, data, column=None, **kwargs):
        """Valida que los datos sean adecuados para rug plot."""
        if not column:
            raise ChartError("column es requerido para rug plot")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if column not in data.columns:
                raise ChartError(f"Columna '{column}' no encontrada")
            if not pd.api.types.is_numeric_dtype(data[column]):
                raise ChartError(f"Columna '{column}' debe ser numérica")
    
    def prepare_data(self, data, column=None, **kwargs):
        """Prepara datos para rug plot."""
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            values = data[column].dropna().values
        else:
            values = [d[column] for d in data if column in d and d[column] is not None]
            if HAS_NUMPY:
                values = np.array(values)
        
        if len(values) == 0:
            raise ChartError("No hay datos válidos para rug plot")
        
        # Crear datos: cada valor es un marcador en el eje
        rug_data = [{'value': float(val)} for val in values]
        
        return rug_data
    
    def get_spec(self, data, column=None, axis='x', **kwargs):
        """
        Genera la especificación del rug plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            axis: Eje donde mostrar rug ('x' o 'y')
            **kwargs: Opciones adicionales
        """
        # Validar datos
        self.validate_data(data, column=column, **kwargs)
        
        # Preparar datos
        rug_data = self.prepare_data(data, column=column, **kwargs)
        
        # Procesar figsize
        process_figsize_in_kwargs(kwargs)
        
        # Extraer opciones
        color = kwargs.pop('color', '#4a90e2')
        size = kwargs.pop('size', 2)
        opacity = kwargs.pop('opacity', 0.6)
        axes = kwargs.pop('axes', True)
        x_label = kwargs.pop('xLabel', column if axis == 'x' else '')
        y_label = kwargs.pop('yLabel', column if axis == 'y' else '')
        
        # Construir spec
        spec = {
            'type': 'rug',
            'data': rug_data,
            'encoding': {
                'value': {'field': 'value'}
            },
            'options': {
                'axis': axis,
                'color': color,
                'size': size,
                'opacity': opacity,
                'axes': axes,
                'xLabel': x_label,
                'yLabel': y_label
            }
        }
        
        # Agregar figsize si existe
        if 'figsize' in kwargs:
            spec['options']['figsize'] = kwargs['figsize']
        
        # Agregar kwargs restantes
        for key, value in kwargs.items():
            if key not in spec:
                spec[key] = value
        
        return spec

