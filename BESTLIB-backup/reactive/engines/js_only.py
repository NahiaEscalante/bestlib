"""
JS-Only Fallback - Engine para entornos sin comunicación con Python
"""
from .base import CommEngineBase


class JSOnlyFallback(CommEngineBase):
    """
    Engine de fallback para entornos sin comunicación bidireccional.
    Proporciona interactividad local en JavaScript únicamente.
    """
    
    @property
    def engine_type(self):
        return 'js-only'
    
    def is_available(self):
        """Siempre disponible como fallback"""
        return True
    
    def register_comm(self, comm_target="bestlib_matrix"):
        """
        No hace nada en modo JS-only.
        
        Args:
            comm_target (str): Nombre del comm target (ignorado)
        
        Returns:
            bool: True (siempre disponible como fallback)
        """
        return True
    
    def send_event(self, div_id, event_type, payload):
        """
        En modo JS-only, los eventos solo se manejan localmente.
        Se pueden registrar callbacks en JS pero no se envían a Python.
        """
        pass
    
    def get_js_code(self):
        """
        Retorna código JS para modo JS-only (sin comunicación con Python).
        
        Returns:
            str: Código JavaScript
        """
        return """
        // Modo JS-only: eventos locales sin comunicación con Python
        global._bestlibLocalHandlers = global._bestlibLocalHandlers || {};
        
        function registerLocalHandler(divId, eventType, handler) {
            const key = divId + ':' + eventType;
            if (!global._bestlibLocalHandlers[key]) {
                global._bestlibLocalHandlers[key] = [];
            }
            global._bestlibLocalHandlers[key].push(handler);
        }
        
        function emitLocalEvent(divId, eventType, payload) {
            const key = divId + ':' + eventType;
            const handlers = global._bestlibLocalHandlers[key] || [];
            handlers.forEach(handler => {
                try {
                    handler(payload);
                } catch (e) {
                    console.error('[BESTLIB] Error en handler local:', e);
                }
            });
        }
        
        function sendEvent(divId, type, payload) {
            // En modo JS-only, solo emitimos localmente
            emitLocalEvent(divId, type, payload);
            console.log('[BESTLIB] Evento local (sin Python):', type, payload);
        }
        
        function getComm(divId) {
            // En modo JS-only, no hay comm real
            return null;
        }
        """

