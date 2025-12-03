"""
KDE (Kernel Density Estimation) Chart para BESTLIB
Estimación de densidad de kernel
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


class KdeChart(ChartBase):
    """Gráfico de estimación de densidad de kernel (KDE)"""
    
    @property
    def chart_type(self):
        return 'kde'
    
    def validate_data(self, data, column=None, **kwargs):
        """
        Valida que los datos sean adecuados para KDE.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not column:
            raise ChartError("column es requerido para KDE")
        
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
    
    def prepare_data(self, data, column=None, bandwidth=None, rug=False, **kwargs):
        """
        Prepara datos para KDE calculando la densidad.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            bandwidth: Ancho de banda para KDE (opcional)
            rug: Si True, incluye datos para rug plot
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con 'x' y 'y' (densidad), y opcionalmente 'rug_data'
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            values = data[column].dropna().values
        else:
            values = [d[column] for d in data if column in d and d[column] is not None]
            if HAS_NUMPY:
                values = np.array(values)
        
        if len(values) == 0:
            raise ChartError("No hay datos válidos para calcular KDE")
        
        # Asegurar que values sea un array numpy para el procesamiento
        if HAS_NUMPY and not isinstance(values, np.ndarray):
            values = np.array(values)
        
        # Calcular KDE usando scipy si está disponible, sino usar numpy
        try:
            from scipy.stats import gaussian_kde
            if bandwidth:
                kde = gaussian_kde(values, bw_method=bandwidth)
            else:
                kde = gaussian_kde(values)
            
            # Crear rango de valores para evaluar
            x_min, x_max = float(np.min(values)), float(np.max(values))
            x_range = x_max - x_min
            if x_range == 0:
                # Si todos los valores son iguales, crear un rango pequeño alrededor del valor
                x_min = x_min - 0.1
                x_max = x_max + 0.1
                x_range = 0.2
            x_padding = x_range * 0.1  # 10% padding
            x_eval = np.linspace(x_min - x_padding, x_max + x_padding, 200)
            y_density = kde(x_eval)
            
            # Convertir a lista de puntos - asegurar que sean tipos Python nativos
            kde_data = []
            for x, y in zip(x_eval, y_density):
                try:
                    kde_data.append({
                        'x': float(x) if not np.isnan(x) else 0.0,
                        'y': float(y) if not np.isnan(y) else 0.0
                    })
                except (ValueError, TypeError, OverflowError):
                    # Si hay un error de conversión, usar 0.0
                    kde_data.append({'x': 0.0, 'y': 0.0})
        except ImportError:
            # Fallback: usar histograma normalizado como aproximación
            if HAS_NUMPY:
                hist, bin_edges = np.histogram(values, bins=50, density=True)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                kde_data = []
                for x, y in zip(bin_centers, hist):
                    try:
                        kde_data.append({
                            'x': float(x) if not np.isnan(x) else 0.0,
                            'y': float(y) if not np.isnan(y) else 0.0
                        })
                    except (ValueError, TypeError, OverflowError):
                        kde_data.append({'x': 0.0, 'y': 0.0})
            else:
                raise ChartError("Se requiere scipy o numpy para calcular KDE")
        except Exception as e:
            # Capturar cualquier otro error y proporcionar un mensaje más informativo
            raise ChartError(f"Error al calcular KDE: {e}")
        
        if len(kde_data) == 0:
            raise ChartError("No se pudieron generar datos para KDE")
        
        result = {'data': kde_data}
        
        # Si se solicita rug plot, agregar los datos originales
        if rug:
            rug_data = []
            for val in values:
                try:
                    float_val = float(val)
                    if HAS_NUMPY and np.isnan(float_val):
                        continue
                    rug_data.append({'x': float_val})
                except (ValueError, TypeError, OverflowError):
                    continue
            
            if len(rug_data) > 0:
                result['rug_data'] = rug_data
        
        return result
    
    def get_spec(self, data, column=None, bandwidth=None, rug=False, **kwargs):
        """
        Genera la especificación del KDE.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            bandwidth: Ancho de banda para KDE (opcional)
            rug: Si True, muestra rug plot debajo del KDE
            **kwargs: Opciones adicionales (color, strokeWidth, axes, etc.)
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, column=column, **kwargs)
        
        # Preparar datos
        kde_result = self.prepare_data(
            data,
            column=column,
            bandwidth=bandwidth,
            rug=rug,
            **kwargs
        )
        
        # Procesar figsize si está en kwargs
        process_figsize_in_kwargs(kwargs)
        
        # Agregar etiquetas de ejes automáticamente
        if 'xLabel' not in kwargs and column:
            kwargs['xLabel'] = column
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = 'Density'
        
        # Construir spec
        spec = {
            'type': self.chart_type,
            'data': kde_result['data'],
        }
        
        # Agregar rug data si existe
        if 'rug_data' in kde_result:
            spec['rugData'] = kde_result['rug_data']
        
        # Agregar encoding
        encoding = {}
        if column:
            encoding['x'] = {'field': column}
        encoding['y'] = {'field': 'density'}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['color', 'strokeWidth', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive', 'fill', 'opacity', 'rug', 'rugColor', 'rugSize', 'rugOpacity']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        # Valores por defecto
        if 'color' not in options:
            options['color'] = '#4a90e2'
        if 'strokeWidth' not in options:
            options['strokeWidth'] = 2
        if 'fill' not in options:
            options['fill'] = True
        if 'opacity' not in options:
            options['opacity'] = 0.3
        if rug:
            options['rug'] = True
            if 'rugColor' not in options:
                options['rugColor'] = options['color']
            if 'rugSize' not in options:
                options['rugSize'] = 2
            if 'rugOpacity' not in options:
                options['rugOpacity'] = 0.6
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

