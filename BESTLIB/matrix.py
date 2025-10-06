import uuid
import json
import os
import weakref

class MatrixLayout:
    _map = {}
    _safe_html = True
    
    # Sistema de comunicación bidireccional (JS → Python)
    _instances = {}  # dict[str, weakref.ReferenceType[MatrixLayout]]
    _global_handlers = {}  # dict[str, callable]
    _comm_registered = False
    
    @classmethod
    def on_global(cls, event, func):
        """
        Registra un callback global para un tipo de evento.
        Se ejecuta si no hay handler específico en la instancia.
        
        Args:
            event (str): Nombre del evento (ej: 'select', 'click', 'brush')
            func (callable): Función callback que recibe (payload)
        """
        cls._global_handlers[event] = func
    
    @classmethod
    def _ensure_comm_target(cls):
        """
        Registra el comm target de Jupyter para recibir eventos desde JS.
        Solo se ejecuta una vez por sesión.
        """
        if cls._comm_registered:
            return
        
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if not ip or not hasattr(ip, "kernel"):
                return
            
            km = ip.kernel.comm_manager
            
            def _target(comm, open_msg):
                @comm.on_msg
                def _recv(msg):
                    try:
                        data = msg["content"]["data"]
                        div_id = data.get("div_id")
                        event_type = data.get("type")
                        payload = data.get("payload")
                        
                        # Buscar instancia por div_id
                        inst_ref = cls._instances.get(div_id)
                        inst = inst_ref() if inst_ref else None
                        
                        # Buscar handler: primero en instancia, luego global
                        handler = None
                        if inst and hasattr(inst, "_handlers"):
                            handler = inst._handlers.get(event_type)
                        if not handler:
                            handler = cls._global_handlers.get(event_type)
                        
                        # Ejecutar callback
                        if handler:
                            handler(payload)
                    except Exception as e:
                        print(f"[MatrixLayout] Error en handler: {e}")
            
            km.register_target("bestlib_matrix", _target)
            cls._comm_registered = True
        except Exception as e:
            print(f"[MatrixLayout] No se pudo registrar comm: {e}")
    
    def on(self, event, func):
        """
        Registra un callback específico para esta instancia.
        
        Args:
            event (str): Nombre del evento (ej: 'select', 'click', 'brush')
            func (callable): Función callback que recibe (payload)
        
        Example:
            layout = MatrixLayout("AAA\\nBBB")
            layout.on('select', lambda data: print(f"Seleccionado: {data}"))
        """
        if not hasattr(self, "_handlers"):
            self._handlers = {}
        self._handlers[event] = func
        return self  # Para encadenar: layout.on(...).on(...)

    @classmethod
    def map(cls, mapping):
        cls._map = mapping

    @classmethod
    def set_safe_html(cls, safe: bool):
        cls._safe_html = bool(safe)

    def __init__(self, ascii_layout):
        self.ascii_layout = ascii_layout
        self.div_id = "matrix-" + str(uuid.uuid4())
        
        # Registrar instancia para recibir eventos
        MatrixLayout._instances[self.div_id] = weakref.ref(self)
        self._handlers = {}

    def _repr_html_(self):
        # Cargar JS y CSS desde el mismo paquete
        js_path = os.path.join(os.path.dirname(__file__), "matrix.js")
        css_path = os.path.join(os.path.dirname(__file__), "style.css")

        with open(js_path, "r", encoding="utf-8") as f:
            js_code = f.read()

        with open(css_path, "r", encoding="utf-8") as f:
            css_code = f.read()

        # Validar layout ASCII: mismas columnas por fila
        rows = [r for r in self.ascii_layout.strip().split("\n") if r]
        if not rows:
            raise ValueError("ascii_layout no puede estar vacío")
        col_len = len(rows[0])
        if any(len(r) != col_len for r in rows):
            raise ValueError("Todas las filas del ascii_layout deben tener igual longitud")

        # Escapar backticks para no romper el template literal JS
        escaped_layout = self.ascii_layout.replace("`", "\\`")

        # Pasar metadata al JS
        meta = {
            "__safe_html__": bool(self._safe_html),
            "__div_id__": self.div_id
        }
        mapping_js = json.dumps({**self._map, **meta})

        # Render HTML con contenedor + CSS + JS inline (compatible con Notebook clásico)
        html = f"""
        <style>{css_code}</style>
        <div id="{self.div_id}" class="matrix-layout"></div>
        <script>
        {js_code}
        render("{self.div_id}", `{escaped_layout}`, {mapping_js});
        </script>
        """
        return html

    def _repr_mimebundle_(self, include=None, exclude=None):
        # Asegurar que el comm target está registrado
        MatrixLayout._ensure_comm_target()
        
        # Cargar JS y CSS desde el mismo paquete
        js_path = os.path.join(os.path.dirname(__file__), "matrix.js")
        css_path = os.path.join(os.path.dirname(__file__), "style.css")

        with open(js_path, "r", encoding="utf-8") as f:
            js_code = f.read()

        with open(css_path, "r", encoding="utf-8") as f:
            css_code = f.read()

        rows = [r for r in self.ascii_layout.strip().split("\n") if r]
        if not rows:
            raise ValueError("ascii_layout no puede estar vacío")
        col_len = len(rows[0])
        if any(len(r) != col_len for r in rows):
            raise ValueError("Todas las filas del ascii_layout deben tener igual longitud")

        escaped_layout = self.ascii_layout.replace("`", "\\`")

        html = f"""
        <style>{css_code}</style>
        <div id="{self.div_id}" class="matrix-layout"></div>
        """
        
        # Pasar div_id y safe_html al JS
        meta = {
            "__safe_html__": bool(self._safe_html),
            "__div_id__": self.div_id
        }
        mapping_js = json.dumps({**self._map, **meta})

        js = (
            js_code
            + "\n"
            + f'render("{self.div_id}", `{escaped_layout}`, {mapping_js});'
        )

        return {
            "text/html": html,
            "application/javascript": js,
        }
    
    def display(self):
        """
        Método alternativo para mostrar el layout usando IPython.display.
        Útil cuando _repr_mimebundle_ no funciona correctamente en VS Code.
        """
        try:
            from IPython.display import display, HTML, Javascript
            
            # Cargar archivos
            js_path = os.path.join(os.path.dirname(__file__), "matrix.js")
            css_path = os.path.join(os.path.dirname(__file__), "style.css")
            
            with open(js_path, "r", encoding="utf-8") as f:
                js_code = f.read()
            
            with open(css_path, "r", encoding="utf-8") as f:
                css_code = f.read()
            
            # Validar layout
            rows = [r for r in self.ascii_layout.strip().split("\n") if r]
            if not rows:
                raise ValueError("ascii_layout no puede estar vacío")
            
            escaped_layout = self.ascii_layout.replace("`", "\\`")
            
            # Metadata
            meta = {
                "__safe_html__": bool(self._safe_html),
                "__div_id__": self.div_id
            }
            mapping_js = json.dumps({**self._map, **meta})
            
            # HTML con estilo y contenedor
            html_content = f"""
            <style>{css_code}</style>
            <div id="{self.div_id}" class="matrix-layout"></div>
            """
            
            # JavaScript con render
            js_content = f"""
            {js_code}
            render("{self.div_id}", `{escaped_layout}`, {mapping_js});
            """
            
            # Mostrar HTML primero, luego JS
            display(HTML(html_content))
            display(Javascript(js_content))
            
        except ImportError:
            print("⚠️ IPython no disponible. Usa en un notebook Jupyter.")
        except Exception as e:
            print(f"❌ Error al mostrar layout: {e}")
