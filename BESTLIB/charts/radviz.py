"""Radviz Chart"""
from .base import ChartBase
from ..core.exceptions import ChartError, DataError
import math

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


class RadvizChart(ChartBase):
    @property
    def chart_type(self):
        return 'radviz'
    
    def validate_data(self, data, features=None, **kwargs):
        if not features:
            raise ChartError("features es requerido para radviz")
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            missing = [f for f in features if f not in data.columns]
            if missing:
                raise DataError(f"Faltan columnas para radviz: {missing}")
    
    def prepare_data(self, data, features=None, class_col=None, **kwargs):
        """
        Prepara datos para RadViz calculando _weights normalizados y coordenadas x,y.
        
        Esta implementación replica la lógica de MatrixLayout.map_radviz() para
        calcular los pesos normalizados y las coordenadas proyectadas que el
        renderer JavaScript necesita.
        
        Returns:
            list: Lista de puntos con {x, y, category, _weights}
        """
        if not (HAS_PANDAS and isinstance(data, pd.DataFrame)):
            # Convertir lista de dicts a DataFrame si es necesario
            if isinstance(data, list) and data:
                data = pd.DataFrame(data)
            else:
                raise ChartError("RadViz requiere datos en formato DataFrame o lista de diccionarios")
        
        df = data.copy()
        
        # Usar las features proporcionadas
        feats = [f for f in features if f in df.columns]
        
        if len(feats) < 2:
            raise ChartError(f"Se requieren al menos 2 features para RadViz. Features disponibles: {list(df.columns)}")
        
        # Normalizar features a 0-1 y manejar valores NaN
        for c in feats:
            col = df[c].astype(float)
            col = col.fillna(0.5)
            mn, mx = col.min(), col.max()
            if mx > mn:
                df[c] = (col - mn) / (mx - mn)
            else:
                df[c] = 0.5
        
        # Calcular posiciones de anchors en círculo unitario
        k = len(feats)
        anchors = []
        for i in range(k):
            ang = 2 * math.pi * i / k - math.pi / 2  # Empezar desde arriba
            anchors.append((math.cos(ang), math.sin(ang)))
        
        points = []
        for idx, row in df.iterrows():
            try:
                # Obtener weights normalizados
                weights = [float(row[c]) if not (isinstance(row[c], float) and math.isnan(row[c])) else 0.5 for c in feats]
                weights = [w if not (math.isnan(w) or math.isinf(w)) else 0.5 for w in weights]
                
                # Calcular posición ponderada
                s = sum(weights) or 1.0
                if s == 0:
                    s = 1.0
                
                x = sum(w * anchors[i][0] for i, w in enumerate(weights)) / s
                y = sum(w * anchors[i][1] for i, w in enumerate(weights)) / s
                
                # Validar coordenadas
                if math.isnan(x) or math.isinf(x):
                    x = 0.0
                if math.isnan(y) or math.isinf(y):
                    y = 0.0
                
                # Manejar categoría
                category = None
                if class_col and class_col in df.columns:
                    cat_val = row[class_col]
                    if cat_val is not None and not (isinstance(cat_val, float) and math.isnan(cat_val)):
                        category = str(cat_val)
                
                point_data = {
                    'x': float(x),
                    'y': float(y),
                    'category': category,
                    '_weights': [float(w) for w in weights]
                }
                points.append(point_data)
            except Exception:
                continue
        
        return points, feats  # Retornar también las features usadas
    
    def get_spec(self, data, features=None, class_col=None, **kwargs):
        self.validate_data(data, features=features)
        radviz_data, used_features = self.prepare_data(data, features=features, class_col=class_col)
        if not radviz_data:
            raise ChartError("No se pudieron preparar datos para radviz")
        spec = {
            'type': self.chart_type,
            'data': radviz_data,
            'features': used_features,
        }
        if class_col:
            spec['class_col'] = class_col
        if kwargs:
            spec['options'] = kwargs
        return spec

