"""
2D Histogram Chart para BESTLIB
Histograma bidimensional (heatmap de densidad)
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


class Hist2dChart(ChartBase):
    """Gráfico histograma 2D (heatmap de densidad)"""
    
    @property
    def chart_type(self):
        return 'hist2d'
    
    def validate_data(self, data, x_col=None, y_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para hist2d.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not x_col or not y_col:
            raise ChartError("x_col e y_col son requeridos para hist2d")
        
        try:
            validate_scatter_data(data, x_col, y_col)
        except DataError as e:
            raise ChartError(f"Datos inválidos para hist2d: {e}")
    
    def prepare_data(self, data, x_col=None, y_col=None, bins=20, **kwargs):
        """
        Prepara datos para hist2d.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            bins: Número de bins (puede ser int o [int, int])
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con bins y conteos
        """
        if not HAS_NUMPY:
            raise ChartError("numpy es requerido para hist2d")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            x_values = data[x_col].dropna().values
            y_values = data[y_col].dropna().values
        else:
            x_values = np.array([d[x_col] for d in data if x_col in d and d[x_col] is not None])
            y_values = np.array([d[y_col] for d in data if y_col in d and d[y_col] is not None])
        
        if len(x_values) == 0 or len(y_values) == 0:
            raise ChartError("No hay datos válidos para hist2d")
        
        # Determinar bins
        if isinstance(bins, (list, tuple)) and len(bins) == 2:
            bins_x, bins_y = bins
        else:
            bins_x = bins_y = int(bins)
        
        # Calcular histograma 2D
        hist, x_edges, y_edges = np.histogram2d(x_values, y_values, bins=[bins_x, bins_y])
        
        # Crear datos para heatmap
        hist2d_data = []
        for i in range(len(x_edges) - 1):
            for j in range(len(y_edges) - 1):
                hist2d_data.append({
                    'x': float((x_edges[i] + x_edges[i+1]) / 2),
                    'y': float((y_edges[j] + y_edges[j+1]) / 2),
                    'value': float(hist[i, j]),
                    'x_bin_start': float(x_edges[i]),
                    'x_bin_end': float(x_edges[i+1]),
                    'y_bin_start': float(y_edges[j]),
                    'y_bin_end': float(y_edges[j+1])
                })
        
        return {'data': hist2d_data}
    
    def get_spec(self, data, x_col=None, y_col=None, bins=20, **kwargs):
        """
        Genera la especificación del hist2d.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            bins: Número de bins
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        self.validate_data(data, x_col=x_col, y_col=y_col, **kwargs)
        
        hist2d_data = self.prepare_data(
            data,
            x_col=x_col,
            y_col=y_col,
            bins=bins,
            **kwargs
        )
        
        process_figsize_in_kwargs(kwargs)
        
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs and y_col:
            kwargs['yLabel'] = y_col
        
        spec = {
            'type': self.chart_type,
            'data': hist2d_data['data'],
        }
        
        encoding = {}
        if x_col:
            encoding['x'] = {'field': x_col}
        if y_col:
            encoding['y'] = {'field': y_col}
        encoding['value'] = {'field': 'count'}
        
        if encoding:
            spec['encoding'] = encoding
        
        options = {}
        for key in ['bins', 'colorScale', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if 'bins' not in options:
            options['bins'] = bins
        if 'colorScale' not in options:
            options['colorScale'] = 'Blues'
        
        if options:
            spec['options'] = options
        
        spec.update(kwargs)
        return spec

