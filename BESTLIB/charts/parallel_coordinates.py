"""
Parallel Coordinates Chart para BESTLIB
Visualización multidimensional con coordenadas paralelas
"""
from .base import ChartBase
from ..utils.figsize import process_figsize_in_kwargs
from ..core.exceptions import ChartError, DataError

# Import de pandas de forma defensiva
import sys
HAS_PANDAS = False
pd = None

try:
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


class ParallelCoordinatesChart(ChartBase):
    """Gráfico de Coordenadas Paralelas para visualización multidimensional"""
    
    @property
    def chart_type(self):
        return 'parallel_coordinates'
    
    def validate_data(self, data, dimensions=None, **kwargs):
        """Valida datos para parallel coordinates"""
        if dimensions is None or len(dimensions) < 2:
            raise ChartError("Se requieren al menos 2 dimensiones para parallel coordinates")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            for dim in dimensions:
                if dim not in data.columns:
                    raise ChartError(f"Dimensión '{dim}' no encontrada en el DataFrame")
        elif isinstance(data, list) and len(data) > 0:
            for dim in dimensions:
                if dim not in data[0]:
                    raise ChartError(f"Dimensión '{dim}' no encontrada en los datos")
    
    def prepare_data(self, data, dimensions=None, category_col=None, **kwargs):
        """Prepara datos para parallel coordinates"""
        processed_data = []
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            for idx, row in data.iterrows():
                point = {}
                for dim in dimensions:
                    try:
                        point[dim] = float(row[dim])
                    except (ValueError, TypeError):
                        point[dim] = 0
                
                if category_col and category_col in data.columns:
                    point['_category'] = str(row[category_col])
                
                processed_data.append(point)
        else:
            for item in data:
                point = {}
                for dim in dimensions:
                    try:
                        point[dim] = float(item.get(dim, 0))
                    except (ValueError, TypeError):
                        point[dim] = 0
                
                if category_col and category_col in item:
                    point['_category'] = str(item.get(category_col, ''))
                
                processed_data.append(point)
        
        return processed_data, data
    
    def get_spec(self, data, dimensions=None, category_col=None, **kwargs):
        """
        Genera especificación de parallel coordinates.
        
        Args:
            data: DataFrame o lista de diccionarios
            dimensions: Lista de nombres de columnas para las dimensiones
            category_col: Columna para categorizar/colorear las líneas
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec para BESTLIB
        """
        self.validate_data(data, dimensions=dimensions, **kwargs)
        
        processed_data, original_data = self.prepare_data(
            data,
            dimensions=dimensions,
            category_col=category_col,
            **kwargs
        )
        
        process_figsize_in_kwargs(kwargs)
        
        spec = {
            'type': self.chart_type,
            'data': processed_data,
            'dimensions': dimensions,
        }
        
        if category_col:
            spec['categoryCol'] = category_col
        
        # Agregar options
        options = {}
        for key in ['axes', 'figsize', 'interactive', 'colorScale']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if options:
            spec['options'] = options
        
        spec.update(kwargs)
        
        return spec

