"""
Fill Between Chart para BESTLIB
Área entre dos líneas
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


class FillBetweenChart(ChartBase):
    """Gráfico de área entre dos líneas"""
    
    @property
    def chart_type(self):
        return 'fill_between'
    
    def validate_data(self, data, x_col=None, y1=None, y2=None, **kwargs):
        """
        Valida que los datos sean adecuados para fill_between.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y1: Nombre de columna para primera línea Y
            y2: Nombre de columna para segunda línea Y
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not x_col:
            raise ChartError("x_col es requerido para fill_between")
        if not y1 or not y2:
            raise ChartError("y1 e y2 son requeridos para fill_between")
        
        # Validar que las columnas existan
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if x_col not in data.columns:
                raise ChartError(f"Columna '{x_col}' no encontrada")
            if y1 not in data.columns:
                raise ChartError(f"Columna '{y1}' no encontrada")
            if y2 not in data.columns:
                raise ChartError(f"Columna '{y2}' no encontrada")
        elif isinstance(data, list) and len(data) > 0:
            if x_col not in data[0]:
                raise ChartError(f"Key '{x_col}' no encontrada")
            if y1 not in data[0]:
                raise ChartError(f"Key '{y1}' no encontrada")
            if y2 not in data[0]:
                raise ChartError(f"Key '{y2}' no encontrada")
    
    def prepare_data(self, data, x_col=None, y1=None, y2=None, **kwargs):
        """
        Prepara datos para fill_between.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y1: Nombre de columna para primera línea Y
            y2: Nombre de columna para segunda línea Y
            **kwargs: Otros parámetros
        
        Returns:
            tuple: (datos_procesados, datos_originales)
        """
        # Preparar datos base con x_col y y1
        processed_data, original_data = prepare_scatter_data(
            data,
            x_col=x_col,
            y_col=y1
        )
        
        # Agregar y2 a los datos procesados
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if y2 in data.columns:
                y2_values = data[y2].astype(float, errors='ignore')
                for idx in range(min(len(processed_data), len(y2_values))):
                    try:
                        processed_data[idx]['y2'] = float(y2_values.iloc[idx])
                        # Renombrar y a y1 para claridad
                        if 'y' in processed_data[idx]:
                            processed_data[idx]['y1'] = processed_data[idx].pop('y')
                    except (ValueError, TypeError):
                        processed_data[idx]['y2'] = processed_data[idx].get('y', 0)
        else:
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    if idx < len(processed_data):
                        if y2 in item:
                            try:
                                processed_data[idx]['y2'] = float(item.get(y2, 0))
                                if 'y' in processed_data[idx]:
                                    processed_data[idx]['y1'] = processed_data[idx].pop('y')
                            except Exception:
                                processed_data[idx]['y2'] = processed_data[idx].get('y', 0)
        
        return processed_data, original_data
    
    def get_spec(self, data, x_col=None, y1=None, y2=None, **kwargs):
        """
        Genera la especificación del fill_between.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y1: Nombre de columna para primera línea Y
            y2: Nombre de columna para segunda línea Y
            **kwargs: Opciones adicionales (color, opacity, axes, etc.)
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        # Validar datos
        self.validate_data(data, x_col=x_col, y1=y1, y2=y2, **kwargs)
        
        # Preparar datos
        processed_data, original_data = self.prepare_data(
            data,
            x_col=x_col,
            y1=y1,
            y2=y2,
            **kwargs
        )
        
        # Procesar figsize si está en kwargs
        process_figsize_in_kwargs(kwargs)
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = f"{y1} / {y2}"
        
        # Construir spec
        spec = {
            'type': self.chart_type,
            'data': processed_data,
        }
        
        # Agregar encoding
        encoding = {}
        if x_col:
            encoding['x'] = {'field': x_col}
        if y1:
            encoding['y1'] = {'field': y1}
        if y2:
            encoding['y2'] = {'field': y2}
        
        if encoding:
            spec['encoding'] = encoding
        
        # Agregar options
        options = {}
        for key in ['color', 'opacity', 'axes', 'xLabel', 'yLabel', 'figsize']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        # Valores por defecto
        if 'opacity' not in options:
            options['opacity'] = 0.3
        
        if options:
            spec['options'] = options
        
        # Agregar cualquier otro kwargs restante
        spec.update(kwargs)
        
        return spec

