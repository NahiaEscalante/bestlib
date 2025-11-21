"""
Errorbars Chart para BESTLIB
Gráfico con barras de error
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


class ErrorbarsChart(ChartBase):
    """Gráfico con barras de error"""
    
    @property
    def chart_type(self):
        return 'errorbars'
    
    def validate_data(self, data, x_col=None, y_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para errorbars.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            **kwargs: Otros parámetros (yerr, xerr)
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not x_col or not y_col:
            raise ChartError("x_col e y_col son requeridos para errorbars")
        
        try:
            validate_scatter_data(data, x_col, y_col)
        except DataError as e:
            raise ChartError(f"Datos inválidos para errorbars: {e}")
        
        # Validar que exista columna de error si se especifica
        yerr = kwargs.get('yerr')
        xerr = kwargs.get('xerr')
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if yerr and yerr not in data.columns:
                raise ChartError(f"Columna '{yerr}' no encontrada para yerr")
            if xerr and xerr not in data.columns:
                raise ChartError(f"Columna '{xerr}' no encontrada para xerr")
        elif isinstance(data, list) and len(data) > 0:
            if yerr and yerr not in data[0]:
                raise ChartError(f"Key '{yerr}' no encontrada para yerr")
            if xerr and xerr not in data[0]:
                raise ChartError(f"Key '{xerr}' no encontrada para xerr")
    
    def prepare_data(self, data, x_col=None, y_col=None, yerr=None, xerr=None, **kwargs):
        """
        Prepara datos para errorbars.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            yerr: Nombre de columna para error en Y (opcional)
            xerr: Nombre de columna para error en X (opcional)
            **kwargs: Otros parámetros
        
        Returns:
            tuple: (datos_procesados, datos_originales)
        """
        processed_data, original_data = prepare_scatter_data(
            data,
            x_col=x_col,
            y_col=y_col
        )
        
        # Agregar valores de error a los datos procesados
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if yerr and yerr in data.columns:
                yerr_values = data[yerr].astype(float, errors='ignore')
                for idx in range(min(len(processed_data), len(yerr_values))):
                    try:
                        processed_data[idx]['yerr'] = float(yerr_values.iloc[idx])
                    except (ValueError, TypeError):
                        processed_data[idx]['yerr'] = 0
            if xerr and xerr in data.columns:
                xerr_values = data[xerr].astype(float, errors='ignore')
                for idx in range(min(len(processed_data), len(xerr_values))):
                    try:
                        processed_data[idx]['xerr'] = float(xerr_values.iloc[idx])
                    except (ValueError, TypeError):
                        processed_data[idx]['xerr'] = 0
        else:
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    if idx < len(processed_data):
                        if yerr and yerr in item:
                            try:
                                processed_data[idx]['yerr'] = float(item.get(yerr, 0))
                            except Exception:
                                processed_data[idx]['yerr'] = 0
                        if xerr and xerr in item:
                            try:
                                processed_data[idx]['xerr'] = float(item.get(xerr, 0))
                            except Exception:
                                processed_data[idx]['xerr'] = 0
        
        return processed_data, original_data
    
    def get_spec(self, data, x_col=None, y_col=None, yerr=None, xerr=None, **kwargs):
        """
        Genera la especificación del errorbars.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            yerr: Nombre de columna para error en Y (opcional)
            xerr: Nombre de columna para error en X (opcional)
            **kwargs: Opciones adicionales (color, strokeWidth, axes, etc.)
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, x_col=x_col, y_col=y_col, yerr=yerr, xerr=xerr, **kwargs)
        
        # Preparar datos
        processed_data, original_data = self.prepare_data(
            data,
            x_col=x_col,
            y_col=y_col,
            yerr=yerr,
            xerr=xerr,
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
        if yerr:
            encoding['yerr'] = {'field': yerr}
        if xerr:
            encoding['xerr'] = {'field': xerr}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['color', 'strokeWidth', 'capSize', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

