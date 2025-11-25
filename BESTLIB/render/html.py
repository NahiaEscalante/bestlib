"""
HTML Generator - Generador de HTML para BESTLIB
"""
from typing import Optional
import html as html_module
from ..utils.json import sanitize_for_json
import json


class HTMLGenerator:
    """
    Generador de HTML para layouts y gráficos de BESTLIB.
    """
    
    @staticmethod
    def generate_container(div_id: str, inline_style: str = "") -> str:
        """
        Genera el contenedor HTML para un layout.
        
        Args:
            div_id (str): ID del contenedor
            inline_style (str): Estilos inline opcionales
        
        Returns:
            str: HTML del contenedor
        
        Raises:
            ValueError: Si div_id no es str no vacío
        """
        if not isinstance(div_id, str) or not div_id:
            raise ValueError(f"div_id debe ser str no vacío, recibido: {div_id!r}")
        
        # Escapar div_id para prevenir XSS
        safe_div_id = html_module.escape(div_id)
        
        if inline_style:
            return f'<div id="{safe_div_id}" class="matrix-layout" {inline_style}></div>'
        else:
            return f'<div id="{safe_div_id}" class="matrix-layout"></div>'
    
    @staticmethod
    def generate_style_tag(css_code: str) -> str:
        """
        Genera el tag <style> con CSS.
        
        Args:
            css_code (str): Código CSS
        
        Returns:
            str: Tag <style>
        """
        return f"<style>{css_code}</style>"
    
    @staticmethod
    def generate_script_tag(js_code: str) -> str:
        """
        Genera el tag <script> con JavaScript.
        
        Args:
            js_code (str): Código JavaScript
        
        Returns:
            str: Tag <script>
        """
        return f"<script>{js_code}</script>"
    
    @staticmethod
    def generate_full_html(div_id: str, css_code: str, js_code: str, inline_style: str = "") -> str:
        """
        Genera HTML completo con CSS y JS.
        
        Args:
            div_id (str): ID del contenedor
            css_code (str): Código CSS
            js_code (str): Código JavaScript
            inline_style (str): Estilos inline opcionales
        
        Returns:
            str: HTML completo
        
        Raises:
            ValueError: Si div_id no es str no vacío
        """
        # Wrapper seguro para cargar D3.js ANTES del código principal
        d3_loader = """<script>
(function() {
    // Cargar D3.js solo si no está disponible
    if (typeof window.d3 === 'undefined') {
        var script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';
        script.async = false; // Cargar de forma síncrona para asegurar disponibilidad
        script.crossOrigin = 'anonymous';
        script.onerror = function() {
            // Fallback a CDN alternativo
            script.src = 'https://unpkg.com/d3@7/dist/d3.min.js';
            document.head.appendChild(script);
        };
        document.head.appendChild(script);
    }
})();
</script>"""
        
        style_tag = HTMLGenerator.generate_style_tag(css_code)
        container = HTMLGenerator.generate_container(div_id, inline_style)
        script_tag = HTMLGenerator.generate_script_tag(js_code)
        
        return f"{d3_loader}\n{style_tag}\n{container}\n{script_tag}"
    
    @staticmethod
    def escape_js_string(s: Any) -> str:
        """
        Escapa una cadena para uso en JavaScript.
        
        Args:
            s: Cadena o valor a escapar
        
        Returns:
            str: Cadena escapada (o "null" si s es None)
        """
        if s is None:
            return "null"
        if not isinstance(s, (str, int, float, bool)):
            s = str(s)
        # Escapar backticks para template literals
        s = str(s).replace("`", "\\`").replace("$", "\\$")
        return s
    
    @staticmethod
    def generate_mapping_js(mapping: dict) -> str:
        """
        Genera código JavaScript para el mapping.
        
        Args:
            mapping (dict): Mapping de letras a specs
        
        Returns:
            str: Código JavaScript (JSON string)
        """
        sanitized = sanitize_for_json(mapping)
        return json.dumps(sanitized)

