"""
Scatter Plot Chart para BESTLIB
"""
from .base import ChartBase
from ..data.preparators import prepare_scatter_data
from ..data.validators import validate_scatter_data
from ..utils.figsize import process_figsize_in_kwargs
from ..core.exceptions import ChartError, DataError

# Import de pandas de forma defensiva para evitar errores de importación circular
import sys  # sys siempre está disponible, importarlo fuera del try
HAS_PANDAS = False
pd = None
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


class ScatterChart(ChartBase):
    """Gráfico de Scatter Plot"""
    
    @property
    def chart_type(self):
        return 'scatter'
    
    def validate_data(self, data, x_col=None, y_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para scatter plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not x_col or not y_col:
            raise ChartError("x_col e y_col son requeridos para scatter plot")
        
        try:
            validate_scatter_data(data, x_col, y_col)
        except DataError as e:
            raise ChartError(f"Datos inválidos para scatter plot: {e}")
    
    def prepare_data(self, data, x_col=None, y_col=None, category_col=None, 
                     size_col=None, color_col=None, **kwargs):
        """
        Prepara datos para scatter plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            category_col: Nombre de columna para categorías (opcional)
            size_col: Nombre de columna para tamaño (opcional)
            color_col: Nombre de columna para color (opcional)
            **kwargs: Otros parámetros
        
        Returns:
            tuple: (datos_procesados, datos_originales)
        """
        processed_data, original_data = prepare_scatter_data(
            data, 
            x_col=x_col, 
            y_col=y_col, 
            category_col=category_col,
            size_col=size_col,
            color_col=color_col
        )
        
        # Enriquecer con tamaño y color si se especificaron
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if size_col and size_col in data.columns:
                size_values = data[size_col].astype(float, errors='ignore')
                for idx in range(min(len(processed_data), len(size_values))):
                    try:
                        processed_data[idx]['size'] = float(size_values.iloc[idx])
                    except (ValueError, TypeError):
                        pass
            if color_col and color_col in data.columns:
                color_values = data[color_col]
                for idx in range(min(len(processed_data), len(color_values))):
                    processed_data[idx]['color'] = color_values.iloc[idx]
        else:
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    if idx < len(processed_data):
                        if size_col and size_col in item:
                            try:
                                processed_data[idx]['size'] = float(item.get(size_col))
                            except Exception:
                                pass
                        if color_col and color_col in item:
                            processed_data[idx]['color'] = item.get(color_col)
        
        # Aplicar sampling si se especifica maxPoints
        max_points = kwargs.get('maxPoints', None)
        if max_points and isinstance(max_points, int) and max_points > 0 and len(processed_data) > max_points:
            if HAS_PANDAS and isinstance(data, pd.DataFrame):
                step = len(data) / max_points
                sample_indices = [int(i * step) for i in range(max_points)]
                processed_data = [processed_data[i] for i in sample_indices if i < len(processed_data)]
            else:
                step = len(processed_data) / max_points
                processed_data = [processed_data[int(i * step)] for i in range(max_points) if int(i * step) < len(processed_data)]
        
        return processed_data, original_data
    
    def get_spec(self, data, x_col=None, y_col=None, category_col=None,
                 size_col=None, color_col=None, **kwargs):
        """
        Genera la especificación del scatter plot (BESTLIB Visualization Spec).
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            category_col: Nombre de columna para categorías (opcional)
            size_col: Nombre de columna para tamaño (opcional)
            color_col: Nombre de columna para color (opcional)
            **kwargs: Opciones adicionales (colorMap, pointRadius, interactive, axes, etc.)
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, x_col=x_col, y_col=y_col, **kwargs)
        
        # Preparar datos
        processed_data, original_data = self.prepare_data(
            data,
            x_col=x_col,
            y_col=y_col,
            category_col=category_col,
            size_col=size_col,
            color_col=color_col,
            **kwargs
        )
        
        # Procesar figsize si está en kwargs
        process_figsize_in_kwargs(kwargs)
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs and y_col:
            kwargs['yLabel'] = y_col
        
        # Construir spec conforme a BESTLIB Visualization Spec
        spec = {
            'type': self.chart_type,
            'data': processed_data,
        }
        
        # Agregar encoding si hay columnas específicas
        encoding = {}
        if x_col:
            encoding['x'] = {'field': x_col}
        if y_col:
            encoding['y'] = {'field': y_col}
        if category_col:
            encoding['color'] = {'field': category_col}
        if size_col:
            encoding['size'] = {'field': size_col}
        if color_col:
            encoding['color'] = {'field': color_col}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        if 'pointRadius' in kwargs:
            options['pointRadius'] = kwargs.pop('pointRadius')
        if 'colorMap' in kwargs:
            options['colorMap'] = kwargs.pop('colorMap')
        if 'axes' in kwargs:
            options['axes'] = kwargs.pop('axes', True)
        if 'xLabel' in kwargs:
            options['xLabel'] = kwargs.pop('xLabel')
        if 'yLabel' in kwargs:
            options['yLabel'] = kwargs.pop('yLabel')
        if 'figsize' in kwargs:
            options['figsize'] = kwargs.pop('figsize')
        
        if options:
            spec['options'] = options
        
        # ✅ CORRECCIÓN CRÍTICA: Asegurar que interactive esté en el spec directamente
        # El JavaScript busca spec.interactive, no spec.interaction.interactive
        if 'interactive' in kwargs:
            spec['interactive'] = kwargs.pop('interactive', False)
        elif 'interaction' in kwargs and isinstance(kwargs.get('interaction'), dict):
            # Si viene en interaction dict, extraerlo
            interaction = kwargs.pop('interaction', {})
            spec['interactive'] = interaction.get('interactive', False)
        else:
            # Por defecto, scatter plots son interactivos
            spec['interactive'] = kwargs.pop('interactive', True)
        
        # Agregar interaction (para compatibilidad)
        interaction = {}
        if 'zoom' in kwargs:
            interaction['zoom'] = kwargs.pop('zoom', False)
        if 'brush' in kwargs:
            interaction['brush'] = kwargs.pop('brush', False)
        
        if interaction:
            spec['interaction'] = interaction
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

