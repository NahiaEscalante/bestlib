"""
Reactive Engine - Motor reactivo unificado para BESTLIB
"""
from ..core.exceptions import BestlibError


class ReactiveEngine:
    """
    Motor reactivo centralizado que gestiona el estado y actualizaciones.
    
    Proporciona un flujo unidireccional de datos para evitar loops infinitos.
    """
    
    def __init__(self):
        """Inicializa el motor reactivo"""
        self._state = {}  # Estado centralizado
        self._subscriptions = {}  # {event: [callbacks]}
        self._updating = False  # Flag para prevenir loops
    
    def set_state(self, key, value):
        """
        Establece un valor en el estado.
        
        Args:
            key (str): Clave del estado
            value: Valor a establecer
        """
        # Evitar loops infinitos
        if self._updating:
            return
        
        old_value = self._state.get(key)
        
        # Solo actualizar si hay cambio real
        if old_value != value:
            self._updating = True
            try:
                self._state[key] = value
                self._notify_subscribers(key, value, old_value)
            finally:
                self._updating = False
    
    def get_state(self, key, default=None):
        """
        Obtiene un valor del estado.
        
        Args:
            key (str): Clave del estado
            default: Valor por defecto si no existe
        
        Returns:
            Valor del estado o default
        """
        return self._state.get(key, default)
    
    def subscribe(self, event, callback):
        """
        Suscribe un callback a un evento.
        
        Args:
            event (str): Nombre del evento
            callback (callable): Función callback
        """
        if event not in self._subscriptions:
            self._subscriptions[event] = []
        
        # Evitar duplicados
        if callback not in self._subscriptions[event]:
            self._subscriptions[event].append(callback)
    
    def unsubscribe(self, event, callback):
        """
        Desuscribe un callback de un evento.
        
        Args:
            event (str): Nombre del evento
            callback (callable): Función callback
        """
        if event in self._subscriptions:
            if callback in self._subscriptions[event]:
                self._subscriptions[event].remove(callback)
    
    def _notify_subscribers(self, key, new_value, old_value):
        """
        Notifica a los suscriptores de un cambio de estado.
        
        Args:
            key (str): Clave que cambió
            new_value: Nuevo valor
            old_value: Valor anterior
        """
        # Notificar cambios específicos por clave
        if key in self._subscriptions:
            for callback in self._subscriptions[key]:
                try:
                    callback(new_value, old_value)
                except Exception as e:
                    print(f"Error en callback para '{key}': {e}")
        
        # Notificar cambios globales
        if '*' in self._subscriptions:
            for callback in self._subscriptions['*']:
                try:
                    callback(key, new_value, old_value)
                except Exception as e:
                    print(f"Error en callback global: {e}")
    
    def clear_state(self):
        """Limpia todo el estado"""
        self._state.clear()
    
    def get_all_state(self):
        """Retorna todo el estado"""
        return self._state.copy()

