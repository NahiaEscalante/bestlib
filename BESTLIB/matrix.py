import uuid
import json
import os

class MatrixLayout:
    _map = {}
    _safe_html = True

    @classmethod
    def map(cls, mapping):
        cls._map = mapping

    @classmethod
    def set_safe_html(cls, safe: bool):
        cls._safe_html = bool(safe)

    def __init__(self, ascii_layout):
        self.ascii_layout = ascii_layout
        self.div_id = "matrix-" + str(uuid.uuid4())

    def _repr_html_(self):
        # Cargar JS y CSS desde el mismo p aquete
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

        # Render HTML con contenedor + CSS + JS inline (compatible con Notebook clásico)
        html = f"""
        <style>{css_code}</style>
        <div id="{self.div_id}" class="matrix-layout"></div>
        <script>
        {js_code}
        render("{self.div_id}", `{escaped_layout}`, {{...{json.dumps(self._map)}, __safe_html__: {str(self._safe_html).lower()}}});
        </script>
        """
        return html

    def _repr_mimebundle_(self, include=None, exclude=None):
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

        js = (
            js_code
            + "\n"
            + f"render(\"{self.div_id}\", `{escaped_layout}`, {{...{json.dumps(self._map)}, __safe_html__: {str(self._safe_html).lower()}}});"
        )

        return {
            "text/html": html,
            "application/javascript": js,
        }
