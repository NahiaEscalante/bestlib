"""
Ridgeline Plot Chart para BESTLIB
Gráfico de densidad apilado (joy plot)
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


class RidgelineChart(ChartBase):
    """Gráfico ridgeline (joy plot) - densidades apiladas"""
    
    @property
    def chart_type(self):
        return 'ridgeline'
    
    def validate_data(self, data, column=None, category_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para ridgeline.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            category_col: Nombre de columna de categorías
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not column:
            raise ChartError("column es requerido para ridgeline")
        if not category_col:
            raise ChartError("category_col es requerido para ridgeline")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if column not in data.columns:
                raise ChartError(f"Columna '{column}' no encontrada")
            if category_col not in data.columns:
                raise ChartError(f"Columna '{category_col}' no encontrada")
            if not pd.api.types.is_numeric_dtype(data[column]):
                raise ChartError(f"Columna '{column}' debe ser numérica")
    
    def prepare_data(self, data, column=None, category_col=None, bandwidth=None, **kwargs):
        """
        Prepara datos para ridgeline (KDE por categoría).
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            category_col: Nombre de columna de categorías
            bandwidth: Ancho de banda para KDE
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con KDE por categoría
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            categories = data[category_col].unique()
            result = {}
            
            for cat in categories:
                cat_data = data[data[category_col] == cat][column].dropna().values
                if len(cat_data) == 0:
                    continue
                
                # Calcular KDE
                try:
                    from scipy.stats import gaussian_kde
                    if bandwidth:
                        kde = gaussian_kde(cat_data, bw_method=bandwidth)
                    else:
                        kde = gaussian_kde(cat_data)
                    
                    x_min, x_max = float(np.min(cat_data)), float(np.max(cat_data))
                    x_range = x_max - x_min
                    x_padding = x_range * 0.1
                    x_eval = np.linspace(x_min - x_padding, x_max + x_padding, 200)
                    y_density = kde(x_eval)
                    
                    result[str(cat)] = [
                        {'x': float(x), 'y': float(y)} 
                        for x, y in zip(x_eval, y_density)
                    ]
                except ImportError:
                    # Fallback: histograma
                    hist, bin_edges = np.histogram(cat_data, bins=50, density=True)
                    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                    result[str(cat)] = [
                        {'x': float(x), 'y': float(y)} 
                        for x, y in zip(bin_centers, hist)
                    ]
            
            # 🔍 DEBUG: Ver datos preparados
            print(f"🔍 [DEBUG] prepare_ridgeline_data - Categorías: {list(result.keys())}")
            for cat, points in result.items():
                print(f"  {cat}: {len(points)} puntos, muestra: {points[:2]}")
            
            return {'series': result}
            # Para listas, agrupar manualmente
            from collections import defaultdict
            grouped = defaultdict(list)
            for d in data:
                if column in d and category_col in d:
                    grouped[d[category_col]].append(d[column])
            
            result = {}
            for cat, values in grouped.items():
                if HAS_NUMPY:
                    values = np.array(values)
                else:
                    values = [v for v in values if v is not None]
                
                if len(values) == 0:
                    continue
                
                # Similar a pandas case
                try:
                    from scipy.stats import gaussian_kde
                    if bandwidth:
                        kde = gaussian_kde(values, bw_method=bandwidth)
                    else:
                        kde = gaussian_kde(values)
                    
                    if HAS_NUMPY:
                        x_min, x_max = float(np.min(values)), float(np.max(values))
                    else:
                        x_min, x_max = float(min(values)), float(max(values))
                    x_range = x_max - x_min
                    x_padding = x_range * 0.1
                    x_eval = np.linspace(x_min - x_padding, x_max + x_padding, 200)
                    y_density = kde(x_eval)
                    
                    result[str(cat)] = [
                        {'x': float(x), 'y': float(y)} 
                        for x, y in zip(x_eval, y_density)
                    ]
                except ImportError:
                    # Fallback
                    if HAS_NUMPY:
                        hist, bin_edges = np.histogram(values, bins=50, density=True)
                        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                        result[str(cat)] = [
                            {'x': float(x), 'y': float(y)} 
                            for x, y in zip(bin_centers, hist)
                        ]
        
        return {'series': result}
    
    def get_spec(self, data, column=None, category_col=None, bandwidth=None, **kwargs):
        """
        Genera la especificación del ridgeline.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            category_col: Nombre de columna de categorías
            bandwidth: Ancho de banda para KDE
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        self.validate_data(data, column=column, category_col=category_col, **kwargs)
        
        ridgeline_data = self.prepare_data(
            data,
            column=column,
            category_col=category_col,
            bandwidth=bandwidth,
            **kwargs
        )
        
        process_figsize_in_kwargs(kwargs)
        
        if 'xLabel' not in kwargs and column:
            kwargs['xLabel'] = column
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = 'Density'
        
        spec = {
            'type': self.chart_type,
        }
        spec.update(ridgeline_data)
        
        encoding = {}
        if column:
            encoding['x'] = {'field': column}
        if category_col:
            encoding['category'] = {'field': category_col}
        
        if encoding:
            spec['encoding'] = encoding
        
        options = {}
        for key in ['bandwidth', 'colorMap', 'overlap', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive', 'opacity']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if 'overlap' not in options:
            options['overlap'] = 0.5
        if 'opacity' not in options:
            options['opacity'] = 0.7
        
        if options:
            spec['options'] = options
        
        spec.update(kwargs)
        return spec

