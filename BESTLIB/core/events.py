"""
Sistema de eventos y callbacks para BESTLIB

⚠️ DEPRECATED: Este módulo está oficialmente deprecado.

CRIT-013: EventManager Deshabilitado

Decisión arquitectónica:
Se decidió no rehabilitar EventManager y declararlo oficialmente deprecado.
core/events.py se mantiene solo como stub para compatibilidad,
y toda la gestión de eventos se realiza a través de core/comm.py.
No hay impacto en la funcionalidad actual.

Este módulo NO debe usarse en ningún flujo de ejecución.
Use core/comm.py (CommManager) para gestión de eventos.
"""
import warnings
from typing import Any, Callable, Dict, List, Optional


class EventManager:
    """
    Gestor centralizado de eventos y callbacks (DEPRECATED).
    
    ⚠️ DEPRECATED: Esta clase está oficialmente deprecada y no debe usarse.
    
    Toda la gestión de eventos se realiza a través de core/comm.py (CommManager).
    Este stub se mantiene solo para compatibilidad hacia atrás.
    
    Todos los métodos lanzan RuntimeError si se intentan usar.
    """
    
    _global_handlers = {}  # dict[str, callable] - Handlers globales (no usado)
    _debug = False  # Modo debug (no usado)
    
    @classmethod
    def set_debug(cls, enabled: bool) -> None:
        """
        DEPRECATED: Este método no debe usarse.
        
        Raises:
            RuntimeError: Siempre, porque EventManager está deprecado
        """
        raise RuntimeError(
            "EventManager está deprecado. Use core/comm.py (CommManager) para gestión de eventos. "
            "Ver CRIT-013 en documentación."
        )
    
    @classmethod
    def on_global(cls, event: str, func: Callable[[Any], None]) -> None:
        """
        DEPRECATED: Este método no debe usarse.
        
        Raises:
            RuntimeError: Siempre, porque EventManager está deprecado
        """
        raise RuntimeError(
            "EventManager está deprecado. Use core/comm.py (CommManager) para gestión de eventos. "
            "Ver CRIT-013 en documentación."
        )
    
    @classmethod
    def get_global_handler(cls, event: str) -> Optional[Callable[[Any], None]]:
        """
        DEPRECATED: Este método no debe usarse.
        
        Raises:
            RuntimeError: Siempre, porque EventManager está deprecado
        """
        raise RuntimeError(
            "EventManager está deprecado. Use core/comm.py (CommManager) para gestión de eventos. "
            "Ver CRIT-013 en documentación."
        )
    
    @classmethod
    def has_global_handler(cls, event: str) -> bool:
        """
        DEPRECATED: Este método no debe usarse.
        
        Raises:
            RuntimeError: Siempre, porque EventManager está deprecado
        """
        raise RuntimeError(
            "EventManager está deprecado. Use core/comm.py (CommManager) para gestión de eventos. "
            "Ver CRIT-013 en documentación."
        )
    
    def __init__(self):
        """
        Inicializa un EventManager de instancia (DEPRECATED).
        
        Raises:
            DeprecationWarning: Siempre, porque EventManager está deprecado
            RuntimeError: Siempre, porque EventManager está deprecado
        """
        warnings.warn(
            "EventManager está deprecado y no debe usarse. "
            "Use core/comm.py (CommManager) para gestión de eventos. "
            "Ver CRIT-013 en documentación.",
            DeprecationWarning,
            stacklevel=2
        )
        raise RuntimeError(
            "EventManager está deprecado. Use core/comm.py (CommManager) para gestión de eventos. "
            "Ver CRIT-013 en documentación."
        )
    
    def on(self, event: str, func: Callable[[Any], None]) -> "EventManager":
        """
        DEPRECATED: Este método no debe usarse.
        
        Raises:
            RuntimeError: Siempre, porque EventManager está deprecado
        """
        raise RuntimeError(
            "EventManager está deprecado. Use core/comm.py (CommManager) para gestión de eventos. "
            "Ver CRIT-013 en documentación."
        )
    
    def get_handlers(self, event: str) -> List[Callable[[Any], None]]:
        """
        DEPRECATED: Este método no debe usarse.
        
        Raises:
            RuntimeError: Siempre, porque EventManager está deprecado
        """
        raise RuntimeError(
            "EventManager está deprecado. Use core/comm.py (CommManager) para gestión de eventos. "
            "Ver CRIT-013 en documentación."
        )
    
    def emit(self, event: str, payload: Dict[str, Any]) -> None:
        """
        DEPRECATED: Este método no debe usarse.
        
        Raises:
            RuntimeError: Siempre, porque EventManager está deprecado
        """
        raise RuntimeError(
            "EventManager está deprecado. Use core/comm.py (CommManager) para gestión de eventos. "
            "Ver CRIT-013 en documentación."
        )
