"""
Google Colab Engine - Engine para Google Colab
"""
from .base import CommEngineBase


class ColabEngine(CommEngineBase):
    """
    Engine de comunicación para Google Colab usando google.colab API.
    """
    
    @property
    def engine_type(self):
        return 'colab'
    
    def is_available(self):
        """Verifica si estamos en Google Colab"""
        try:
            # En Colab, google.colab está disponible globalmente
            # Verificamos en el contexto JS, no Python
            # Por ahora retornamos False desde Python
            # La detección real se hace en JS
            return False  # Se detecta desde JS
        except Exception:
            return False
    
    def register_comm(self, comm_target="bestlib_matrix"):
        """
        En Colab, los comms se crean desde JavaScript.
        
        Args:
            comm_target (str): Nombre del comm target
        
        Returns:
            bool: True (asumimos que funciona desde JS)
        """
        # En Colab, el registro se hace desde JS
        return True
    
    def send_event(self, div_id, event_type, payload):
        """
        Los eventos se envían desde JS usando google.colab API.
        """
        pass
    
    def get_js_code(self):
        """
        Retorna código JS para crear Comm en Colab.
        
        Returns:
            str: Código JavaScript
        """
        return """
        function getComm(divId, maxRetries = 3) {
            if (!global._bestlibComms) {
                global._bestlibComms = {};
            }
            
            if (global._bestlibComms[divId]) {
                const cachedComm = global._bestlibComms[divId];
                if (cachedComm instanceof Promise) {
                    return cachedComm;
                }
                if (cachedComm && typeof cachedComm.send === 'function') {
                    return cachedComm;
                }
                delete global._bestlibComms[divId];
            }
            
            // Intentar con Google Colab
            if (global.google && global.google.colab && global.google.colab.kernel) {
                const commPromise = global.google.colab.kernel.comms.open("bestlib_matrix", { div_id: divId });
                
                global._bestlibComms[divId] = commPromise;
                
                commPromise.then((comm) => {
                    global._bestlibComms[divId] = comm;
                    comm.onMsg.addListener((msg) => {
                        // Manejar mensajes recibidos desde Python
                        const data = msg.data;
                        if (data && data.type && data.payload) {
                            // Procesar mensaje
                            console.log('[BESTLIB] Mensaje recibido desde Python:', data);
                        }
                    });
                }).catch((error) => {
                    console.warn('[BESTLIB] Error al abrir comm en Colab:', error);
                    delete global._bestlibComms[divId];
                });
                
                return commPromise;
            }
            
            return null;
        }
        
        function sendEvent(divId, type, payload) {
            const commPromise = getComm(divId);
            if (commPromise) {
                commPromise.then((comm) => {
                    comm.send({ 
                        type: type, 
                        div_id: divId, 
                        payload: payload 
                    });
                }).catch((error) => {
                    console.warn('[BESTLIB] Error al enviar evento:', error);
                });
            }
        }
        """

