"""
Violin Chart para BESTLIB
Combinación de boxplot y KDE para mostrar distribución de datos
"""
from .base import ChartBase
from ..core.exceptions import ChartError
from ..utils.figsize import process_figsize_in_kwargs

# Import defensivo de pandas y numpy
import sys
HAS_PANDAS = False
HAS_NUMPY = False
pd = None
np = None

try:
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


class ViolinChart(ChartBase):
    """Gráfico de violín - muestra distribución como KDE rotada + estadísticas de boxplot"""
    
    @property
    def chart_type(self):
        return 'violin'
    
    def validate_data(self, data, value_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para violin plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            value_col: Nombre de columna numérica para valores
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not value_col:
            raise ChartError("value_col es requerido para violin plot")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if value_col not in data.columns:
                raise ChartError(f"Columna '{value_col}' no encontrada en los datos")
            if not pd.api.types.is_numeric_dtype(data[value_col]):
                raise ChartError(f"Columna '{value_col}' debe ser numérica")
        else:
            if isinstance(data, list) and len(data) > 0:
                if value_col not in data[0]:
                    raise ChartError(f"Columna '{value_col}' no encontrada en los datos")
            else:
                raise ChartError("Los datos deben ser un DataFrame o lista no vacía")
    
    def prepare_data(self, data, category_col=None, value_col=None, **kwargs):
        """
        Prepara datos para violin plot calculando KDE y estadísticas.
        
        Args:
            data: DataFrame o lista de diccionarios
            category_col: Columna para categorías (opcional)
            value_col: Columna con valores numéricos
            **kwargs: Otros parámetros
        
        Returns:
            list: Lista de violines con datos de densidad y estadísticas
        """
        violin_data = []
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if category_col and category_col in data.columns:
                # Violin plot por categoría
                for category in data[category_col].unique():
                    cat_data = data[data[category_col] == category][value_col].dropna()
                    if len(cat_data) > 0:
                        violin_info = self._calculate_violin(cat_data, str(category))
                        if violin_info:
                            violin_data.append(violin_info)
            else:
                # Violin plot simple
                values = data[value_col].dropna()
                if len(values) > 0:
                    violin_info = self._calculate_violin(values, 'All')
                    if violin_info:
                        violin_data.append(violin_info)
        else:
            # Fallback para listas de diccionarios
            if category_col:
                categories = {}
                for item in data:
                    if category_col in item and value_col in item:
                        cat = str(item[category_col])
                        if cat not in categories:
                            categories[cat] = []
                        if item[value_col] is not None:
                            categories[cat].append(item[value_col])
                
                for cat, values in categories.items():
                    if HAS_NUMPY:
                        values = np.array(values)
                    if len(values) > 0:
                        violin_info = self._calculate_violin(values, cat)
                        if violin_info:
                            violin_data.append(violin_info)
            else:
                values = [item[value_col] for item in data if value_col in item and item[value_col] is not None]
                if HAS_NUMPY:
                    values = np.array(values)
                if len(values) > 0:
                    violin_info = self._calculate_violin(values, 'All')
                    if violin_info:
                        violin_data.append(violin_info)
        
        return violin_data
    
    def _calculate_violin(self, values, category):
        """
        Calcula la información del violín: KDE y estadísticas.
        
        Args:
            values: Array de valores numéricos
            category: Nombre de la categoría
        
        Returns:
            dict: Información del violín
        """
        if HAS_NUMPY and not isinstance(values, np.ndarray):
            values = np.array(values)
        
        if len(values) == 0:
            return None
        
        # Calcular estadísticas tipo boxplot
        try:
            if HAS_PANDAS and hasattr(values, 'quantile'):
                q1 = float(values.quantile(0.25))
                median = float(values.quantile(0.5))
                q3 = float(values.quantile(0.75))
                min_val = float(values.min())
                max_val = float(values.max())
            elif HAS_NUMPY:
                q1 = float(np.percentile(values, 25))
                median = float(np.percentile(values, 50))
                q3 = float(np.percentile(values, 75))
                min_val = float(np.min(values))
                max_val = float(np.max(values))
            else:
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                q1 = float(sorted_vals[int(n * 0.25)])
                median = float(sorted_vals[int(n * 0.5)])
                q3 = float(sorted_vals[int(n * 0.75)])
                min_val = float(min(values))
                max_val = float(max(values))
        except (ValueError, TypeError, OverflowError):
            return None
        
        # Calcular KDE para la forma del violín
        kde_points = []
        try:
            from scipy.stats import gaussian_kde
            
            kde = gaussian_kde(values)
            x_range = max_val - min_val
            if x_range == 0:
                x_range = 1.0
            x_eval = np.linspace(min_val - x_range * 0.1, max_val + x_range * 0.1, 100)
            density = kde(x_eval)
            
            # Normalizar densidad para que el ancho máximo sea razonable
            max_density = np.max(density)
            if max_density > 0:
                density = density / max_density
            
            for x, d in zip(x_eval, density):
                try:
                    kde_points.append({
                        'value': float(x),
                        'density': float(d)
                    })
                except (ValueError, TypeError, OverflowError):
                    pass
        except ImportError:
            # Fallback: usar histograma como aproximación
            if HAS_NUMPY:
                hist, bin_edges = np.histogram(values, bins=30, density=True)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                max_hist = np.max(hist) if np.max(hist) > 0 else 1.0
                
                for x, h in zip(bin_centers, hist):
                    try:
                        kde_points.append({
                            'value': float(x),
                            'density': float(h / max_hist)
                        })
                    except (ValueError, TypeError, OverflowError):
                        pass
        except Exception:
            # Si falla KDE, crear una aproximación simple
            pass
        
        return {
            'category': category,
            'stats': {
                'min': min_val,
                'q1': q1,
                'median': median,
                'q3': q3,
                'max': max_val
            },
            'density': kde_points
        }
    
    def get_spec(self, data, category_col=None, value_col=None, **kwargs):
        """
        Genera la especificación del violin plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            category_col: Columna para categorías (opcional)
            value_col: Columna con valores numéricos
            **kwargs: Opciones adicionales (color, axes, figsize, etc.)
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, value_col=value_col, **kwargs)
        
        # Preparar datos
        violin_data = self.prepare_data(
            data,
            category_col=category_col,
            value_col=value_col,
            **kwargs
        )
        
        # Procesar figsize si está en kwargs
        process_figsize_in_kwargs(kwargs)
        
        # Agregar etiquetas de ejes automáticamente
        if 'xLabel' not in kwargs and category_col:
            kwargs['xLabel'] = category_col
        elif 'xLabel' not in kwargs:
            kwargs['xLabel'] = 'Category'
        if 'yLabel' not in kwargs and value_col:
            kwargs['yLabel'] = value_col
        
        # Construir spec
        spec = {
            'type': self.chart_type,
            'data': violin_data,
        }
        
        # Agregar encoding
        encoding = {}
        if category_col:
            encoding['x'] = {'field': category_col}
        if value_col:
            encoding['y'] = {'field': value_col}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['color', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive', 'showBox', 'showMedian']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        # Valores por defecto
        if 'color' not in options:
            options['color'] = '#4a90e2'
        if 'showBox' not in options:
            options['showBox'] = True
        if 'showMedian' not in options:
            options['showMedian'] = True
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

