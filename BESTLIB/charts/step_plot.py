"""
Step Plot Chart para BESTLIB
Gráfico de líneas escalonadas
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


class StepPlotChart(ChartBase):
    """Gráfico de líneas escalonadas (step plot)"""
    
    @property
    def chart_type(self):
        return 'step_plot'
    
    def validate_data(self, data, x_col=None, y_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para step plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not x_col or not y_col:
            raise ChartError("x_col e y_col son requeridos para step plot")
        
        try:
            validate_scatter_data(data, x_col, y_col)
        except DataError as e:
            raise ChartError(f"Datos inválidos para step plot: {e}")
    
    def prepare_data(self, data, x_col=None, y_col=None, **kwargs):
        """
        Prepara datos para step plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Otros parámetros
        
        Returns:
            dict: Diccionario con 'series' (prepare_line_data devuelve dict, no tupla)
        """
        # Ordenar por x_col para step plot
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            data_sorted = data.sort_values(by=x_col).copy()
        else:
            # Para listas, ordenar manualmente
            data_sorted = sorted(data, key=lambda d: d.get(x_col, 0))
        
        # prepare_line_data devuelve {'series': {...}}, no una tupla
        line_data = prepare_line_data(
            data_sorted,
            x_col=x_col,
            y_col=y_col
        )
        
        return line_data
    
    def get_spec(self, data, x_col=None, y_col=None, **kwargs):
        """
        Genera la especificación del step plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Opciones adicionales (stepType, color, strokeWidth, axes, etc.)
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, x_col=x_col, y_col=y_col, **kwargs)
        
        # Preparar datos (devuelve dict con 'series')
        prepared_data = self.prepare_data(
            data,
            x_col=x_col,
            y_col=y_col,
            **kwargs
        )
        
        # Extraer puntos de todas las series para 'data'
        all_points = []
        for series_points in prepared_data.get('series', {}).values():
            all_points.extend(series_points)
        
        # Procesar figsize si está en kwargs
        process_figsize_in_kwargs(kwargs)
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs and y_col:
            kwargs['yLabel'] = y_col
        
        # Construir spec
        spec = {
            'type': self.chart_type,
            'data': all_points,
            'series': prepared_data.get('series', {}),
        }
        
        # Agregar encoding
        encoding = {}
        if x_col:
            encoding['x'] = {'field': x_col}
        if y_col:
            encoding['y'] = {'field': y_col}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['stepType', 'color', 'strokeWidth', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        # Valor por defecto para stepType si no se especifica
        if 'stepType' not in options:
            options['stepType'] = 'step'  # 'step', 'stepBefore', 'stepAfter'
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

