"""
Q-Q Plot Chart para BESTLIB
Quantile-Quantile plot para comparar distribuciones
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


class QqplotChart(ChartBase):
    """Gráfico Q-Q plot (Quantile-Quantile)"""
    
    @property
    def chart_type(self):
        return 'qqplot'
    
    def validate_data(self, data, column=None, dist='norm', **kwargs):
        """
        Valida que los datos sean adecuados para Q-Q plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            dist: Distribución teórica ('norm', 'uniform', etc.)
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not column:
            raise ChartError("column es requerido para Q-Q plot")
        
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
    
    def prepare_data(self, data, column=None, dist='norm', **kwargs):
        """
        Prepara datos para Q-Q plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            dist: Distribución teórica ('norm', 'uniform', etc.)
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con quantiles teóricos y observados
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            values = data[column].dropna().values
        else:
            values = [d[column] for d in data if column in d and d[column] is not None]
            if HAS_NUMPY:
                values = np.array(values)
        
        if len(values) == 0:
            raise ChartError("No hay datos válidos para Q-Q plot")
        
        if not HAS_NUMPY:
            raise ChartError("numpy es requerido para Q-Q plot")
        
        # Ordenar valores
        sorted_values = np.sort(values)
        n = len(sorted_values)
        
        # Calcular quantiles observados
        observed_quantiles = sorted_values
        
        # Calcular quantiles teóricos
        try:
            from scipy import stats
            if dist == 'norm':
                # Distribución normal estándar
                theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, n))
            elif dist == 'uniform':
                # Distribución uniforme
                theoretical_quantiles = stats.uniform.ppf(np.linspace(0.01, 0.99, n))
            else:
                # Por defecto, normal
                theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, n))
        except ImportError:
            # Fallback: usar aproximación normal sin scipy
            # Usar percentiles aproximados
            theoretical_quantiles = np.linspace(-2.5, 2.5, n)
        
        # Crear datos para el plot
        qq_data = []
        for tq, oq in zip(theoretical_quantiles, observed_quantiles):
            try:
                qq_data.append({
                    'x': float(tq) if not np.isnan(tq) else 0.0,
                    'y': float(oq) if not np.isnan(oq) else 0.0
                })
            except (ValueError, TypeError, OverflowError):
                continue  # Saltar valores inválidos
        
        if len(qq_data) == 0:
            raise ChartError("No se pudieron generar datos para Q-Q plot")
        
        return {'data': qq_data, 'dist': dist}
    
    def get_spec(self, data, column=None, dist='norm', **kwargs):
        """
        Genera la especificación del Q-Q plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            dist: Distribución teórica ('norm', 'uniform', etc.)
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, column=column, dist=dist, **kwargs)
        
        # Preparar datos
        qq_data = self.prepare_data(
            data,
            column=column,
            dist=dist,
            **kwargs
        )
        
        # Procesar figsize si está en kwargs
        process_figsize_in_kwargs(kwargs)
        
        # Agregar etiquetas de ejes automáticamente
        if 'xLabel' not in kwargs:
            kwargs['xLabel'] = f'Theoretical Quantiles ({dist})'
        if 'yLabel' not in kwargs and column:
            kwargs['yLabel'] = f'Observed Quantiles ({column})'
        
        # Construir spec
        spec = {
            'type': self.chart_type,
            'data': qq_data['data'],
        }
        
        # Agregar encoding
        encoding = {}
        encoding['x'] = {'field': 'theoretical'}
        encoding['y'] = {'field': 'observed'}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['dist', 'color', 'strokeWidth', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive', 'showLine']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        # Valores por defecto
        if 'dist' not in options:
            options['dist'] = dist
        if 'color' not in options:
            options['color'] = '#4a90e2'
        if 'strokeWidth' not in options:
            options['strokeWidth'] = 2
        if 'showLine' not in options:
            options['showLine'] = True  # Mostrar línea de referencia
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

