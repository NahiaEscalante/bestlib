"""
Registry de gráficos para BESTLIB
"""
from typing import Dict, Type, List
from .base import ChartBase
from ..core.exceptions import ChartError
from ..core.registry import Registry as CoreRegistry


class ChartRegistry:
    """
    Registry global de tipos de gráficos.
    Permite registrar nuevos gráficos sin modificar código existente.
    """
    
    _charts: Dict[str, Type[ChartBase]] = {}  # {chart_type: ChartClass}
    
    @classmethod
    def register(cls, chart_class: Type[ChartBase]):
        """
        Registra un nuevo tipo de gráfico.
        
        Args:
            chart_class: Clase de gráfico que hereda de ChartBase
        
        Raises:
            ChartError: Si el chart_type ya está registrado
        """
        # Crear instancia temporal para obtener chart_type
        instance = chart_class()
        chart_type = instance.chart_type
        
        if chart_type in cls._charts:
            # Permitir re-registro (útil para hot-reload en desarrollo)
            pass
        
        cls._charts[chart_type] = chart_class
        
        # Mantener Registry central sincronizado
        if CoreRegistry:
            CoreRegistry.register('chart', chart_type, chart_class)
    
    @classmethod
    def get(cls, chart_type: str) -> ChartBase:
        """
        Obtiene una instancia de gráfico por tipo.
        
        Args:
            chart_type: Tipo de gráfico (ej: 'scatter', 'bar')
        
        Returns:
            ChartBase: Instancia del gráfico
        
        Raises:
            ChartError: Si el tipo no está registrado
        """
        if chart_type not in cls._charts:
            # Revisar Registry central por si fue registrado allí primero
            if CoreRegistry and CoreRegistry.is_registered('chart', chart_type):
                cls._charts[chart_type] = CoreRegistry.get('chart', chart_type)
            else:
                available = list(cls._charts.keys())
                raise ChartError(
                    f"Chart type '{chart_type}' not registered. "
                    f"Available types: {available}"
                )
        
        chart_class = cls._charts[chart_type]
        return chart_class()
    
    @classmethod
    def list_types(cls) -> List[str]:
        """
        Lista todos los tipos de gráficos registrados.
        
        Returns:
            list: Lista de tipos de gráficos
        """
        return list(cls._charts.keys())
    
    @classmethod
    def is_registered(cls, chart_type: str) -> bool:
        """
        Verifica si un tipo de gráfico está registrado.
        
        Args:
            chart_type: Tipo de gráfico
        
        Returns:
            bool: True si está registrado
        """
        return chart_type in cls._charts
    
    @classmethod
    def get_all(cls) -> Dict[str, Type[ChartBase]]:
        """
        Obtiene todos los gráficos registrados.
        
        Returns:
            dict: Diccionario de {chart_type: ChartClass}
        """
        return cls._charts.copy()

