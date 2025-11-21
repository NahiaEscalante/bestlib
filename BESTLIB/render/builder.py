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
    def build_render_call(div_id, layout_ascii, mapping, wait_for_d3=False):
        """
        Construye la llamada a render() en JavaScript.
        
        Args:
            div_id (str): ID del contenedor
            layout_ascii (str): Layout ASCII
            mapping (dict): Mapping de letras a specs
            wait_for_d3 (bool): Si True, espera a que D3 esté disponible antes de renderizar
        
        Returns:
            str: Código JavaScript
        """
        # Escapar layout ASCII para template literal
        escaped_layout = layout_ascii.replace("`", "\\`").replace("$", "\\$")
        
        # Generar mapping como JSON
        mapping_js = json.dumps(sanitize_for_json(mapping))
        
        if wait_for_d3:
            # Versión que espera a D3 y lo carga si no está disponible
            return f"""
(function() {{
  const mapping = {mapping_js};
  const container = document.getElementById("{div_id}");
  if (container) {{
    container.__mapping__ = mapping;
  }}
  
  // Función para cargar D3.js si no está disponible
  function loadD3IfNeeded() {{
    return new Promise((resolve, reject) => {{
      // Si D3 ya está disponible, resolver inmediatamente
      if (typeof d3 !== 'undefined') {{
        resolve();
        return;
      }}
      
      // Verificar si ya hay un script de D3 cargándose
      var existingScript = document.querySelector('script[src*="d3"]');
      if (existingScript) {{
        // Esperar a que el script existente se cargue
        existingScript.onload = function() {{
          if (typeof d3 !== 'undefined') {{
            resolve();
          }} else {{
            reject(new Error('D3 no se inicializó después de cargar'));
          }}
        }};
        existingScript.onerror = function() {{
          reject(new Error('Error al cargar script D3 existente'));
        }};
        return;
      }}
      
      // Cargar D3 desde CDN
      var script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';
      script.async = true;
      script.onload = function() {{
        if (typeof d3 !== 'undefined') {{
          console.log('✅ [BESTLIB] D3.js cargado desde CDN');
          resolve();
        }} else {{
          reject(new Error('D3 no se inicializó después de cargar'));
        }}
      }};
      script.onerror = function() {{
        console.warn('⚠️ [BESTLIB] Error al cargar D3.js desde CDN primario, intentando alternativo');
        // Intentar CDN alternativo
        script.src = 'https://unpkg.com/d3@7/dist/d3.min.js';
        script.onload = function() {{
          if (typeof d3 !== 'undefined') {{
            console.log('✅ [BESTLIB] D3.js cargado desde CDN alternativo');
            resolve();
          }} else {{
            reject(new Error('D3 no se inicializó después de cargar'));
          }}
        }};
        script.onerror = function() {{
          reject(new Error('No se pudo cargar D3.js desde ningún CDN'));
        }};
      }};
      document.head.appendChild(script);
    }});
  }}
  
  // Timeout máximo: 15 segundos
  const maxWaitTime = 15000;
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
      // Intentar cargar D3 si no está disponible
      if (typeof d3 === 'undefined') {{
        loadD3IfNeeded().then(function() {{
          // D3 cargado, esperar un poco más para que render esté disponible
          setTimeout(waitForD3AndRender, 100);
        }}).catch(function(error) {{
          console.error('❌ [BESTLIB] Error al cargar D3.js:', error);
          setTimeout(waitForD3AndRender, 100);
        }});
      }} else {{
        // Esperar 100ms y volver a intentar
        setTimeout(waitForD3AndRender, 100);
      }}
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
    def build_full_js(js_lib_code, div_id, layout_ascii, mapping, wait_for_d3=False):
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
        """
        render_call = JSBuilder.build_render_call(div_id, layout_ascii, mapping, wait_for_d3=wait_for_d3)
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

