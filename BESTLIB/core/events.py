"""
Sistema de eventos y callbacks para BESTLIB
"""
import weakref


class EventManager:
    """
    Gestor centralizado de eventos y callbacks.
    Proporciona sistema de eventos con soporte para múltiples handlers por tipo de evento.
    """
    
    _global_handlers = {}  # dict[str, callable] - Handlers globales
    _debug = False  # Modo debug
    
    @classmethod
    def set_debug(cls, enabled: bool):
        """
        Activa/desactiva mensajes de debug.
        
        Args:
            enabled (bool): Si True, activa mensajes detallados de debug.
        """
        cls._debug = enabled
    
    @classmethod
    def on_global(cls, event, func):
        """
        Registra un callback global para un tipo de evento.
        
        Los callbacks globales se ejecutan para TODOS los layouts, no solo uno específico.
        Útil para logging o procesamiento centralizado de eventos.
        
        Args:
            event (str): Tipo de evento ('select', 'click', 'brush', etc.)
            func (callable): Función callback que recibe el payload del evento
        """
        cls._global_handlers[event] = func
    
    @classmethod
    def get_global_handler(cls, event):
        """Obtiene el handler global para un tipo de evento"""
        return cls._global_handlers.get(event)
    
    @classmethod
    def has_global_handler(cls, event):
        """Verifica si existe handler global para un tipo de evento"""
        return event in cls._global_handlers
    
    def __init__(self):
        """Inicializa un EventManager de instancia"""
        self._handlers = {}  # dict[str, list[callable]] - Handlers de instancia
    
    def on(self, event, func):
        """
        Registra un callback específico para esta instancia.
        
        Nota: Si se registran múltiples handlers para el mismo evento,
        todos se ejecutarán.
        
        Args:
            event (str): Tipo de evento
            func (callable): Función callback
        
        Returns:
            self para encadenamiento
        """
        if event not in self._handlers:
            self._handlers[event] = []
        elif not isinstance(self._handlers[event], list):
            # Convertir handler único a lista
            self._handlers[event] = [self._handlers[event]]
        
        self._handlers[event].append(func)
        return self
    
    def get_handlers(self, event):
        """
        Obtiene todos los handlers para un tipo de evento (instancia + globales).
        
        Args:
            event (str): Tipo de evento
        
        Returns:
            list: Lista de handlers a ejecutar
        """
        handlers = []
        
        # Handlers de instancia
        if event in self._handlers:
            inst_handlers = self._handlers[event]
            if isinstance(inst_handlers, list):
                handlers.extend(inst_handlers)
            else:
                handlers.append(inst_handlers)
        
        # Handler global
        global_handler = self._global_handlers.get(event)
        if global_handler:
            handlers.append(global_handler)
        
        return handlers
    
    def emit(self, event, payload):
        """
        Emite un evento, ejecutando todos los handlers registrados.
        
        Args:
            event (str): Tipo de evento
            payload (dict): Datos del evento
        """
        handlers = self.get_handlers(event)
        
        if handlers:
            if self._debug:
                print(f"🔄 [EventManager] Encontrados {len(handlers)} handler(s) para evento '{event}'")
            for idx, handler in enumerate(handlers):
                try:
                    if self._debug:
                        print(f"   🔄 [EventManager] Ejecutando handler #{idx+1}/{len(handlers)}")
                    handler(payload)
                    if self._debug:
                        print(f"   ✅ [EventManager] Handler #{idx+1} completado")
                except Exception as e:
                    error_msg = f"❌ [EventManager] Error en handler #{idx+1} para evento '{event}': {e}"
                    if self._debug:
                        print(error_msg)
                        import traceback
                        traceback.print_exc()
                    else:
                        print(f"⚠️ {error_msg}")
        else:
            if self._debug:
                print(f"⚠️ [EventManager] No hay handler registrado para '{event}'")
                print(f"   Handlers disponibles: {list(self._handlers.keys())}")
                print(f"   Handlers globales: {list(self._global_handlers.keys())}")

