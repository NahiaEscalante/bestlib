"""Violin Chart"""
from collections import defaultdict
import numpy as np

from .base import ChartBase
from ..core.exceptions import ChartError, DataError

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class ViolinChart(ChartBase):
    @property
    def chart_type(self):
        return 'violin'
    
    def validate_data(self, data, value_col=None, **kwargs):
        if not value_col:
            raise ChartError("value_col es requerido para violin plot")
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if value_col not in data.columns:
                raise DataError(f"Columna '{value_col}' no encontrada en los datos")
    
    def prepare_data(self, data, value_col=None, category_col=None, bins=50, **kwargs):
        """
        Prepara datos para violin plot calculando perfiles de densidad (KDE).
        
        Args:
            data: DataFrame o lista de diccionarios
            value_col: Columna con valores numéricos
            category_col: Columna de categorías (opcional)
            bins: Número de puntos para el perfil de densidad
            
        Returns:
            Lista de objetos {category: str, profile: [{y: float, w: float}]}
        """
        groups = defaultdict(list)
        original_rows = defaultdict(list)
        
        # Agrupar valores por categoría
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            cols = [value_col]
            if category_col:
                cols.append(category_col)
            subset = data[cols].dropna()
            for idx, row in subset.iterrows():
                cat = row[category_col] if category_col else 'All'
                val = float(row[value_col])
                groups[str(cat)].append(val)
                # Guardar fila original completa para selección posterior
                original_rows[str(cat)].append(data.loc[idx].to_dict())
        else:
            for item in data or []:
                if value_col not in item:
                    continue
                cat = item.get(category_col, 'All') if category_col else 'All'
                try:
                    val = float(item[value_col])
                except (TypeError, ValueError):
                    continue
                key = str(cat)
                groups[key].append(val)
                # Guardar copia de la fila original completa
                original_rows[key].append(item.copy())
        
        # Calcular perfiles de densidad para cada categoría
        violin_data = []
        for cat, values in groups.items():
            if len(values) < 2:
                # Si hay muy pocos valores, crear un perfil simple
                if len(values) == 1:
                    y_val = values[0]
                    profile = [
                        {'y': y_val, 'w': 0.01}
                    ]
                else:
                    profile = []
            else:
                # Calcular KDE si scipy está disponible
                if HAS_SCIPY:
                    try:
                        # Usar gaussian_kde de scipy
                        kde = stats.gaussian_kde(values)
                        
                        # Generar puntos para evaluar la densidad
                        y_min, y_max = min(values), max(values)
                        y_range = y_max - y_min
                        y_points = np.linspace(y_min - 0.1 * y_range, y_max + 0.1 * y_range, bins)
                        
                        # Evaluar densidad en cada punto
                        densities = kde(y_points)
                        
                        # Normalizar densidades para que el máximo sea 1
                        max_density = max(densities) if max(densities) > 0 else 1
                        normalized_densities = densities / max_density
                        
                        # Crear perfil
                        profile = [
                            {'y': float(y), 'w': float(w)}
                            for y, w in zip(y_points, normalized_densities)
                            if w > 0.01  # Filtrar valores muy pequeños
                        ]
                    except Exception:
                        # Si falla KDE, usar histograma como fallback
                        profile = self._histogram_fallback(values, bins)
                else:
                    # Si no hay scipy, usar histograma
                    profile = self._histogram_fallback(values, bins)
            
            if profile:
                violin_data.append({
                    'category': cat,
                    'profile': profile,
                    # Adjuntar filas originales para selección por categoría
                    '_original_rows': original_rows.get(cat, [])
                })
        
        return violin_data
    
    def _histogram_fallback(self, values, bins):
        """Crea un perfil de densidad usando histograma cuando scipy no está disponible."""
        try:
            counts, bin_edges = np.histogram(values, bins=min(bins, len(values)))
            max_count = max(counts) if max(counts) > 0 else 1
            
            profile = []
            for i in range(len(counts)):
                y = (bin_edges[i] + bin_edges[i+1]) / 2  # Centro del bin
                w = counts[i] / max_count  # Densidad normalizada
                if w > 0.01:
                    profile.append({'y': float(y), 'w': float(w)})
            
            return profile
        except Exception:
            return []
    
    def get_spec(self, data, value_col=None, category_col=None, bins=50, **kwargs):
        self.validate_data(data, value_col=value_col, category_col=category_col)
        violin_data = self.prepare_data(data, value_col=value_col, category_col=category_col, bins=bins)
        
        if not violin_data:
            raise ChartError("No se pudieron preparar datos para violin plot")
        
        spec = {
            'type': self.chart_type,
            'data': violin_data,
            'value_col': value_col,
        }
        if category_col:
            spec['category_col'] = category_col
        
        # Procesar figsize y otras opciones
        from ..utils.figsize import process_figsize_in_kwargs
        process_figsize_in_kwargs(kwargs)
        
        if kwargs:
            spec.update(kwargs)
        
        return spec

