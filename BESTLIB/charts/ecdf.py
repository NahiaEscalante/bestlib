"""
ECDF (Empirical Cumulative Distribution Function) Chart para BESTLIB
Función de distribución acumulativa empírica
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
            # Pandas está corrupto, limpiarlo
            del sys.modules['pandas']
            modules_to_remove = [k for k in list(sys.modules.keys()) if k.startswith('pandas.')]
            for mod in modules_to_remove:
                try:
                    del sys.modules[mod]
                except:
                    pass
    # Intentar importar pandas limpio
    import pandas as pd
    # Verificar que pandas esté completamente inicializado
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


class EcdfChart(ChartBase):
    """Gráfico ECDF (Empirical Cumulative Distribution Function)"""
    
    @property
    def chart_type(self):
        return 'ecdf'
    
    def validate_data(self, data, column=None, **kwargs):
        """
        Valida que los datos sean adecuados para ECDF.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not column:
            raise ChartError("column es requerido para ECDF")
        
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
        Prepara datos para ECDF.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con valores y probabilidades acumulativas
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            values = data[column].dropna().values
        else:
            values = [d[column] for d in data if column in d and d[column] is not None]
            if HAS_NUMPY:
                values = np.array(values)
        
        if len(values) == 0:
            raise ChartError("No hay datos válidos para ECDF")
        
        if not HAS_NUMPY:
            # Fallback sin numpy
            sorted_values = sorted(values)
            n = len(sorted_values)
            ecdf_data = []
            for i, val in enumerate(sorted_values):
                ecdf_data.append({
                    'x': float(val),
                    'y': float((i + 1) / n)  # Probabilidad acumulativa
                })
        else:
            # Ordenar valores
            sorted_values = np.sort(values)
            n = len(sorted_values)
            
            # Calcular ECDF: para cada valor, la proporción de datos <= valor
            ecdf_data = []
            for i, val in enumerate(sorted_values):
                try:
                    ecdf_data.append({
                        'x': float(val) if not np.isnan(val) else 0.0,
                        'y': float((i + 1) / n)  # Probabilidad acumulativa
                    })
                except (ValueError, TypeError, OverflowError):
                    continue  # Saltar valores inválidos
        
        if len(ecdf_data) == 0:
            raise ChartError("No se pudieron generar datos para ECDF")
        
        return {'data': ecdf_data}
    
    def get_spec(self, data, column=None, **kwargs):
        """
        Genera la especificación del ECDF.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, column=column, **kwargs)
        
        # Preparar datos
        ecdf_data = self.prepare_data(
            data,
            column=column,
            **kwargs
        )
        
        # Procesar figsize si está en kwargs
        process_figsize_in_kwargs(kwargs)
        
        # Agregar etiquetas de ejes automáticamente
        if 'xLabel' not in kwargs and column:
            kwargs['xLabel'] = column
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = 'Cumulative Probability'
        
        # Construir spec
        spec = {
            'type': self.chart_type,
            'data': ecdf_data['data'],
        }
        
        # Agregar encoding
        encoding = {}
        if column:
            encoding['x'] = {'field': column}
        encoding['y'] = {'field': 'cumulative_probability'}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['color', 'strokeWidth', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive', 'step']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        # Valores por defecto
        if 'color' not in options:
            options['color'] = '#4a90e2'
        if 'strokeWidth' not in options:
            options['strokeWidth'] = 2
        if 'step' not in options:
            options['step'] = True  # Usar step plot por defecto para ECDF
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

