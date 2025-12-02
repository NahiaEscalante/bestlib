"""
HTML Generator - Generador de HTML para BESTLIB
"""
from ..utils.json import sanitize_for_json
import json


class HTMLGenerator:
    """
    Generador de HTML para layouts y gráficos de BESTLIB.
    """
    
    @staticmethod
    def generate_container(div_id, inline_style="", theme_class=""):
        """
        Genera el contenedor HTML para un layout.
        
        Args:
            div_id (str): ID del contenedor
            inline_style (str): Estilos inline opcionales
            theme_class (str): Clase CSS del tema (ej: 'bestlib-theme-dark')
        
        Returns:
            str: HTML del contenedor
        """
        classes = "matrix-layout"
        if theme_class:
            classes += f" {theme_class}"
        
        if inline_style:
            return f'<div id="{div_id}" class="{classes}" {inline_style}></div>'
        else:
            return f'<div id="{div_id}" class="{classes}"></div>'
    
    @staticmethod
    def generate_style_tag(css_code):
        """
        Genera el tag <style> con CSS.
        
        Args:
            css_code (str): Código CSS
        
        Returns:
            str: Tag <style>
        """
        return f"<style>{css_code}</style>"
    
    @staticmethod
    def generate_script_tag(js_code):
        """
        Genera el tag <script> con JavaScript.
        
        Args:
            js_code (str): Código JavaScript
        
        Returns:
            str: Tag <script>
        """
        return f"<script>{js_code}</script>"
    
    @staticmethod
    def generate_full_html(div_id, css_code, js_code, inline_style="", theme_class=""):
        """
        Genera HTML completo con CSS y JS.
        
        Args:
            div_id (str): ID del contenedor
            css_code (str): Código CSS
            js_code (str): Código JavaScript
            inline_style (str): Estilos inline opcionales
            theme_class (str): Clase CSS del tema (ej: 'bestlib-theme-dark')
        
        Returns:
            str: HTML completo
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
        container = HTMLGenerator.generate_container(div_id, inline_style, theme_class)
        script_tag = HTMLGenerator.generate_script_tag(js_code)
        
        return f"{d3_loader}\n{style_tag}\n{container}\n{script_tag}"
    
    @staticmethod
    def escape_js_string(s):
        """
        Escapa una cadena para uso en JavaScript.
        
        Args:
            s (str): Cadena a escapar
        
        Returns:
            str: Cadena escapada
        """
        if s is None:
            return "null"
        # Escapar backticks para template literals
        s = str(s).replace("`", "\\`").replace("$", "\\$")
        return s
    
    @staticmethod
    def generate_mapping_js(mapping):
        """
        Genera código JavaScript para el mapping.
        
        Args:
            mapping (dict): Mapping de letras a specs
        
        Returns:
            str: Código JavaScript
        """
        sanitized = sanitize_for_json(mapping)
        return json.dumps(sanitized)

