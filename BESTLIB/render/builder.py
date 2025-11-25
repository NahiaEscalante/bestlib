"""
JS Builder - Constructor de código JavaScript modular
"""
from typing import Dict, Any
from ..utils.json import sanitize_for_json
import json


class JSBuilder:
    """
    Constructor de código JavaScript a partir de specs y templates.
    """
    
    @staticmethod
    def build_render_call(div_id: str, layout_ascii: str, mapping: Dict[str, Any], wait_for_d3: bool = False) -> str:
        """
        Construye la llamada a render() en JavaScript.
        
        Args:
            div_id (str): ID del contenedor
            layout_ascii (str): Layout ASCII
            mapping (dict): Mapping de letras a specs
            wait_for_d3 (bool): Si True, espera a que D3 esté disponible antes de renderizar
        
        Returns:
            str: Código JavaScript
        
        Raises:
            TypeError: Si los parámetros no son del tipo correcto
            ValueError: Si div_id no es str no vacío
        """
        if not isinstance(div_id, str) or not div_id:
            raise ValueError(f"div_id debe ser str no vacío, recibido: {div_id!r}")
        if not isinstance(layout_ascii, str):
            raise TypeError(f"layout_ascii debe ser str, recibido: {type(layout_ascii).__name__}")
        if not isinstance(mapping, dict):
            raise TypeError(f"mapping debe ser dict, recibido: {type(mapping).__name__}")
        
        # Escapar layout ASCII para template literal
        escaped_layout = layout_ascii.replace("`", "\\`").replace("$", "\\$")
        
        # Generar mapping como JSON
        mapping_js = json.dumps(sanitize_for_json(mapping))
        
        if wait_for_d3:
            # Versión que espera a D3 (para Colab)
            return f"""
(function() {{
  const mapping = {mapping_js};
  const container = document.getElementById("{div_id}");
  if (container) {{
    container.__mapping__ = mapping;
  }}
  
  // Timeout máximo: 10 segundos
  const maxWaitTime = 10000;
  const startTime = Date.now();
  
  // Función para esperar a D3 y luego renderizar
  function waitForD3AndRender() {{
    const elapsed = Date.now() - startTime;
    
    if (elapsed > maxWaitTime) {{
      console.error('❌ [BESTLIB] Timeout esperando D3.js. El gráfico no se renderizará.');
      if (container) {{
        container.innerHTML = '<div style="padding: 20px; color: red; border: 2px solid red; background: #ffeeee;">Error: No se pudo cargar D3.js. Por favor, recarga la página.</div>';
      }}
      return;
    }}
    
    if (typeof d3 !== 'undefined' && typeof render !== 'undefined') {{
      // D3 y render están disponibles, ejecutar render
      render("{div_id}", `{escaped_layout}`, mapping);
    }} else {{
      // Esperar 100ms y volver a intentar
      setTimeout(waitForD3AndRender, 100);
    }}
  }}
  
  // Intentar renderizar inmediatamente, o esperar si es necesario
  if (typeof d3 !== 'undefined' && typeof render !== 'undefined') {{
    render("{div_id}", `{escaped_layout}`, mapping);
  }} else {{
    waitForD3AndRender();
  }}
}})();
"""
        else:
            # Versión normal (para Jupyter)
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
    def build_full_js(js_lib_code: str, div_id: str, layout_ascii: str, mapping: Dict[str, Any], wait_for_d3: bool = False) -> str:
        """
        Construye código JavaScript completo incluyendo la librería.
        
        Args:
            js_lib_code (str): Código de la librería JS
            div_id (str): ID del contenedor
            layout_ascii (str): Layout ASCII
            mapping (dict): Mapping de letras a specs
            wait_for_d3 (bool): Si True, espera a que D3 esté disponible antes de renderizar
        
        Returns:
            str: Código JavaScript completo
        
        Raises:
            TypeError: Si los parámetros no son del tipo correcto
            ValueError: Si div_id no es str no vacío
        """
        render_call = JSBuilder.build_render_call(div_id, layout_ascii, mapping, wait_for_d3=wait_for_d3)
        return f"{js_lib_code}\n{render_call}"
    
    @staticmethod
    def build_comm_code(comm_engine_js: str) -> str:
        """
        Incluye código del engine de comunicación en el JS.
        
        Args:
            comm_engine_js (str): Código JS del engine de comunicación
        
        Returns:
            str: Código JavaScript con Comm
        """
        return f"{comm_engine_js}\n"
    
    @staticmethod
    def wrap_in_iife(js_code: str) -> str:
        """
        Envuelve código JS en IIFE (Immediately Invoked Function Expression).
        
        Args:
            js_code (str): Código JavaScript
        
        Returns:
            str: Código envuelto en IIFE
        """
        return f"(function() {{\n{js_code}\n}})();"

