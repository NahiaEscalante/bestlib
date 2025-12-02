"""Star Coordinates Chart"""
from .base import ChartBase
from ..core.exceptions import ChartError, DataError
import math

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


class StarCoordinatesChart(ChartBase):
    @property
    def chart_type(self):
        return 'star_coordinates'
    
    def validate_data(self, data, features=None, **kwargs):
        if not features:
            raise ChartError("features es requerido para star coordinates")
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            missing = [f for f in features if f not in data.columns]
            if missing:
                raise DataError(f"Faltan columnas: {missing}")
    
    def prepare_data(self, data, features=None, class_col=None, **kwargs):
        """
        Prepara datos para Star Coordinates calculando _weights normalizados y coordenadas x,y.
        
        Esta implementación replica la lógica de MatrixLayout.map_star_coordinates() para
        calcular los pesos normalizados y las coordenadas proyectadas que el
        renderer JavaScript necesita.
        
        Returns:
            tuple: (lista de puntos con {x, y, category, _weights}, features ordenados)
        """
        if not (HAS_PANDAS and isinstance(data, pd.DataFrame)):
            # Convertir lista de dicts a DataFrame si es necesario
            if isinstance(data, list) and data:
                data = pd.DataFrame(data)
            else:
                raise ChartError("Star Coordinates requiere datos en formato DataFrame o lista de diccionarios")
        
        df = data.copy()
        
        # Usar las features proporcionadas
        feats = [f for f in features if f in df.columns]
        
        if len(feats) < 2:
            raise ChartError(f"Se requieren al menos 2 features para Star Coordinates. Features disponibles: {list(df.columns)}")
        
        # Normalizar features a 0-1 y manejar valores NaN
        for c in feats:
            col = df[c].astype(float)
            col = col.fillna(0.5)
            mn, mx = col.min(), col.max()
            if mx > mn:
                df[c] = (col - mn) / (mx - mn)
            else:
                df[c] = 0.5
        
        k = len(feats)
        # IMPORTANTE: Ordenar features alfabéticamente para mantener orden consistente
        sorted_feats = sorted(feats)
        
        # Calcular posiciones de anchors en círculo unitario
        anchors = []
        for i in range(k):
            ang = 2 * math.pi * i / k - math.pi / 2  # Empezar desde arriba
            anchors.append((math.cos(ang), math.sin(ang)))
        
        points = []
        for idx, row in df.iterrows():
            try:
                # Obtener weights normalizados en el orden original de feats
                weights_original = [float(row[c]) if not (isinstance(row[c], float) and math.isnan(row[c])) else 0.5 for c in feats]
                weights_original = [w if not (math.isnan(w) or math.isinf(w)) else 0.5 for w in weights_original]
                
                # IMPORTANTE: Reordenar weights al orden alfabético para que coincidan con sorted_feats
                weights = [weights_original[feats.index(feat)] for feat in sorted_feats]
                
                # Calcular posición ponderada (Star Coordinates)
                s = sum(weights) or 1.0
                if s == 0:
                    s = 1.0
                
                # Calcular posición ponderada
                x = sum(weights[i] * anchors[i][0] for i in range(len(weights))) / s
                y = sum(weights[i] * anchors[i][1] for i in range(len(weights))) / s
                
                # Normalizar para que los puntos estén dentro de un círculo unitario
                distance = math.sqrt(x * x + y * y)
                if distance > 1.0:
                    x = x / distance
                    y = y / distance
                
                # Validar coordenadas
                if math.isnan(x) or math.isinf(x):
                    x = 0.0
                if math.isnan(y) or math.isinf(y):
                    y = 0.0
                
                # Asegurar que las coordenadas estén en [-1, 1]
                x = max(-1.0, min(1.0, x))
                y = max(-1.0, min(1.0, y))
                
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
        
        return points, sorted_feats
    
    def get_spec(self, data, features=None, class_col=None, **kwargs):
        self.validate_data(data, features=features)
        star_data, sorted_feats = self.prepare_data(data, features=features, class_col=class_col)
        if not star_data:
            raise ChartError("No se pudieron preparar datos para star coordinates")
        spec = {
            'type': self.chart_type,
            'data': star_data,
            'features': sorted_feats,  # Usar features ordenados
        }
        if class_col:
            spec['class_col'] = class_col
        if kwargs:
            spec['options'] = kwargs
        return spec

