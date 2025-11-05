import uuid
import json
import os
import weakref

try:
    import ipywidgets as widgets
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

class MatrixLayout:
    _map = {}
    _safe_html = True
    
    # Sistema de comunicación bidireccional (JS → Python)
    _instances = {}  # dict[str, weakref.ReferenceType[MatrixLayout]]
    _global_handlers = {}  # dict[str, callable]
    _comm_registered = False
    _debug = False  # Modo debug para ver mensajes detallados
    
    @staticmethod
    def _prepare_data(data, x_col=None, y_col=None, category_col=None, value_col=None):
        """
        Prepara datos para visualización, aceptando DataFrames de pandas o listas de diccionarios.
        
        Args:
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X (scatter plots)
            y_col: Nombre de columna para eje Y (scatter plots)
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (bar charts)
        
        Returns:
            tuple: (datos_procesados, datos_originales)
            - datos_procesados: Lista de diccionarios con formato estándar
            - datos_originales: Lista de diccionarios con todas las columnas originales
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            # Convertir DataFrame a lista de diccionarios
            original_data = data.to_dict('records')
            
            processed_data = []
            for idx, row in data.iterrows():
                item = {}
                
                # Mapear columnas según especificación
                if x_col and x_col in data.columns:
                    item['x'] = row[x_col]
                elif 'x' in row:
                    item['x'] = row['x']
                
                if y_col and y_col in data.columns:
                    item['y'] = row[y_col]
                elif 'y' in row:
                    item['y'] = row['y']
                
                if category_col and category_col in data.columns:
                    item['category'] = row[category_col]
                elif 'category' in row:
                    item['category'] = row['category']
                
                if value_col and value_col in data.columns:
                    item['value'] = row[value_col]
                elif 'value' in row:
                    item['value'] = row['value']
                
                # Guardar referencia a la fila original completa
                item['_original_row'] = original_data[idx]
                item['_original_index'] = int(idx)
                
                processed_data.append(item)
            
            return processed_data, original_data
        else:
            # Si ya es lista de diccionarios, solo agregar referencias
            if isinstance(data, list):
                processed_data = []
                for idx, item in enumerate(data):
                    processed_item = item.copy()
                    # Asegurar que existe _original_row
                    if '_original_row' not in processed_item:
                        processed_item['_original_row'] = item
                    if '_original_index' not in processed_item:
                        processed_item['_original_index'] = idx
                    processed_data.append(processed_item)
                return processed_data, data
            else:
                raise ValueError("Los datos deben ser un DataFrame de pandas o una lista de diccionarios")
    
    @classmethod
    def set_debug(cls, enabled: bool):
        """Activa/desactiva mensajes de debug."""
        cls._debug = enabled
    
    @classmethod
    def on_global(cls, event, func):
        """Registra un callback global para un tipo de evento."""
        cls._global_handlers[event] = func
    
    @classmethod
    def register_comm(cls, force=False):
        """
        Registra manualmente el comm target de Jupyter.
        Útil para forzar el registro o verificar que funciona.
        
        Args:
            force (bool): Si True, fuerza el re-registro incluso si ya está registrado
        
        Returns:
            bool: True si el registro fue exitoso, False si falló
        """
        if cls._comm_registered and not force:
            if cls._debug:
                print("ℹ️ [MatrixLayout] Comm ya estaba registrado")
            return True
        
        if force:
            cls._comm_registered = False
        
        return cls._ensure_comm_target()
    
    @classmethod
    def _ensure_comm_target(cls):
        """
        Registra el comm target de Jupyter para recibir eventos desde JS.
        Solo se ejecuta una vez por sesión.
        
        Returns:
            bool: True si el registro fue exitoso, False si falló
        """
        if cls._comm_registered:
            return True
        
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if not ip or not hasattr(ip, "kernel"):
                if cls._debug:
                    print("⚠️ [MatrixLayout] No hay kernel de IPython disponible")
                return False
            
            km = ip.kernel.comm_manager
            
            def _target(comm, open_msg):
                """Handler del comm target que procesa mensajes desde JS"""
                div_id = open_msg['content']['data'].get('div_id', 'unknown')
                
                if cls._debug:
                    print(f"🔗 [MatrixLayout] Comm abierto para div_id: {div_id}")
                
                @comm.on_msg
                def _recv(msg):
                    try:
                        data = msg["content"]["data"]
                        div_id = data.get("div_id")
                        event_type = data.get("type")
                        payload = data.get("payload")
                        
                        if cls._debug:
                            print(f"📩 [MatrixLayout] Evento recibido:")
                            print(f"   - Tipo: {event_type}")
                            print(f"   - Div ID: {div_id}")
                            print(f"   - Payload: {payload}")
                        
                        # Buscar instancia por div_id
                        inst_ref = cls._instances.get(div_id)
                        inst = inst_ref() if inst_ref else None
                        
                        # Buscar handler: primero en instancia, luego global
                        handler = None
                        if inst and hasattr(inst, "_handlers"):
                            handler = inst._handlers.get(event_type)
                            if handler and cls._debug:
                                print(f"   ✓ Usando handler de instancia")
                        
                        if not handler:
                            handler = cls._global_handlers.get(event_type)
                            if handler and cls._debug:
                                print(f"   ✓ Usando handler global")
                        
                        # Ejecutar callback
                        if handler:
                            handler(payload)
                        else:
                            if cls._debug:
                                print(f"   ⚠️ No hay handler registrado para '{event_type}'")
                    
                    except Exception as e:
                        print(f"❌ [MatrixLayout] Error en handler: {e}")
                        if cls._debug:
                            import traceback
                            traceback.print_exc()
            
            km.register_target("bestlib_matrix", _target)
            cls._comm_registered = True
            
            if cls._debug:
                print("✅ [MatrixLayout] Comm target 'bestlib_matrix' registrado exitosamente")
            
            return True
            
        except Exception as e:
            print(f"❌ [MatrixLayout] No se pudo registrar comm: {e}")
            if cls._debug:
                import traceback
                traceback.print_exc()
            return False
    
    def on(self, event, func):
        """Registra un callback específico para esta instancia."""
        if not hasattr(self, "_handlers"):
            self._handlers = {}
        self._handlers[event] = func
        return self

    @classmethod
    def map(cls, mapping):
        cls._map = mapping
    
    @classmethod
    def map_scatter(cls, letter, data, x_col=None, y_col=None, category_col=None, **kwargs):
        """
        Método helper para crear scatter plot desde DataFrame de pandas.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            category_col: Nombre de columna para categorías (opcional)
            **kwargs: Argumentos adicionales (colorMap, pointRadius, interactive, axes, etc.)
        
        Returns:
            dict: Especificación del scatter plot para usar en map()
        
        Ejemplo:
            import pandas as pd
            df = pd.DataFrame({'edad': [20, 30, 40], 'salario': [5000, 8000, 12000], 'dept': ['A', 'B', 'A']})
            
            MatrixLayout.map_scatter('S', df, x_col='edad', y_col='salario', category_col='dept', interactive=True)
            layout = MatrixLayout("S")
        """
        processed_data, original_data = cls._prepare_data(data, x_col=x_col, y_col=y_col, category_col=category_col)
        
        spec = {
            'type': 'scatter',
            'data': processed_data,
            **kwargs
        }
        
        # Actualizar el mapping
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        
        return spec
    
    @classmethod
    def map_barchart(cls, letter, data, category_col=None, value_col=None, **kwargs):
        """
        Método helper para crear bar chart desde DataFrame de pandas.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional, si no se especifica cuenta)
            **kwargs: Argumentos adicionales (color, colorMap, interactive, axes, etc.)
        
        Returns:
            dict: Especificación del bar chart para usar en map()
        
        Ejemplo:
            import pandas as pd
            df = pd.DataFrame({'dept': ['A', 'B', 'C'], 'ventas': [100, 200, 150]})
            
            MatrixLayout.map_barchart('B', df, category_col='dept', value_col='ventas', interactive=True)
            layout = MatrixLayout("B")
        """
        from collections import Counter
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            # Si hay value_col, agrupar y sumar
            if value_col and value_col in data.columns:
                bar_data = data.groupby(category_col)[value_col].sum().reset_index()
                bar_data = bar_data.rename(columns={category_col: 'category', value_col: 'value'})
                bar_data = bar_data.to_dict('records')
            elif category_col and category_col in data.columns:
                # Contar por categoría
                counts = data[category_col].value_counts()
                bar_data = [{'category': cat, 'value': count} for cat, count in counts.items()]
            else:
                raise ValueError("Debe especificar category_col")
            
            # Agregar datos originales para referencia
            original_data = data.to_dict('records')
            for i, bar_item in enumerate(bar_data):
                # Encontrar todas las filas con esta categoría
                matching_rows = [row for row in original_data if row.get(category_col) == bar_item['category']]
                bar_item['_original_rows'] = matching_rows
        else:
            # Lista de diccionarios
            if category_col:
                categories = Counter([item.get(category_col, 'unknown') for item in data])
                bar_data = [{'category': cat, 'value': count} for cat, count in categories.items()]
            else:
                categories = Counter([item.get('category', 'unknown') for item in data])
                bar_data = [{'category': cat, 'value': count} for cat, count in categories.items()]
            
            # Agregar datos originales
            original_data = data if isinstance(data, list) else []
            for bar_item in bar_data:
                matching_rows = [row for row in original_data if row.get(category_col or 'category') == bar_item['category']]
                bar_item['_original_rows'] = matching_rows
        
        spec = {
            'type': 'bar',
            'data': bar_data,
            **kwargs
        }
        
        # Actualizar el mapping
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        
        return spec

    @classmethod
    def set_safe_html(cls, safe: bool):
        cls._safe_html = bool(safe)
    
    @classmethod
    def get_status(cls):
        """Retorna el estado actual del sistema de comunicación."""
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
            "global_handlers": list(cls._global_handlers.keys()),
        }

    def __init__(self, ascii_layout=None):
        """
        Crea una nueva instancia de MatrixLayout.
        
        Args:
            ascii_layout (str, optional): Layout ASCII. Si no se proporciona, se genera uno simple.
        """
        # Si no se proporciona layout, crear uno simple
        if ascii_layout is None:
            ascii_layout = "A"
        
        self.ascii_layout = ascii_layout
        self.div_id = "matrix-" + str(uuid.uuid4())
        MatrixLayout._instances[self.div_id] = weakref.ref(self)
        self._handlers = {}
        self._reactive_model = None  # Para modelo reactivo
        
        # Asegurar que el comm esté registrado
        MatrixLayout._ensure_comm_target()
    
    def connect_selection(self, reactive_model):
        """
        Conecta un modelo reactivo para actualizar automáticamente.
        
        Args:
            reactive_model: Instancia de ReactiveData o SelectionModel
        
        Ejemplo:
            from BESTLIB.reactive import SelectionModel
            
            selection = SelectionModel()
            selection.on_change(lambda items, count: print(f"{count} seleccionados"))
            
            layout = MatrixLayout("S")
            layout.connect_selection(selection)
            layout.display()
        """
        if not HAS_WIDGETS:
            print("⚠️ ipywidgets no está instalado. Instala con: pip install ipywidgets")
            return
        
        self._reactive_model = reactive_model
        
        # Crear handler que actualiza el modelo reactivo
        def update_model(payload):
            items = payload.get('items', [])
            # Extraer filas originales completas si existen
            original_rows = []
            for item in items:
                if '_original_row' in item:
                    original_rows.append(item['_original_row'])
                else:
                    # Si no hay _original_row, usar el item completo
                    original_rows.append(item)
            reactive_model.update(original_rows)
        
        # Registrar el handler
        self.on('select', update_model)
        
        return self
    
    def __del__(self):
        """Limpia la referencia cuando se destruye la instancia"""
        if hasattr(self, 'div_id') and self.div_id in MatrixLayout._instances:
            del MatrixLayout._instances[self.div_id]

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
    
    def display(self, ascii_layout=None):
        """
        Muestra el layout usando IPython.display.
        
        Args:
            ascii_layout (str, optional): Layout ASCII a usar. Si no se proporciona, usa self.ascii_layout.
        """
        try:
            from IPython.display import display, HTML, Javascript
            
            MatrixLayout._ensure_comm_target()
            
            # Usar el layout proporcionado o el de la instancia
            layout_to_use = ascii_layout if ascii_layout is not None else self.ascii_layout
            
            js_path = os.path.join(os.path.dirname(__file__), "matrix.js")
            css_path = os.path.join(os.path.dirname(__file__), "style.css")
            
            with open(js_path, "r", encoding="utf-8") as f:
                js_code = f.read()
            
            with open(css_path, "r", encoding="utf-8") as f:
                css_code = f.read()
            
            rows = [r for r in layout_to_use.strip().split("\n") if r]
            if not rows:
                raise ValueError("ascii_layout no puede estar vacío")
            
            escaped_layout = layout_to_use.replace("`", "\\`")
            
            meta = {
                "__safe_html__": bool(self._safe_html),
                "__div_id__": self.div_id
            }
            mapping_js = json.dumps({**self._map, **meta})
            
            html_content = f"""
            <style>{css_code}</style>
            <div id="{self.div_id}" class="matrix-layout"></div>
            """
            
            js_content = f"""
            (function() {{
                function ensureD3() {{
                    if (window.d3) return Promise.resolve(window.d3);
                    
                    return new Promise((resolve, reject) => {{
                        const script = document.createElement('script');
                        script.src = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';
                        script.onload = () => {{
                            if (window.d3) resolve(window.d3);
                            else reject(new Error('D3 no se cargó'));
                        }};
                        script.onerror = () => reject(new Error('Error al cargar D3'));
                        document.head.appendChild(script);
                    }});
                }}
                
                ensureD3().then(d3 => {{
                    {js_code}
                    render("{self.div_id}", `{escaped_layout}`, {mapping_js});
                }}).catch(e => {{
                    const errorDiv = document.getElementById("{self.div_id}");
                    if (errorDiv) {{
                        errorDiv.innerHTML = '<div style="color: #e74c3c; padding: 20px; border: 2px solid #e74c3c; border-radius: 5px;">' +
                            '<strong>❌ Error:</strong> ' + e.message + '</div>';
                    }}
                }});
            }})();
            """
            
            display(HTML(html_content))
            display(Javascript(js_content))
            
        except Exception as e:
            print(f"❌ Error: {e}")
