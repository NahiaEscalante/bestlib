"""
Line Plot completo para BESTLIB
Versión mejorada del line chart básico con más opciones
"""
from .base import ChartBase
from ..data.preparators import prepare_line_data
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


class LinePlotChart(ChartBase):
    """Gráfico de Líneas completo con múltiples opciones"""
    
    @property
    def chart_type(self):
        return 'line_plot'
    
    def validate_data(self, data, x_col=None, y_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para line plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not x_col or not y_col:
            raise ChartError("x_col e y_col son requeridos para line plot")
        
        try:
            validate_scatter_data(data, x_col, y_col)
        except DataError as e:
            raise ChartError(f"Datos inválidos para line plot: {e}")
    
    def prepare_data(self, data, x_col=None, y_col=None, series_col=None, **kwargs):
        """
        Prepara datos para line plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            series_col: Nombre de columna para series (opcional)
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con 'series' (prepare_line_data devuelve dict, no tuple)
        """
        # prepare_line_data devuelve {'series': {...}}, no una tupla
        line_data = prepare_line_data(
            data,
            x_col=x_col,
            y_col=y_col,
            series_col=series_col
        )
        
        # Retornar el diccionario directamente (contiene 'series')
        return line_data
    
    def get_spec(self, data, x_col=None, y_col=None, series_col=None, **kwargs):
        """
        Genera la especificación del line plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            series_col: Nombre de columna para series (opcional)
            **kwargs: Opciones adicionales (colorMap, strokeWidth, axes, etc.)
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, x_col=x_col, y_col=y_col, **kwargs)
        
        # Preparar datos (devuelve dict con 'series')
        line_data = self.prepare_data(
            data,
            x_col=x_col,
            y_col=y_col,
            series_col=series_col,
            **kwargs
        )
        
        # Procesar figsize si está en kwargs
        process_figsize_in_kwargs(kwargs)
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs and y_col:
            kwargs['yLabel'] = y_col
        
        # Extraer puntos de todas las series para 'data' (compatibilidad con validate_spec)
        all_points = []
        for series_points in line_data.get('series', {}).values():
            all_points.extend(series_points)
        
        # Construir spec
        # line_data ya contiene 'series', así que lo desempacamos directamente
        spec = {
            'type': self.chart_type,
            'data': all_points,  # Agregar 'data' para compatibilidad
        }
        spec.update(line_data)  # Agregar 'series' al spec
        
        # Agregar encoding
        encoding = {}
        if x_col:
            encoding['x'] = {'field': x_col}
        if y_col:
            encoding['y'] = {'field': y_col}
        if series_col:
            encoding['series'] = {'field': series_col}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['colorMap', 'strokeWidth', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive', 'markers']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if options:
            spec['options'] = options
        
        # Agregar interaction
        interaction = {}
        if 'interactive' in kwargs:
            interaction['interactive'] = kwargs.pop('interactive', False)
        
        if interaction:
            spec['interaction'] = interaction
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

