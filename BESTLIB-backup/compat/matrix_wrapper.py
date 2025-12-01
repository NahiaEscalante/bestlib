"""
Wrapper de compatibilidad para MatrixLayout
"""
import warnings
from ..matrix import MatrixLayout as _MatrixLayout

warnings.warn(
    "BESTLIB está siendo modularizado. MatrixLayout ahora usa nuevos módulos internamente.",
    FutureWarning,
    stacklevel=2
)


class MatrixLayoutCompat(_MatrixLayout):
    """
    Wrapper de compatibilidad para MatrixLayout.
    Mantiene la API original mientras internamente usa los nuevos módulos.
    """
    
    # Delegar métodos estáticos a la clase original
    @classmethod
    def map(cls, mapping):
        """Mapear gráficos a letras (compatibilidad)"""
        return _MatrixLayout.map(mapping)
    
    @classmethod
    def map_scatter(cls, letter, data, **kwargs):
        """Wrapper para map_scatter usando nuevo sistema de gráficos"""
        from ..charts.registry import ChartRegistry
        
        chart = ChartRegistry.get('scatter')
        spec = chart.get_spec(data, **kwargs)
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_barchart(cls, letter, data, **kwargs):
        """Wrapper para map_barchart usando nuevo sistema de gráficos"""
        from ..charts.registry import ChartRegistry
        
        chart = ChartRegistry.get('bar')
        spec = chart.get_spec(data, **kwargs)
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    # Métodos adicionales delegados...
    # Nota: Para compatibilidad completa, todos los map_* deberían ser wrappers


# Alias para compatibilidad
MatrixLayout = MatrixLayoutCompat

