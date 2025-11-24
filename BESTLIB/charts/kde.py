"""
KDE (Kernel Density Estimation) Chart para BESTLIB
Estimación de densidad de kernel - VERSIÓN REESCRITA
"""
from .base import ChartBase
from ..utils.figsize import process_figsize_in_kwargs
from ..core.exceptions import ChartError
import json

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
    HAS_NUMPY = True
except ImportError:
    HAS_PANDAS = False
    HAS_NUMPY = False
    pd = None
    np = None


class KdeChart(ChartBase):
    """Gráfico de estimación de densidad de kernel (KDE)"""
    
    @property
    def chart_type(self):
        return 'kde'
    
    def validate_data(self, data, column=None, **kwargs):
        """Valida que los datos sean adecuados para KDE."""
        if not column:
            raise ChartError("column es requerido para KDE")
        
        if not HAS_PANDAS or not HAS_NUMPY:
            raise ChartError("KDE requiere pandas y numpy instalados")
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if column not in data.columns:
                raise ChartError(f"Columna '{column}' no encontrada")
            if not pd.api.types.is_numeric_dtype(data[column]):
                raise ChartError(f"Columna '{column}' debe ser numérica")
        elif isinstance(data, list) and len(data) > 0:
            if column not in data[0]:
                raise ChartError(f"Columna '{column}' no encontrada")
        else:
            raise ChartError("Los datos deben ser un DataFrame o lista no vacía")
    
    def prepare_data(self, data, column=None, bandwidth=None, **kwargs):
        """
        Prepara datos para KDE calculando la densidad.
        CRÍTICO: Retorna lista de diccionarios con tipos Python nativos (no numpy).
        """
        # Extraer valores numéricos
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            values = data[column].dropna().values
        else:
            values = [d[column] for d in data if column in d and d[column] is not None]
            values = np.array(values)
        
        if len(values) == 0:
            raise ChartError(f"No hay datos válidos en columna '{column}'")
        
        # Calcular KDE
        try:
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(values, bw_method=bandwidth) if bandwidth else gaussian_kde(values)
            
            # Crear rango de evaluación
            x_min = float(np.min(values))
            x_max = float(np.max(values))
            x_range = x_max - x_min
            x_padding = x_range * 0.1
            
            # Generar puntos de evaluación
            x_eval = np.linspace(x_min - x_padding, x_max + x_padding, 200)
            y_density = kde(x_eval)
            
        except ImportError:
            # Fallback: histograma normalizado
            hist, bin_edges = np.histogram(values, bins=50, density=True)
            x_eval = (bin_edges[:-1] + bin_edges[1:]) / 2
            y_density = hist
        
        # CRÍTICO: Convertir explícitamente a tipos Python nativos
        # No usar numpy types que no serializan bien a JSON
        kde_points = []
        for x, y in zip(x_eval, y_density):
            # Asegurar que x e y son float Python nativos, no numpy.float64
            kde_points.append({
                'x': float(x),
                'y': float(y)
            })
        
        return kde_points
    
    def get_spec(self, data, column=None, bandwidth=None, **kwargs):
        """
        Genera la especificación del KDE.
        CRÍTICO: Asegura que todos los datos sean serializables a JSON.
        """
        try:
            # Validar datos
            self.validate_data(data, column=column, **kwargs)
            
            # Preparar datos KDE
            kde_points = self.prepare_data(data, column=column, bandwidth=bandwidth, **kwargs)
            
            # Verificar que tenemos datos válidos
            if not kde_points or len(kde_points) == 0:
                raise ChartError("No se pudieron calcular puntos KDE")
            
            # Procesar figsize
            process_figsize_in_kwargs(kwargs)
            
            # Extraer opciones con valores por defecto
            color = kwargs.pop('color', '#4a90e2')
            stroke_width = kwargs.pop('strokeWidth', 2)
            fill = kwargs.pop('fill', True)
            opacity = kwargs.pop('opacity', 0.3)
            axes = kwargs.pop('axes', True)
            x_label = kwargs.pop('xLabel', column if column else 'Value')
            y_label = kwargs.pop('yLabel', 'Density')
            
            # Construir spec - ESTRUCTURA LIMPIA
            spec = {
                'type': 'kde',
                'data': kde_points,  # Lista de {x, y} con tipos Python nativos
                'encoding': {
                    'x': {'field': 'x'},
                    'y': {'field': 'y'}
                },
                'options': {
                    'color': color,
                    'strokeWidth': stroke_width,
                    'fill': fill,
                    'opacity': opacity,
                    'axes': axes,
                    'xLabel': x_label,
                    'yLabel': y_label
                }
            }
            
            # Agregar figsize si existe
            if 'figsize' in kwargs:
                spec['options']['figsize'] = kwargs['figsize']
            
            # Verificar que el spec es serializable a JSON
            try:
                json.dumps(spec)
            except (TypeError, ValueError) as e:
                raise ChartError(f"Spec no es serializable a JSON: {e}")
            
            return spec
            
        except Exception as e:
            # En caso de error, retornar spec vacío pero válido
            print(f"[KDE ERROR] {str(e)}")
            return {
                'type': 'kde',
                'data': [],
                'encoding': {'x': {'field': 'x'}, 'y': {'field': 'y'}},
                'options': {}
            }

