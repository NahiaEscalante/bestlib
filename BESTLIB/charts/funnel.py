"""
Funnel Plot Chart para BESTLIB
Gráfico de embudo (funnel plot)
"""
from .base import ChartBase
from ..data.validators import validate_scatter_data
from ..utils.figsize import process_figsize_in_kwargs
from ..core.exceptions import ChartError, DataError

# Import de pandas y numpy de forma defensiva para evitar errores de importación circular
import sys  # sys siempre está disponible, importarlo fuera del try
HAS_PANDAS = False
HAS_NUMPY = False
pd = None
np = None

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

try:
    import numpy as np
    HAS_NUMPY = True
except (ImportError, AttributeError, ModuleNotFoundError, Exception):
    HAS_NUMPY = False
    np = None


class FunnelChart(ChartBase):
    """Gráfico funnel (embudo)"""
    
    @property
    def chart_type(self):
        return 'funnel'
    
    def validate_data(self, data, stage_col=None, value_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para funnel plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            stage_col: Nombre de columna para etapas
            value_col: Nombre de columna para valores
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not stage_col or not value_col:
            raise ChartError("stage_col y value_col son requeridos para funnel plot")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if stage_col not in data.columns:
                raise ChartError(f"Columna '{stage_col}' no encontrada")
            if value_col not in data.columns:
                raise ChartError(f"Columna '{value_col}' no encontrada")
            if not pd.api.types.is_numeric_dtype(data[value_col]):
                raise ChartError(f"Columna '{value_col}' debe ser numérica")
        else:
            if isinstance(data, list) and len(data) > 0:
                if stage_col not in data[0] or value_col not in data[0]:
                    raise ChartError(f"Columnas requeridas no encontradas")
            else:
                raise ChartError("Los datos deben ser un DataFrame o lista no vacía")
    
    def prepare_data(self, data, stage_col=None, value_col=None, **kwargs):
        """
        Prepara datos para funnel plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            stage_col: Nombre de columna para etapas
            value_col: Nombre de columna para valores
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con etapas y valores
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            # Ordenar por valor descendente (típico en funnel)
            data_sorted = data.sort_values(by=value_col, ascending=False).copy()
            funnel_data = []
            for idx, row in data_sorted.iterrows():
                funnel_data.append({
                    'stage': str(row[stage_col]),
                    'value': float(row[value_col]),
                    'index': idx
                })
        else:
            # Para listas
            data_sorted = sorted(data, key=lambda d: d.get(value_col, 0), reverse=True)
            funnel_data = []
            for idx, d in enumerate(data_sorted):
                funnel_data.append({
                    'stage': str(d[stage_col]),
                    'value': float(d[value_col]),
                    'index': idx
                })
        
        return {'data': funnel_data}
    
    def get_spec(self, data, stage_col=None, value_col=None, **kwargs):
        """
        Genera la especificación del funnel plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            stage_col: Nombre de columna para etapas
            value_col: Nombre de columna para valores
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        self.validate_data(data, stage_col=stage_col, value_col=value_col, **kwargs)
        
        funnel_data = self.prepare_data(
            data,
            stage_col=stage_col,
            value_col=value_col,
            **kwargs
        )
        
        process_figsize_in_kwargs(kwargs)
        
        if 'xLabel' not in kwargs:
            kwargs['xLabel'] = 'Stage'
        if 'yLabel' not in kwargs and value_col:
            kwargs['yLabel'] = value_col
        
        spec = {
            'type': self.chart_type,
            'data': funnel_data['data'],
        }
        
        encoding = {}
        if stage_col:
            encoding['stage'] = {'field': stage_col}
        if value_col:
            encoding['value'] = {'field': value_col}
        
        if encoding:
            spec['encoding'] = encoding
        
        options = {}
        for key in ['color', 'opacity', 'orientation', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if 'color' not in options:
            options['color'] = '#4a90e2'
        if 'opacity' not in options:
            options['opacity'] = 0.7
        if 'orientation' not in options:
            options['orientation'] = 'vertical'  # 'vertical' o 'horizontal'
        
        if options:
            spec['options'] = options
        
        spec.update(kwargs)
        return spec

