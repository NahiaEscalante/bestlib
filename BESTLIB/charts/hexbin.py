"""
Hexbin Chart para BESTLIB
Visualización de densidad usando hexágonos
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


class HexbinChart(ChartBase):
    """Gráfico Hexbin para visualización de densidad"""
    
    @property
    def chart_type(self):
        return 'hexbin'
    
    def validate_data(self, data, x_col=None, y_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para hexbin.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not x_col or not y_col:
            raise ChartError("x_col e y_col son requeridos para hexbin")
        
        try:
            validate_scatter_data(data, x_col, y_col)
        except DataError as e:
            raise ChartError(f"Datos inválidos para hexbin: {e}")
    
    def prepare_data(self, data, x_col=None, y_col=None, **kwargs):
        """
        Prepara datos para hexbin.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Otros parámetros
        
        Returns:
            tuple: (datos_procesados, datos_originales)
        """
        processed_data, original_data = prepare_scatter_data(
            data,
            x_col=x_col,
            y_col=y_col
        )
        
        return processed_data, original_data
    
    def get_spec(self, data, x_col=None, y_col=None, **kwargs):
        """
        Genera la especificación del hexbin.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Opciones adicionales (bins, colorScale, axes, etc.)
        
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
            **kwargs
        )
        
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
            'data': processed_data,
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
        for key in ['bins', 'colorScale', 'axes', 'xLabel', 'yLabel', 'figsize']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        # Valor por defecto para bins si no se especifica
        if 'bins' not in options:
            options['bins'] = 20
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

