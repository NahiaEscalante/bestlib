"""
JS Builder - Constructor de código JavaScript modular
"""
from ..utils.json import sanitize_for_json
import json


class JSBuilder:
    """
    Constructor de código JavaScript a partir de specs y templates.
    """
    
    @staticmethod
    def build_render_call(div_id, layout_ascii, mapping):
        """
        Construye la llamada a render() en JavaScript.
        
        Args:
            div_id (str): ID del contenedor
            layout_ascii (str): Layout ASCII
            mapping (dict): Mapping de letras a specs
        
        Returns:
            str: Código JavaScript
        """
        # Escapar layout ASCII para template literal
        escaped_layout = layout_ascii.replace("`", "\\`").replace("$", "\\$")
        
        # Generar mapping como JSON
        mapping_js = json.dumps(sanitize_for_json(mapping))
        
        return f"""
(function() {{
  const mapping = {mapping_js};
  const container = document.getElementById("{div_id}");
  if (container) {{
    container.__mapping__ = mapping;
  }}
  render("{div_id}", `{escaped_layout}`, mapping);
}})();
"""
    
    @staticmethod
    def build_full_js(js_lib_code, div_id, layout_ascii, mapping):
        """
        Construye código JavaScript completo incluyendo la librería.
        
        Args:
            js_lib_code (str): Código de la librería JS
            div_id (str): ID del contenedor
            layout_ascii (str): Layout ASCII
            mapping (dict): Mapping de letras a specs
        
        Returns:
            str: Código JavaScript completo
        """
        render_call = JSBuilder.build_render_call(div_id, layout_ascii, mapping)
        return f"{js_lib_code}\n{render_call}"
    
    @staticmethod
    def build_comm_code(comm_engine_js):
        """
        Incluye código del engine de comunicación en el JS.
        
        Args:
            comm_engine_js (str): Código JS del engine de comunicación
        
        Returns:
            str: Código JavaScript con Comm
        """
        return f"{comm_engine_js}\n"
    
    @staticmethod
    def wrap_in_iife(js_code):
        """
        Envuelve código JS en IIFE (Immediately Invoked Function Expression).
        
        Args:
            js_code (str): Código JavaScript
        
        Returns:
            str: Código envuelto en IIFE
        """
        return f"(function() {{\n{js_code}\n}})();"

