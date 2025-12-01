"""
Asset Manager - Gestión de assets JS y CSS
"""
import os
import sys
from pathlib import Path


class AssetManager:
    """
    Gestor de assets (JS/CSS) con caching.
    """
    
    _js_cache = None
    _css_cache = None
    _d3_cache = None
    
    @classmethod
    def get_base_path(cls):
        """Retorna la ruta base del paquete BESTLIB"""
        return Path(__file__).parent.parent
    
    @classmethod
    def load_js(cls, force_reload=False):
        """
        Carga y cachea el archivo matrix.js.
        
        Args:
            force_reload (bool): Si True, fuerza recarga del cache
        
        Returns:
            str: Contenido del archivo JS
        """
        if cls._js_cache is None or force_reload:
            js_path = cls.get_base_path() / "matrix.js"
            if js_path.exists():
                with open(js_path, "r", encoding="utf-8") as f:
                    cls._js_cache = f.read()
            else:
                cls._js_cache = ""
        
        return cls._js_cache
    
    @classmethod
    def load_css(cls, force_reload=False):
        """
        Carga y cachea el archivo style.css.
        
        Args:
            force_reload (bool): Si True, fuerza recarga del cache
        
        Returns:
            str: Contenido del archivo CSS
        """
        if cls._css_cache is None or force_reload:
            css_path = cls.get_base_path() / "style.css"
            if css_path.exists():
                with open(css_path, "r", encoding="utf-8") as f:
                    cls._css_cache = f.read()
            else:
                cls._css_cache = ""
        
        return cls._css_cache
    
    @classmethod
    def load_d3(cls, force_reload=False):
        """
        Carga y cachea el archivo d3.min.js.
        
        Args:
            force_reload (bool): Si True, fuerza recarga del cache
        
        Returns:
            str: Contenido del archivo D3.js
        """
        if cls._d3_cache is None or force_reload:
            d3_path = cls.get_base_path() / "d3.min.js"
            if d3_path.exists():
                with open(d3_path, "r", encoding="utf-8") as f:
                    cls._d3_cache = f.read()
            else:
                cls._d3_cache = ""
        
        return cls._d3_cache
    
    @classmethod
    def clear_cache(cls):
        """Limpia el cache de assets"""
        cls._js_cache = None
        cls._css_cache = None
        cls._d3_cache = None
    
    @classmethod
    def get_all_assets(cls):
        """
        Retorna todos los assets como diccionario.
        
        Returns:
            dict: {'js': str, 'css': str, 'd3': str}
        """
        return {
            'js': cls.load_js(),
            'css': cls.load_css(),
            'd3': cls.load_d3()
        }
    
    @classmethod
    def is_colab(cls):
        """
        Detecta si el código se está ejecutando en Google Colab.
        
        Returns:
            bool: True si está en Colab, False en caso contrario
        """
        return "google.colab" in sys.modules
    
    @classmethod
    def ensure_colab_assets_loaded(cls):
        """
        Carga automáticamente los assets (d3.min.js, style.css) en Google Colab.
        matrix.js se incluye directamente en el JS generado, no se carga por separado.
        
        Solo se ejecuta si está en Colab y si los assets no han sido cargados previamente.
        """
        if not cls.is_colab():
            return False
        
        try:
            from IPython.display import display, HTML, Javascript
            
            # Usar un flag de módulo para evitar cargar múltiples veces
            if not hasattr(cls, '_colab_assets_loaded'):
                cls._colab_assets_loaded = False
            
            if cls._colab_assets_loaded:
                return True
            
            # Cargar D3.js desde CDN si no está disponible
            load_d3_js = """
            (function() {
                // Verificar si D3 ya está cargado
                if (typeof d3 !== 'undefined') {
                    console.log('✅ [BESTLIB] D3.js ya está cargado');
                    return;
                }
                
                // Verificar si ya hay un script de D3 cargándose
                var existingScript = document.querySelector('script[src*="d3"]');
                if (existingScript) {
                    console.log('✅ [BESTLIB] D3.js ya se está cargando');
                    return;
                }
                
                // Cargar D3 desde CDN
                var script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';
                script.async = true;
                script.onload = function() {
                    console.log('✅ [BESTLIB] D3.js cargado desde CDN');
                };
                script.onerror = function() {
                    console.warn('⚠️ [BESTLIB] Error al cargar D3.js desde CDN primario, intentando alternativo');
                    // Intentar CDN alternativo
                    script.src = 'https://unpkg.com/d3@7/dist/d3.min.js';
                    script.onload = function() {
                        console.log('✅ [BESTLIB] D3.js cargado desde CDN alternativo');
                    };
                };
                document.head.appendChild(script);
            })();
            """
            display(Javascript(load_d3_js))
            
            # Cargar style.css (solo si no está ya cargado)
            css_content = cls.load_css()
            if css_content:
                # Verificar si ya existe antes de insertar
                css_check_js = """
                (function() {
                    if (document.getElementById('bestlib-style')) {
                        return; // Ya está cargado
                    }
                })();
                """
                display(Javascript(css_check_js))
                display(HTML(f"<style id='bestlib-style'>{css_content}</style>"))
            
            # Marcar como cargado
            cls._colab_assets_loaded = True
            
            return True
            
        except ImportError:
            # IPython no disponible, no podemos cargar assets
            return False
        except Exception as e:
            # Error al cargar assets, pero no fallar silenciosamente
            print(f"⚠️ [BESTLIB] Error al cargar assets para Colab: {e}")
            return False

