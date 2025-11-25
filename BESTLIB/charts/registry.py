"""
Registry de gráficos para BESTLIB
"""
from typing import Dict, Type, List, Optional, Callable, Any
from .base import ChartBase
from ..core.exceptions import ChartError


class ChartRegistry:
    """
    Registry global de tipos de gráficos.
    Permite registrar nuevos gráficos sin modificar código existente.
    """
    
    _charts: Dict[str, Type[ChartBase]] = {}  # {chart_type: ChartClass}
    
    @classmethod
    def register(cls, chart_class: Type[ChartBase]):
        """
        Registra un nuevo tipo de gráfico con validación estricta.
        
        Args:
            chart_class: Clase de gráfico que hereda de ChartBase
        
        Raises:
            TypeError: Si chart_class no es una clase o no hereda de ChartBase
            ChartError: Si no se puede instanciar o chart_type es inválido
        """
        # Validate that chart_class is a class
        if not isinstance(chart_class, type):
            raise TypeError(f"chart_class must be a class, received: {type(chart_class).__name__}")
        
        # Validate that chart_class inherits from ChartBase
        if not issubclass(chart_class, ChartBase):
            raise TypeError(f"chart_class must inherit from ChartBase, received: {chart_class.__name__}")
        
        # Attempt to instantiate to get chart_type
        try:
            instance = chart_class()
            chart_type = instance.chart_type
        except Exception as e:
            raise ChartError(f"Failed to instantiate chart_class: {e}") from e
        
        # Validate that chart_type is a non-empty string
        if not isinstance(chart_type, str) or not chart_type:
            raise ChartError(f"chart_type must be a non-empty str, received: {chart_type!r}")
        
        # Allow re-registration (useful for hot-reload in development)
        cls._charts[chart_type] = chart_class
    
    @classmethod
    def get(cls, chart_type: str) -> Optional[ChartBase]:
        """
        Obtiene una instancia de gráfico por tipo.
        
        Args:
            chart_type: Tipo de gráfico (ej: 'scatter', 'bar')
        
        Returns:
            Optional[ChartBase]: Instancia del gráfico, o None si no está registrado
        
        Raises:
            TypeError: Si chart_type no es un str no vacío
        """
        # Validate input type
        if not isinstance(chart_type, str) or not chart_type:
            raise TypeError(f"chart_type must be a non-empty str, received: {chart_type!r}")
        
        # Return None if chart not registered (NO exception)
        if chart_type not in cls._charts:
            return None
        
        chart_class = cls._charts[chart_type]
        try:
            instance = chart_class()
            # ✅ CRIT-008: Validación completa de instancia
            if not isinstance(instance, ChartBase):
                # Silenciar error si no hay debug, pero retornar None
                return None
            # ✅ Validar que chart_type sea consistente
            if not hasattr(instance, 'chart_type'):
                return None
            instance_chart_type = instance.chart_type
            if not isinstance(instance_chart_type, str) or instance_chart_type != chart_type:
                # chart_type inconsistente
                return None
            return instance
        except (TypeError, ValueError, AttributeError) as e:
            # Errores esperados en instanciación
            return None
        except Exception as e:
            # Error inesperado - registrar pero retornar None para compatibilidad
            return None
    
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

