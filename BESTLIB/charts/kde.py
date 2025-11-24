"""
KDE (Kernel Density Estimation) Chart para BESTLIB
Estimación de densidad de kernel
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


class KdeChart(ChartBase):
    """Gráfico de estimación de densidad de kernel (KDE)"""
    
    @property
    def chart_type(self):
        return 'kde'
    
    def validate_data(self, data, column=None, **kwargs):
        """Valida que los datos sean adecuados para KDE."""
        if not column:
            raise ChartError("column es requerido para KDE")
        
        if not HAS_PANDAS or not HAS_NUMPY:
            raise ChartError("KDE requiere pandas y numpy instalados")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if column not in data.columns:
                raise ChartError(f"Columna '{column}' no encontrada. Columnas: {list(data.columns)}")
            if not pd.api.types.is_numeric_dtype(data[column]):
                raise ChartError(f"Columna '{column}' debe ser numérica")
        else:
            if isinstance(data, list) and len(data) > 0:
                if column not in data[0]:
                    raise ChartError(f"Columna '{column}' no encontrada en los datos")
            else:
                raise ChartError("Los datos deben ser un DataFrame o lista no vacía")
    
    def prepare_data(self, data, column=None, bandwidth=None, **kwargs):
        """Prepara datos para KDE calculando la densidad."""
        # Extraer valores
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            values = data[column].dropna().values
        else:
            values = [d[column] for d in data if column in d and d[column] is not None]
            values = np.array(values)
        
        if len(values) == 0:
            raise ChartError(f"No hay datos válidos en columna '{column}'")
        
        # Calcular KDE con scipy o fallback a numpy
        try:
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(values, bw_method=bandwidth) if bandwidth else gaussian_kde(values)
            
            # Crear rango de evaluación
            x_min, x_max = float(np.min(values)), float(np.max(values))
            x_range = x_max - x_min
            x_padding = x_range * 0.1
            x_eval = np.linspace(x_min - x_padding, x_max + x_padding, 200)
            y_density = kde(x_eval)
            
        except ImportError:
            # Fallback: histograma normalizado
            hist, bin_edges = np.histogram(values, bins=50, density=True)
            x_eval = (bin_edges[:-1] + bin_edges[1:]) / 2
            y_density = hist
        
        # Convertir a lista de puntos {x, y}
        kde_data = [{'x': float(x), 'y': float(y)} for x, y in zip(x_eval, y_density)]
        
        return kde_data
    
    def get_spec(self, data, column=None, bandwidth=None, **kwargs):
        """Genera la especificación del KDE."""
        # Validar y preparar datos
        self.validate_data(data, column=column, **kwargs)
        kde_data = self.prepare_data(data, column=column, bandwidth=bandwidth, **kwargs)
        
        # Procesar figsize
        process_figsize_in_kwargs(kwargs)
        
        # Etiquetas automáticas
        if 'xLabel' not in kwargs:
            kwargs['xLabel'] = column if column else 'Value'
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = 'Density'
        
        # Construir spec simple y directo
        spec = {
            'type': self.chart_type,
            'data': kde_data,  # Lista directa de {x, y}
        }
        
        # Encoding
        spec['encoding'] = {
            'x': {'field': 'x'},
            'y': {'field': 'y'}
        }
        
        # Options con valores por defecto
        spec['options'] = {
            'color': kwargs.pop('color', '#4a90e2'),
            'strokeWidth': kwargs.pop('strokeWidth', 2),
            'fill': kwargs.pop('fill', True),
            'opacity': kwargs.pop('opacity', 0.3),
            'axes': kwargs.pop('axes', True),
            'xLabel': kwargs.pop('xLabel', column),
            'yLabel': kwargs.pop('yLabel', 'Density')
        }
        
        # Agregar figsize si existe
        if 'figsize' in kwargs:
            spec['options']['figsize'] = kwargs.pop('figsize')
        
        # Resto de kwargs
        spec.update(kwargs)
        
        return spec

