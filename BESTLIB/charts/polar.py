"""
Polar Plot Chart para BESTLIB
Gráfico en coordenadas polares
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


class PolarChart(ChartBase):
    """Gráfico polar (coordenadas polares)"""
    
    @property
    def chart_type(self):
        return 'polar'
    
    def validate_data(self, data, angle_col=None, radius_col=None, **kwargs):
        """
        Valida que los datos sean adecuados para polar plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            angle_col: Nombre de columna para ángulo (en radianes o grados)
            radius_col: Nombre de columna para radio
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        if not angle_col or not radius_col:
            raise ChartError("angle_col y radius_col son requeridos para polar plot")
        
        try:
            validate_scatter_data(data, angle_col, radius_col)
        except DataError as e:
            raise ChartError(f"Datos inválidos para polar plot: {e}")
    
    def prepare_data(self, data, angle_col=None, radius_col=None, angle_unit='rad', **kwargs):
        """
        Prepara datos para polar plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            angle_col: Nombre de columna para ángulo
            radius_col: Nombre de columna para radio
            angle_unit: Unidad del ángulo ('rad' o 'deg')
            **kwargs: Otros parámetros
        
        Returns:
            dict: Datos preparados con x, y (coordenadas cartesianas)
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            angles = data[angle_col].values
            radii = data[radius_col].values
        else:
            angles = [d[angle_col] for d in data if angle_col in d and angle_col in d]
            radii = [d[radius_col] for d in data if radius_col in d and radius_col in d]
            if HAS_NUMPY:
                angles = np.array(angles)
                radii = np.array(radii)
        
        # Convertir ángulos a radianes si es necesario
        if angle_unit == 'deg':
            if HAS_NUMPY:
                angles = np.deg2rad(angles)
            else:
                angles = [np.pi * a / 180.0 for a in angles]
        
        # Convertir a coordenadas cartesianas
        if HAS_NUMPY:
            x_coords = radii * np.cos(angles)
            y_coords = radii * np.sin(angles)
        else:
            import math
            x_coords = [r * math.cos(a) for r, a in zip(radii, angles)]
            y_coords = [r * math.sin(a) for r, a in zip(radii, angles)]
        
        polar_data = []
        for x, y, angle, radius in zip(x_coords, y_coords, angles, radii):
            polar_data.append({
                'x': float(x),
                'y': float(y),
                'angle': float(angle),
                'radius': float(radius)
            })
        
        return {'data': polar_data}
    
    def get_spec(self, data, angle_col=None, radius_col=None, angle_unit='rad', **kwargs):
        """
        Genera la especificación del polar plot.
        
        Args:
            data: DataFrame o lista de diccionarios
            angle_col: Nombre de columna para ángulo
            radius_col: Nombre de columna para radio
            angle_unit: Unidad del ángulo ('rad' o 'deg')
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        """
        self.validate_data(data, angle_col=angle_col, radius_col=radius_col, **kwargs)
        
        polar_data = self.prepare_data(
            data,
            angle_col=angle_col,
            radius_col=radius_col,
            angle_unit=angle_unit,
            **kwargs
        )
        
        process_figsize_in_kwargs(kwargs)
        
        spec = {
            'type': self.chart_type,
            'data': polar_data['data'],
        }
        
        encoding = {}
        if angle_col:
            encoding['angle'] = {'field': angle_col}
        if radius_col:
            encoding['radius'] = {'field': radius_col}
        
        if encoding:
            spec['encoding'] = encoding
        
        options = {}
        for key in ['angle_unit', 'showGrid', 'showLabels', 'color', 'strokeWidth', 'axes', 'figsize', 'interactive']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if 'angle_unit' not in options:
            options['angle_unit'] = angle_unit
        if 'showGrid' not in options:
            options['showGrid'] = True
        if 'color' not in options:
            options['color'] = '#4a90e2'
        
        if options:
            spec['options'] = options
        
        spec.update(kwargs)
        return spec

