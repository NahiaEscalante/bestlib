"""
Rug Plot Chart para BESTLIB
Marcadores en el eje para mostrar distribución de datos
"""
from .base import ChartBase
from ..data.validators import validate_scatter_data
from ..utils.figsize import process_figsize_in_kwargs
from ..core.exceptions import ChartError, DataError

# Import de pandas y numpy de forma defensiva para evitar errores de importación circular
import sys  # sys siempre está disponible, importarlo fuera del try
HAS_PANDAS = False
HAS_NUMPY = False
pd = None
np = None
try:
    # Verificar que pandas no esté parcialmente inicializado
    if 'pandas' in sys.modules:
        try:
            pd_test = sys.modules['pandas']
            _ = pd_test.__version__
        except (AttributeError, ImportError):
            del sys.modules['pandas']
            modules_to_remove = [k for k in list(sys.modules.keys()) if k.startswith('pandas.')]
            for mod in modules_to_remove:
                try:
                    del sys.modules[mod]
                except:
                    pass
    import pandas as pd
    _ = pd.__version__
    HAS_PANDAS = True
except (ImportError, AttributeError, ModuleNotFoundError, Exception):
    HAS_PANDAS = False
    pd = None

try:
    import numpy as np
    HAS_NUMPY = True
except (ImportError, AttributeError, ModuleNotFoundError, Exception):
    HAS_NUMPY = False
    np = None


class RugChart(ChartBase):
    """Gráfico rug plot (marcadores en el eje)"""
    
    @property
    def chart_type(self):
        return 'rug'
    
    def validate_data(self, data, column=None, **kwargs):
        """
        Valida que los datos sean adecuados para rug plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not column:
            raise ChartError("column es requerido para rug plot")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if column not in data.columns:
                raise ChartError(f"Columna '{column}' no encontrada en los datos")
            if not pd.api.types.is_numeric_dtype(data[column]):
                raise ChartError(f"Columna '{column}' debe ser numérica")
        else:
            if isinstance(data, list) and len(data) > 0:
                if column not in data[0]:
                    raise ChartError(f"Columna '{column}' no encontrada en los datos")
            else:
                raise ChartError("Los datos deben ser un DataFrame o lista no vacía")
    
    def prepare_data(self, data, column=None, **kwargs):
        """
        Prepara datos para rug plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con 'x' y 'y' (posiciones en el eje)
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            values = data[column].dropna().values
        else:
            values = [d[column] for d in data if column in d and d[column] is not None]
            if HAS_NUMPY:
                values = np.array(values)
        
        if len(values) == 0:
            raise ChartError("No hay datos válidos para rug plot")
        
        # Asegurar que values sea un array numpy para el procesamiento
        if HAS_NUMPY and not isinstance(values, np.ndarray):
            values = np.array(values)
        
        # Crear datos para rug plot: cada valor se marca en el eje
        # Formato: [{"x": 5.1}, {"x": 4.9}, ...] - solo 'x' es necesario
        rug_data = []
        for val in values:
            try:
                # Convertir a float y validar
                float_val = float(val)
                if HAS_NUMPY and np.isnan(float_val):
                    continue  # Saltar NaN
                rug_data.append({
                    'x': float_val
                })
            except (ValueError, TypeError, OverflowError):
                continue  # Saltar valores inválidos
        
        if len(rug_data) == 0:
            raise ChartError("No se pudieron generar datos para rug plot")
        
        return {'data': rug_data}
    
    def get_spec(self, data, column=None, axis='x', **kwargs):
        """
        Genera la especificación del rug plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            axis: Eje donde mostrar rug ('x' o 'y')
            **kwargs: Opciones adicionales (color, size, opacity, etc.)
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, column=column, **kwargs)
        
        # Preparar datos
        rug_data = self.prepare_data(
            data,
            column=column,
            **kwargs
        )
        
        # Procesar figsize si está en kwargs
        process_figsize_in_kwargs(kwargs)
        
        # Agregar etiquetas de ejes automáticamente
        if 'xLabel' not in kwargs and column and axis == 'x':
            kwargs['xLabel'] = column
        if 'yLabel' not in kwargs and column and axis == 'y':
            kwargs['yLabel'] = column
        
        # Construir spec
        spec = {
            'type': self.chart_type,
            'data': rug_data['data'],
        }
        
        # Agregar encoding
        encoding = {}
        if column:
            encoding['x' if axis == 'x' else 'y'] = {'field': column}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['color', 'size', 'opacity', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive', 'axis']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        # Valores por defecto
        if 'color' not in options:
            options['color'] = '#4a90e2'
        if 'size' not in options:
            options['size'] = 2
        if 'opacity' not in options:
            options['opacity'] = 0.6
        if 'axis' not in options:
            options['axis'] = axis
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

