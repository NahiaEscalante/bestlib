"""
Distribution Plot Chart para BESTLIB
Combinación de histograma y KDE
"""
from .base import ChartBase
from ..data.validators import validate_scatter_data
from ..utils.figsize import process_figsize_in_kwargs
from ..core.exceptions import ChartError, DataError

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


class DistplotChart(ChartBase):
    """Gráfico de distribución (histograma + KDE)"""
    
    @property
    def chart_type(self):
        return 'distplot'
    
    def validate_data(self, data, column=None, **kwargs):
        """
        Valida que los datos sean adecuados para distplot.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not column:
            raise ChartError("column es requerido para distplot")
        
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
    
    def prepare_data(self, data, column=None, bins=30, kde=True, rug=False, **kwargs):
        """
        Prepara datos para distplot (histograma + KDE opcional).
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            bins: Número de bins para histograma
            kde: Si True, incluir KDE
            rug: Si True, incluir rug plot
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con histograma y opcionalmente KDE
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            values = data[column].dropna().values
        else:
            values = [d[column] for d in data if column in d and d[column] is not None]
            if HAS_NUMPY:
                values = np.array(values)
        
        if len(values) == 0:
            raise ChartError("No hay datos válidos para distplot")
        
        result = {}
        
        # Histograma
        if HAS_NUMPY:
            hist, bin_edges = np.histogram(values, bins=bins, density=True)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            histogram_data = [
                {'x': float(x), 'y': float(y), 'bin_start': float(be[0]), 'bin_end': float(be[1])}
                for x, y, be in zip(bin_centers, hist, zip(bin_edges[:-1], bin_edges[1:]))
            ]
        else:
            # Fallback sin numpy
            min_val, max_val = min(values), max(values)
            bin_width = (max_val - min_val) / bins
            histogram_data = []
            for i in range(bins):
                bin_start = min_val + i * bin_width
                bin_end = bin_start + bin_width
                count = sum(1 for v in values if bin_start <= v < bin_end)
                density = count / (len(values) * bin_width) if len(values) > 0 else 0
                histogram_data.append({
                    'x': float((bin_start + bin_end) / 2),
                    'y': float(density),
                    'bin_start': float(bin_start),
                    'bin_end': float(bin_end)
                })
        
        result['histogram'] = histogram_data
        
        # KDE opcional
        if kde:
            try:
                from scipy.stats import gaussian_kde
                kde_obj = gaussian_kde(values)
                x_min, x_max = float(np.min(values)), float(np.max(values))
                x_range = x_max - x_min
                x_padding = x_range * 0.1
                x_eval = np.linspace(x_min - x_padding, x_max + x_padding, 200)
                y_density = kde_obj(x_eval)
                
                kde_data = [
                    {'x': float(x), 'y': float(y)} 
                    for x, y in zip(x_eval, y_density)
                ]
                result['kde'] = kde_data
            except ImportError:
                # Si no hay scipy, no incluir KDE
                pass
        
        # Rug opcional
        if rug:
            rug_data = [
                {'x': float(val), 'y': 0}
                for val in values
            ]
            result['rug'] = rug_data
        
        return result
    
    def get_spec(self, data, column=None, bins=30, kde=True, rug=False, **kwargs):
        """
        Genera la especificación del distplot.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            bins: Número de bins para histograma
            kde: Si True, incluir KDE
            rug: Si True, incluir rug plot
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, column=column, **kwargs)
        
        # Preparar datos
        dist_data = self.prepare_data(
            data,
            column=column,
            bins=bins,
            kde=kde,
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
            'data': dist_data,
        }
        
        # Agregar encoding
        encoding = {}
        if column:
            encoding['x'] = {'field': column}
        encoding['y'] = {'field': 'density'}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['bins', 'kde', 'rug', 'color', 'kdeColor', 'rugColor', 'strokeWidth', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive', 'opacity']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        # Valores por defecto
        if 'bins' not in options:
            options['bins'] = bins
        if 'kde' not in options:
            options['kde'] = kde
        if 'rug' not in options:
            options['rug'] = rug
        if 'color' not in options:
            options['color'] = '#4a90e2'
        if 'kdeColor' not in options:
            options['kdeColor'] = '#e24a4a'
        if 'rugColor' not in options:
            options['rugColor'] = '#4a90e2'
        if 'opacity' not in options:
            options['opacity'] = 0.6
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

