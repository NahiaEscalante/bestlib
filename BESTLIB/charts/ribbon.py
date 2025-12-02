"""
Ribbon Plot Chart para BESTLIB
Área entre dos líneas con gradiente
"""
from .base import ChartBase
from ..data.preparators import prepare_line_data, _safe_to_number
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


class RibbonChart(ChartBase):
    """Gráfico ribbon (área entre líneas con gradiente)"""
    
    @property
    def chart_type(self):
        return 'ribbon'
    
    def validate_data(self, data, x_col=None, y1_col=None, y2_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para ribbon.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y1_col: Nombre de columna para línea superior
            y2_col: Nombre de columna para línea inferior
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not x_col or not y1_col or not y2_col:
            raise ChartError("x_col, y1_col e y2_col son requeridos para ribbon")
        
        try:
            validate_scatter_data(data, x_col, y1_col)
            validate_scatter_data(data, x_col, y2_col)
        except DataError as e:
            raise ChartError(f"Datos inválidos para ribbon: {e}")
    
    def prepare_data(self, data, x_col=None, y1_col=None, y2_col=None, **kwargs):
        """
        Prepara datos para ribbon.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X (soporta valores numéricos y temporales)
            y1_col: Nombre de columna para línea superior
            y2_col: Nombre de columna para línea inferior
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con x, y1, y2
        
        Note:
            Los valores de x_col que sean Timestamps, datetimes u otros tipos temporales
            serán convertidos automáticamente a timestamps numéricos.
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            # Ordenar por x_col
            data_sorted = data.sort_values(by=x_col).copy()
            ribbon_data = []
            for _, row in data_sorted.iterrows():
                ribbon_data.append({
                    'x': _safe_to_number(row[x_col]),
                    'y1': _safe_to_number(row[y1_col]),
                    'y2': _safe_to_number(row[y2_col])
                })
        else:
            # Para listas
            data_sorted = sorted(data, key=lambda d: d.get(x_col, 0))
            ribbon_data = []
            for d in data_sorted:
                ribbon_data.append({
                    'x': _safe_to_number(d[x_col]),
                    'y1': _safe_to_number(d[y1_col]),
                    'y2': _safe_to_number(d[y2_col])
                })
        
        return {'data': ribbon_data}
    
    def get_spec(self, data, x_col=None, y1_col=None, y2_col=None, **kwargs):
        """
        Genera la especificación del ribbon.
        
        Args:
            data: DataFrame o lista de diccionarios
            x_col: Nombre de columna para eje X
            y1_col: Nombre de columna para línea superior
            y2_col: Nombre de columna para línea inferior
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        self.validate_data(data, x_col=x_col, y1_col=y1_col, y2_col=y2_col, **kwargs)
        
        ribbon_data = self.prepare_data(
            data,
            x_col=x_col,
            y1_col=y1_col,
            y2_col=y2_col,
            **kwargs
        )
        
        process_figsize_in_kwargs(kwargs)
        
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = f'{y1_col} / {y2_col}'
        
        spec = {
            'type': self.chart_type,
            'data': ribbon_data['data'],
        }
        
        encoding = {}
        if x_col:
            encoding['x'] = {'field': x_col}
        if y1_col:
            encoding['y1'] = {'field': y1_col}
        if y2_col:
            encoding['y2'] = {'field': y2_col}
        
        if encoding:
            spec['encoding'] = encoding
        
        options = {}
        for key in ['color1', 'color2', 'gradient', 'opacity', 'showLines', 'strokeWidth', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if 'color1' not in options:
            options['color1'] = '#4a90e2'
        if 'color2' not in options:
            options['color2'] = '#e24a4a'
        if 'opacity' not in options:
            options['opacity'] = 0.4
        if 'showLines' not in options:
            options['showLines'] = True
        
        if options:
            spec['options'] = options
        
        spec.update(kwargs)
        return spec

