"""
KDE (Kernel Density Estimation) Chart para BESTLIB
Estimación de densidad de kernel
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
    
    def prepare_data(self, data, column=None, bandwidth=None, **kwargs):
        """
        Prepara datos para KDE calculando la densidad.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            bandwidth: Ancho de banda para KDE (opcional)
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con 'x' y 'y' (densidad)
        """
        print(f"[DEBUG KDE prepare_data] Iniciando con column={column}")
        
        # Debug: verificar datos de entrada
        if not HAS_PANDAS or not HAS_NUMPY:
            raise ChartError("KDE requiere pandas y numpy instalados")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if column not in data.columns:
                raise ChartError(f"Columna '{column}' no encontrada. Columnas disponibles: {list(data.columns)}")
            values = data[column].dropna().values
            print(f"[DEBUG KDE] Valores extraídos: {len(values)} puntos")
        else:
            # Si data es lista de dicts
            if isinstance(data, list) and len(data) > 0:
                values = [d[column] for d in data if column in d and d[column] is not None]
                if HAS_NUMPY:
                    values = np.array(values)
                print(f"[DEBUG KDE] Valores desde lista: {len(values)} puntos")
            else:
                raise ChartError(f"Datos inválidos para KDE: tipo={type(data)}")
        
        if len(values) == 0:
            raise ChartError(f"No hay datos válidos para calcular KDE en columna '{column}'")
        
        # Calcular KDE usando scipy si está disponible, sino usar numpy
        print(f"[DEBUG KDE] Intentando calcular KDE con scipy...")
        try:
            from scipy.stats import gaussian_kde
            if bandwidth:
                kde = gaussian_kde(values, bw_method=bandwidth)
            else:
                kde = gaussian_kde(values)
            
            print(f"[DEBUG KDE] KDE creado exitosamente con scipy")
            
            # Crear rango de valores para evaluar
            x_min, x_max = float(np.min(values)), float(np.max(values))
            x_range = x_max - x_min
            x_padding = x_range * 0.1  # 10% padding
            x_eval = np.linspace(x_min - x_padding, x_max + x_padding, 200)
            y_density = kde(x_eval)
            
            print(f"[DEBUG KDE] Densidad calculada: {len(x_eval)} puntos, rango x=[{x_min:.2f}, {x_max:.2f}]")
            
            # Convertir a lista de puntos
            kde_data = [
                {'x': float(x), 'y': float(y)} 
                for x, y in zip(x_eval, y_density)
            ]
            print(f"[DEBUG KDE] Lista de puntos creada: {len(kde_data)} elementos")
        except ImportError as e:
            print(f"[DEBUG KDE] Scipy no disponible: {e}, usando fallback numpy")
            # Fallback: usar histograma normalizado como aproximación
            if HAS_NUMPY:
                hist, bin_edges = np.histogram(values, bins=50, density=True)
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                kde_data = [
                    {'x': float(x), 'y': float(y)} 
                    for x, y in zip(bin_centers, hist)
                ]
                print(f"[DEBUG KDE] Fallback completado: {len(kde_data)} elementos")
            else:
                raise ChartError("Se requiere scipy o numpy para calcular KDE")
        
        print(f"[DEBUG KDE] prepare_data retornando {len(kde_data)} puntos")
        return {'data': kde_data}
    
    def get_spec(self, data, column=None, bandwidth=None, **kwargs):
        """
        Genera la especificación del KDE.
        
        Args:
            data: DataFrame o lista de diccionarios
            column: Nombre de columna numérica
            bandwidth: Ancho de banda para KDE (opcional)
            **kwargs: Opciones adicionales (color, strokeWidth, axes, etc.)
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, column=column, **kwargs)
        
        # Preparar datos
        kde_data = self.prepare_data(
            data,
            column=column,
            bandwidth=bandwidth,
            **kwargs
        )
        
        # DEBUG: Verificar datos preparados
        print(f"[DEBUG KDE] Datos preparados: {len(kde_data['data'])} puntos")
        if len(kde_data['data']) > 0:
            print(f"[DEBUG KDE] Primer punto: {kde_data['data'][0]}")
            print(f"[DEBUG KDE] Último punto: {kde_data['data'][-1]}")
        
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
            'data': kde_data['data'],
        }
        
        # DEBUG: Verificar spec
        print(f"[DEBUG KDE] Spec type: {spec['type']}")
        print(f"[DEBUG KDE] Spec data length: {len(spec.get('data', []))}")
        
        # Agregar encoding - los datos tienen campos 'x' e 'y'
        encoding = {
            'x': {'field': 'x'},
            'y': {'field': 'y'}
        }
        spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['color', 'strokeWidth', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive', 'fill', 'opacity']:
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
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

