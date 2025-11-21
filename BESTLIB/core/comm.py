"""
Sistema de comunicación bidireccional JS ↔ Python
"""
import weakref
from .exceptions import CommunicationError


class CommManager:
    """
    Gestor de comunicación bidireccional entre JavaScript y Python.
    Maneja el registro de Comm targets de Jupyter y el routing de mensajes.
    """
    
    _instances = {}  # dict[str, weakref.ReferenceType] - Instancias registradas
    _comm_registered = False
    _debug = False
    
    @classmethod
    def set_debug(cls, enabled: bool):
        """Activa/desactiva mensajes de debug"""
        cls._debug = enabled
    
    @classmethod
    def register_instance(cls, div_id, instance):
        """
        Registra una instancia para recibir eventos.
        
        Args:
            div_id (str): ID del div contenedor
            instance: Instancia a registrar (weak reference)
        """
        cls._instances[div_id] = weakref.ref(instance)
    
    @classmethod
    def unregister_instance(cls, div_id):
        """Desregistra una instancia"""
        if div_id in cls._instances:
            del cls._instances[div_id]
    
    @classmethod
    def get_instance(cls, div_id):
        """Obtiene instancia por div_id (si aún existe)"""
        inst_ref = cls._instances.get(div_id)
        return inst_ref() if inst_ref else None
    
    @classmethod
    def register_comm(cls, force=False):
        """
        Registra manualmente el comm target de Jupyter.
        
        Args:
            force (bool): Si True, fuerza el re-registro
        
        Returns:
            bool: True si el registro fue exitoso
        """
        if cls._comm_registered and not force:
            if cls._debug:
                print("ℹ️ [CommManager] Comm ya estaba registrado")
            return True
        
        if force:
            cls._comm_registered = False
        
        return cls._ensure_comm_target()
    
    @classmethod
    def _ensure_comm_target(cls):
        """
        Registra el comm target de Jupyter para recibir eventos desde JS.
        
        Returns:
            bool: True si el registro fue exitoso
        """
        if cls._comm_registered:
            return True
        
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if not ip or not hasattr(ip, "kernel"):
                if cls._debug:
                    print("⚠️ [CommManager] No hay kernel de IPython disponible")
                return False
            
            km = ip.kernel.comm_manager
            
            def _target(comm, open_msg):
                """Handler del comm target que procesa mensajes desde JS"""
                div_id = open_msg['content']['data'].get('div_id', 'unknown')
                
                if cls._debug:
                    print(f"🔗 [CommManager] Comm abierto para div_id: {div_id}")
                
                @comm.on_msg
                def _recv(msg):
                    cls._handle_message(div_id, msg)
            
            km.register_target("bestlib_matrix", _target)
            cls._comm_registered = True
            
            if cls._debug:
                print("✅ [CommManager] Comm target 'bestlib_matrix' registrado exitosamente")
            
            return True
            
        except Exception as e:
            print(f"❌ [CommManager] No se pudo registrar comm: {e}")
            if cls._debug:
                import traceback
                traceback.print_exc()
            return False
    
    @classmethod
    def _handle_message(cls, div_id, msg):
        """
        Maneja un mensaje recibido desde JavaScript.
        ✅ MEJORADO: Validación de payload y mejor manejo de errores.
        
        Args:
            div_id (str): ID del div contenedor
            msg: Mensaje de comm
        """
        try:
            data = msg["content"]["data"]
            event_type = data.get("type")
            payload = data.get("payload")
            
            # ✅ CORRECCIÓN: Validar estructura básica del payload
            if not isinstance(payload, dict):
                if cls._debug:
                    print(f"⚠️ [CommManager] Payload no es dict: {type(payload)}")
                # Intentar convertir o crear payload vacío
                if payload is None:
                    payload = {}
                else:
                    payload = {"raw": payload}
            
            # ✅ CORRECCIÓN: Validar que items exista si es evento de selección
            if event_type == 'select':
                if 'items' not in payload:
                    if cls._debug:
                        print(f"⚠️ [CommManager] Evento 'select' sin campo 'items', agregando items vacío")
                    payload['items'] = []
                # Asegurar que items sea una lista
                if not isinstance(payload.get('items'), list):
                    if cls._debug:
                        print(f"⚠️ [CommManager] items no es lista: {type(payload.get('items'))}, convirtiendo")
                    items = payload.get('items')
                    payload['items'] = [items] if items is not None else []
            
            if cls._debug:
                print(f"📩 [CommManager] Evento recibido:")
                print(f"   - Tipo: {event_type}")
                print(f"   - Div ID: {div_id}")
                print(f"   - Payload keys: {list(payload.keys())}")
                if event_type == 'select':
                    print(f"   - Items count: {len(payload.get('items', []))}")
            
            # Buscar instancia por div_id
            instance = cls.get_instance(div_id)
            
            if instance:
                # ✅ CORRECCIÓN CRÍTICA: Usar EventManager si está disponible (sistema modular)
                if hasattr(instance, "_event_manager"):
                    # Usar EventManager de la instancia (sistema modular)
                    instance._event_manager.emit(event_type, payload)
                    if cls._debug:
                        print(f"   ✅ Evento emitido a EventManager de instancia")
                    return  # ✅ IMPORTANTE: Salir después de emitir al EventManager
                
                # ✅ CORRECCIÓN: También verificar sistema legacy (_handlers) para compatibilidad
                if hasattr(instance, "_handlers"):
                    # Sistema legacy: buscar handlers en _handlers
                    handlers = instance._handlers.get(event_type, [])
                    if handlers:
                        if not isinstance(handlers, list):
                            handlers = [handlers]
                        for handler in handlers:
                            try:
                                handler(payload)
                            except Exception as e:
                                if cls._debug:
                                    print(f"   ❌ Error en handler legacy: {e}")
                                    import traceback
                                    traceback.print_exc()
                        if cls._debug:
                            print(f"   ✅ {len(handlers)} handler(s) legacy ejecutado(s)")
                        return  # ✅ IMPORTANTE: Salir después de ejecutar handlers legacy
                    else:
                        if cls._debug:
                            print(f"   ⚠️ No hay handler registrado para '{event_type}' en sistema legacy")
                else:
                    if cls._debug:
                        print(f"   ⚠️ Instancia no tiene _event_manager ni _handlers")
            else:
                if cls._debug:
                    print(f"   ⚠️ No se encontró instancia para div_id '{div_id}'")
        
        except Exception as e:
            error_msg = f"❌ [CommManager] Error procesando mensaje para div_id '{div_id}': {e}"
            print(error_msg)
            if cls._debug:
                import traceback
                traceback.print_exc()
    
    @classmethod
    def get_status(cls):
        """Retorna el estado actual del sistema de comunicación"""
        active_instances = {
            div_id: ref() is not None 
            for div_id, ref in cls._instances.items()
        }
        
        return {
            "comm_registered": cls._comm_registered,
            "debug_mode": cls._debug,
            "active_instances": sum(active_instances.values()),
            "total_instances": len(cls._instances),
            "instance_ids": list(cls._instances.keys()),
        }


def get_comm_engine():
    """
    Obtiene el engine de comunicación apropiado según el entorno.
    
    Esta función será extendida para soportar múltiples entornos.
    Por ahora retorna CommManager para Jupyter.
    
    Returns:
        CommManager: Engine de comunicación
    """
    # Por ahora solo soportamos Jupyter
    # En el futuro se detectará el entorno automáticamente
    return CommManager

