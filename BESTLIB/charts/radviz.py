"""
Radviz Chart para BESTLIB
Visualización radial de datos multidimensionales
"""
from .base import ChartBase
from ..utils.figsize import process_figsize_in_kwargs
from ..core.exceptions import ChartError, DataError
import math

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


class RadvizChart(ChartBase):
    """Gráfico Radviz para visualización radial multidimensional"""
    
    @property
    def chart_type(self):
        return 'radviz'
    
    def validate_data(self, data, features=None, **kwargs):
        """Valida datos para radviz"""
        if features is None or len(features) < 2:
            raise ChartError("Se requieren al menos 2 features para radviz")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            for feat in features:
                if feat not in data.columns:
                    raise ChartError(f"Feature '{feat}' no encontrada en el DataFrame")
        elif isinstance(data, list) and len(data) > 0:
            for feat in features:
                if feat not in data[0]:
                    raise ChartError(f"Feature '{feat}' no encontrada en los datos")
    
    def prepare_data(self, data, features=None, class_col=None, **kwargs):
        """
        Prepara datos para radviz normalizando features y calculando posiciones.
        
        Args:
            data: DataFrame o lista de diccionarios
            features: Lista de nombres de features a usar
            class_col: Columna de clase/categoría para colorear
        
        Returns:
            tuple: (datos_procesados, datos_originales)
        """
        # Normalizar features (min-max scaling)
        feature_mins = {}
        feature_maxs = {}
        
        # Calcular min/max para cada feature
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            for feat in features:
                try:
                    feature_mins[feat] = float(data[feat].min())
                    feature_maxs[feat] = float(data[feat].max())
                except:
                    feature_mins[feat] = 0
                    feature_maxs[feat] = 1
        else:
            for feat in features:
                values = [item.get(feat, 0) for item in data]
                try:
                    feature_mins[feat] = min(values)
                    feature_maxs[feat] = max(values)
                except:
                    feature_mins[feat] = 0
                    feature_maxs[feat] = 1
        
        # Calcular posiciones de anclaje de features (círculo unitario)
        n_features = len(features)
        anchors = {}
        for i, feat in enumerate(features):
            angle = (2 * math.pi * i) / n_features
            anchors[feat] = {
                'x': math.cos(angle),
                'y': math.sin(angle),
                'angle': angle
            }
        
        processed_data = []
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            for idx, row in data.iterrows():
                # Normalizar valores
                weights = []
                sum_weights = 0
                
                for feat in features:
                    try:
                        val = float(row[feat])
                        min_val = feature_mins[feat]
                        max_val = feature_maxs[feat]
                        
                        if max_val - min_val > 0:
                            normalized = (val - min_val) / (max_val - min_val)
                        else:
                            normalized = 0.5
                        
                        weights.append(normalized)
                        sum_weights += normalized
                    except:
                        weights.append(0)
                
                # Calcular posición ponderada
                if sum_weights > 0:
                    x = sum(w * anchors[feat]['x'] for w, feat in zip(weights, features)) / sum_weights
                    y = sum(w * anchors[feat]['y'] for w, feat in zip(weights, features)) / sum_weights
                else:
                    x, y = 0, 0
                
                point = {
                    'x': x,
                    'y': y,
                    '_weights': weights
                }
                
                if class_col and class_col in data.columns:
                    point['_class'] = str(row[class_col])
                
                processed_data.append(point)
        else:
            for item in data:
                weights = []
                sum_weights = 0
                
                for feat in features:
                    try:
                        val = float(item.get(feat, 0))
                        min_val = feature_mins[feat]
                        max_val = feature_maxs[feat]
                        
                        if max_val - min_val > 0:
                            normalized = (val - min_val) / (max_val - min_val)
                        else:
                            normalized = 0.5
                        
                        weights.append(normalized)
                        sum_weights += normalized
                    except:
                        weights.append(0)
                
                if sum_weights > 0:
                    x = sum(w * anchors[feat]['x'] for w, feat in zip(weights, features)) / sum_weights
                    y = sum(w * anchors[feat]['y'] for w, feat in zip(weights, features)) / sum_weights
                else:
                    x, y = 0, 0
                
                point = {
                    'x': x,
                    'y': y,
                    '_weights': weights
                }
                
                if class_col and class_col in item:
                    point['_class'] = str(item.get(class_col, ''))
                
                processed_data.append(point)
        
        return processed_data, data
    
    def get_spec(self, data, features=None, class_col=None, **kwargs):
        """
        Genera especificación de radviz.
        
        Args:
            data: DataFrame o lista de diccionarios
            features: Lista de nombres de features para las dimensiones radiales
            class_col: Columna para clasificar/colorear los puntos
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec para BESTLIB
        """
        self.validate_data(data, features=features, **kwargs)
        
        processed_data, original_data = self.prepare_data(
            data,
            features=features,
            class_col=class_col,
            **kwargs
        )
        
        process_figsize_in_kwargs(kwargs)
        
        spec = {
            'type': self.chart_type,
            'data': processed_data,
            'features': features,
        }
        
        if class_col:
            spec['classCol'] = class_col
        
        # Agregar options
        options = {}
        for key in ['figsize', 'interactive', 'colorScale']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if options:
            spec['options'] = options
        
        spec.update(kwargs)
        
        return spec

