"""
Jupyter Comm Engine - Engine para Jupyter Notebook/JupyterLab
"""
from .base import CommEngineBase
from ...core.comm import CommManager


class JupyterCommEngine(CommEngineBase):
    """
    Engine de comunicación para Jupyter usando Comm targets.
    Soporta Jupyter Notebook clásico y JupyterLab.
    """
    
    @property
    def engine_type(self):
        return 'jupyter'
    
    def is_available(self):
        """Verifica si estamos en Jupyter"""
        try:
            from IPython import get_ipython
            ip = get_ipython()
            return ip is not None and hasattr(ip, "kernel")
        except Exception:
            return False
    
    def register_comm(self, comm_target="bestlib_matrix"):
        """
        Registra el comm target usando CommManager.
        
        Args:
            comm_target (str): Nombre del comm target
        
        Returns:
            bool: True si el registro fue exitoso
        """
        return CommManager.register_comm()
    
    def send_event(self, div_id, event_type, payload):
        """
        Los eventos se envían desde JS usando el Comm registrado.
        Esta función es principalmente para referencia.
        """
        # En Jupyter, los eventos se envían desde JS directamente
        # usando el Comm creado automáticamente
        pass
    
    def get_js_code(self):
        """
        Retorna código JS para crear Comm en Jupyter.
        
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
            
            function createComm(attempt = 1) {
                try {
                    const J = global.Jupyter;
                    if (J && J.notebook && J.notebook.kernel) {
                        try {
                            const comm = J.notebook.kernel.comm_manager.new_comm("bestlib_matrix", { div_id: divId });
                            global._bestlibComms[divId] = comm;
                            return comm;
                        } catch (e) {
                            if (attempt < maxRetries) {
                                console.warn(`Intento ${attempt} fallido, reintentando...`);
                                setTimeout(() => createComm(attempt + 1), 100 * attempt);
                                return null;
                            }
                            throw e;
                        }
                    }
                    return null;
                } catch (e) {
                    console.warn('[BESTLIB] No se pudo crear comm:', e);
                    return null;
                }
            }
            
            const comm = createComm();
            if (comm) {
                global._bestlibComms[divId] = comm;
            }
            return comm;
        }
        
        function sendEvent(divId, type, payload) {
            const comm = getComm(divId);
            if (comm) {
                comm.send({ 
                    type: type, 
                    div_id: divId, 
                    payload: payload 
                });
            }
        }
        """

