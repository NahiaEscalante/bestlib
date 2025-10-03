from IPython.display import display, HTML
import uuid
import json
import os

class MatrixLayout:
    _map = {}

    @classmethod
    def map(cls, mapping):
        cls._map = mapping

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

        # Render HTML con contenedor + CSS + JS inline
        html = f"""
        <style>{css_code}</style>
        <div id="{self.div_id}" class="matrix-layout"></div>
        <script>
        {js_code}
        render("{self.div_id}", `{self.ascii_layout}`, {json.dumps(self._map)});
        </script>
        """
        return html
