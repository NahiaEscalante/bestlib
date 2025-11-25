"""
Sistema de comunicación bidireccional JS ↔ Python
"""
import weakref
import threading
from typing import Optional, TYPE_CHECKING
from .exceptions import CommunicationError, get_logger

if TYPE_CHECKING:
    from ..layouts.matrix import MatrixLayout


class CommManager:
    """
    Gestor de comunicación bidireccional entre JavaScript y Python.
    Maneja el registro de Comm targets de Jupyter y el routing de mensajes.
    """
    
    _instances = {}  # dict[str, weakref.ReferenceType] - Instancias registradas
    _instances_lock = threading.Lock()  # ✅ CRIT-009: Lock para thread-safety
    _comm_registered = False
    _debug = False
    
    @classmethod
    def set_debug(cls, enabled: bool):
        """
        Activa/desactiva mensajes de debug
        
        Args:
            enabled (bool): Si True, activa mensajes de debug
        
        Raises:
            TypeError: Si enabled no es bool
        """
        if not isinstance(enabled, bool):
            raise TypeError(f"enabled must be bool, received: {type(enabled).__name__}")
        cls._debug = enabled
    
    @classmethod
    def register_instance(cls, div_id: str, instance: "MatrixLayout") -> None:
        """
        Registra una instancia para recibir eventos.
        
        Args:
            div_id (str): ID del div contenedor
            instance: Instancia a registrar (weak reference)
        
        Raises:
            ValueError: Si div_id no es str no vacío o si instance es None
        """
        if not isinstance(div_id, str) or not div_id:
            raise ValueError(f"div_id debe ser str no vacío, recibido: {div_id!r}")
        
        # ✅ NUEVO: Validar formato HTML ID (letras, números, guiones, guiones bajos)
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', div_id):
            raise ValueError(
                f"div_id debe ser un ID HTML válido (empezar con letra, "
                f"seguido de letras/números/guiones/guiones bajos), recibido: {div_id!r}"
            )
        
        if instance is None:
            raise ValueError("instance no puede ser None")
        
        # ✅ CRIT-010: Validar unicidad de div_id
        with cls._instances_lock:
            if div_id in cls._instances:
                existing_ref = cls._instances[div_id]
                existing_instance = existing_ref()
                if existing_instance is not None and existing_instance is not instance:
                    if cls._debug:
                        logger = get_logger()
                        logger.warning(f"div_id '{div_id}' ya está registrado. Sobrescribiendo instancia anterior.")
                    # Emitir warning
                    import warnings
                    warnings.warn(
                        f"div_id '{div_id}' ya está registrado. La instancia anterior será reemplazada.",
                        UserWarning,
                        stacklevel=2
                    )
            
        cls._instances[div_id] = weakref.ref(instance)
    
    @classmethod
    def unregister_instance(cls, div_id: str) -> None:
        """
        Desregistra una instancia.
        
        Args:
            div_id (str): ID del div contenedor a desregistrar
        
        Raises:
            ValueError: Si div_id no es str no vacío
        """
        with cls._instances_lock:
            if div_id in cls._instances:
                del cls._instances[div_id]
    
    @classmethod
    def _cleanup_dead_instances(cls) -> int:
        """
        Limpia referencias muertas de _instances.
        
        ✅ CRIT-009: Thread-safe usando lock.
        
        Returns:
            int: Número de instancias muertas eliminadas
        
        Raises:
            RuntimeError: Si hay error al acceder a las referencias
        """
        with cls._instances_lock:
            # Crear copia para iterar de forma segura (evita race condition)
            instances_copy = dict(cls._instances)
            dead = [k for k, ref in instances_copy.items() if ref() is None]
            for k in dead:
                if k in cls._instances:  # Verificar que aún existe
                    del cls._instances[k]
        return len(dead)
    
    @classmethod
    def get_instance(cls, div_id: str) -> Optional["MatrixLayout"]:
        """
        Obtiene instancia por div_id (si aún existe).
        
        Args:
            div_id (str): ID del div contenedor
        
        Returns:
            Optional[MatrixLayout]: Instancia si existe, None si no existe o murió
        
        Raises:
            ValueError: Si div_id no es str no vacío
        """
        # Cleanup dead instances periodically (every 10 calls)
        if not hasattr(cls, "_get_instance_counter"):
            cls._get_instance_counter = 0
        cls._get_instance_counter += 1
        if cls._get_instance_counter % 10 == 0:
            cls._cleanup_dead_instances()
        
        with cls._instances_lock:
            inst_ref = cls._instances.get(div_id)
            if inst_ref is None:
                return None
            
            instance = inst_ref()
            # ✅ Validar que la instancia sea válida
            if instance is None:
                # Instancia murió, limpiar referencia
                if div_id in cls._instances:
                    del cls._instances[div_id]
                return None
            
            return instance
    
    @classmethod
    def register_comm(cls, force: bool = False) -> bool:
        """
        Registra manualmente el comm target de Jupyter.
        
        Args:
            force (bool): Si True, fuerza el re-registro
        
        Returns:
            bool: True si el registro fue exitoso
        
        Raises:
            TypeError: Si force no es bool
            RuntimeError: Si no hay kernel de IPython disponible
        """
        if cls._comm_registered and not force:
            if cls._debug:
                logger = get_logger()
                logger.info("ℹ️ [CommManager] Comm ya estaba registrado")
            return True
        
        if force:
            cls._comm_registered = False
        
        return cls._ensure_comm_target()
    
    @classmethod
    def _ensure_comm_target(cls) -> bool:
        """
        Registra el comm target de Jupyter para recibir eventos desde JS.
        
        Returns:
            bool: True si el registro fue exitoso
        
        Raises:
            RuntimeError: Si no hay kernel de IPython disponible o falla el registro
        """
        if cls._comm_registered:
            return True
        
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if not ip or not hasattr(ip, "kernel"):
                if cls._debug:
                    logger = get_logger()
                    logger.warning("⚠️ [CommManager] No hay kernel de IPython disponible")
                return False
            
            km = ip.kernel.comm_manager
            
            def _target(comm, open_msg):
                """Handler del comm target que procesa mensajes desde JS"""
                # Validate open_msg structure
                logger = get_logger()
                if not isinstance(open_msg, dict):
                    if cls._debug:
                        logger.warning(f"⚠️ [CommManager] open_msg no es dict: {type(open_msg)}")
                    return
                
                content = open_msg.get("content", {})
                if not isinstance(content, dict):
                    if cls._debug:
                        logger.warning("⚠️ [CommManager] open_msg['content'] no es dict")
                    return
                
                data = content.get("data", {})
                if not isinstance(data, dict):
                    if cls._debug:
                        logger.warning("⚠️ [CommManager] open_msg['content']['data'] no es dict")
                    return
                
                div_id = data.get("div_id", "unknown")
                
                if cls._debug:
                    logger.info(f"🔗 [CommManager] Comm abierto para div_id: {div_id}")
                
                @comm.on_msg
                def _recv(msg):
                    cls._handle_message(div_id, msg)
            
            km.register_target("bestlib_matrix", _target)
            cls._comm_registered = True
            
            if cls._debug:
                logger = get_logger()
                logger.info("✅ [CommManager] Comm target 'bestlib_matrix' registrado exitosamente")
            
            return True
            
        except Exception as e:
            logger = get_logger()
            logger.error(f"❌ [CommManager] No se pudo registrar comm: {e}", exc_info=True)
            return False
    
    @classmethod
    def _handle_message(cls, div_id: str, msg: dict) -> None:
        """
        Maneja un mensaje recibido desde JavaScript.
        ✅ MEJORADO: Validación de payload y mejor manejo de errores.
        
        Args:
            div_id (str): ID del div contenedor
            msg (dict): Mensaje de comm
        
        Raises:
            ValueError: Si div_id no es str no vacío o msg no es dict válido
            CommunicationError: Si hay error procesando el mensaje
        """
        # Validate message structure
        if not isinstance(msg, dict):
            logger = get_logger()
            logger.warning(f"[CommManager] Invalid msg type: {type(msg)}")
            return
        
        content = msg.get("content", {})
        if not isinstance(content, dict):
            logger = get_logger()
            logger.warning("[CommManager] content is not a dict")
            return
        
        data = content.get("data", {})
        if not isinstance(data, dict):
            logger = get_logger()
            logger.warning("[CommManager] data is not a dict")
            return
        
        try:
            # ✅ NUEVO: Validar que data sea dict antes de acceder
            logger = get_logger()
            if not isinstance(data, dict):
                if cls._debug:
                    logger.warning(f"⚠️ [CommManager] data no es dict: {type(data)}")
                return
            
            event_type = data.get("type")
            payload = data.get("payload")
            
            if event_type is None:
                if cls._debug:
                    logger.warning("⚠️ [CommManager] event_type es None")
                return
            
            # ✅ CORRECCIÓN: Validar estructura básica del payload
            logger = get_logger()
            if not isinstance(payload, dict):
                if cls._debug:
                    logger.warning(f"[CommManager] Payload no es dict: {type(payload)}")
                # Intentar convertir o crear payload vacío
                if payload is None:
                    payload = {}
                else:
                    payload = {"raw": payload}
            
            # ✅ CORRECCIÓN: Validar que items exista si es evento de selección
            if event_type == 'select':
                if 'items' not in payload:
                    if cls._debug:
                        logger.warning("[CommManager] Evento 'select' sin campo 'items', agregando items vacío")
                    payload['items'] = []
                # Asegurar que items sea una lista
                if not isinstance(payload.get('items'), list):
                    if cls._debug:
                        logger.warning(f"[CommManager] items no es lista: {type(payload.get('items'))}, convirtiendo")
                    items = payload.get('items')
                    payload['items'] = [items] if items is not None else []
                
                # ✅ NUEVO: Validar que todos los elementos sean diccionarios
                valid_items = []
                for item in payload['items']:
                    if isinstance(item, dict) and item:  # Dict no vacío
                        valid_items.append(item)
                    elif item is not None:
                        if cls._debug:
                            logger.warning(f"[CommManager] Item inválido en payload: {type(item)}, omitiendo")
                payload['items'] = valid_items
            
            if cls._debug:
                logger.info(f"[CommManager] Evento recibido: tipo={event_type}, div_id={div_id}, items={len(payload.get('items', [])) if event_type == 'select' else 0}")
            
            # Buscar instancia por div_id
            instance = cls.get_instance(div_id)
            
            if instance:
                # TEMP FIX: EventManager disabled until full migration
                # Using legacy `_handlers` for all events to maintain compatibility
                # ALWAYS use legacy system first
                if hasattr(instance, "_handlers"):
                    # Sistema legacy: buscar handlers en _handlers
                    handlers = instance._handlers.get(event_type, [])
                    if handlers:
                        if not isinstance(handlers, list):
                            handlers = [handlers]
                        for handler in handlers:
                            try:
                                handler(payload)
                            except (TypeError, ValueError, AttributeError) as e:
                                # Errores esperados en handlers
                                if cls._debug:
                                    logger.warning(f"   ⚠️ Error en handler legacy: {e}")
                            except Exception as e:
                                # Error inesperado - registrar y re-raise
                                logger.error(f"   ❌ Error inesperado en handler legacy: {e}", exc_info=True)
                                # Re-raise para que el usuario sepa que algo salió mal
                                raise
                        if cls._debug:
                            logger.info(f"   ✅ {len(handlers)} handler(s) legacy ejecutado(s)")
                        return  # IMPORTANTE: Salir después de ejecutar handlers legacy
                    else:
                        if cls._debug:
                            logger.warning(f"   ⚠️ No hay handler registrado para '{event_type}' en sistema legacy")
                else:
                    if cls._debug:
                        logger.warning(f"   ⚠️ Instancia no tiene _handlers")
                
                # TEMP FIX: EventManager temporarily disabled
                # DO NOT use EventManager until migration is complete
                # if hasattr(instance, "_event_manager"):
                #     # Usar EventManager de la instancia (sistema modular)
                #     instance._event_manager.emit(event_type, payload)
                #     if cls._debug:
                #         print(f"   ✅ Evento emitido a EventManager de instancia")
                #     return
            else:
                if cls._debug:
                    logger.warning(f"   ⚠️ No se encontró instancia para div_id '{div_id}'")
        
        except (KeyError, TypeError, AttributeError) as e:
            # Errores esperados al procesar mensajes
            logger.warning(f"⚠️ [CommManager] Error procesando mensaje para div_id '{div_id}': {e}")
        except Exception as e:
            # Error inesperado - registrar y re-raise
            logger.error(f"❌ [CommManager] Error inesperado procesando mensaje para div_id '{div_id}': {e}", exc_info=True)
            raise
    
    @classmethod
    def get_status(cls) -> dict:
        """
        Retorna el estado actual del sistema de comunicación.
        
        Returns:
            dict: Diccionario con información del estado del sistema
        
        Raises:
            RuntimeError: Si hay error accediendo al estado
        """
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


def get_comm_engine() -> type:
    """
    Obtiene el engine de comunicación apropiado según el entorno.
    
    Esta función será extendida para soportar múltiples entornos.
    Por ahora retorna CommManager para Jupyter.
    
    Returns:
        type: Clase del engine de comunicación (CommManager)
    
    Raises:
        RuntimeError: Si no hay engine disponible
    
    Returns:
        CommManager: Engine de comunicación
    """
    # Por ahora solo soportamos Jupyter
    # En el futuro se detectará el entorno automáticamente
    return CommManager

