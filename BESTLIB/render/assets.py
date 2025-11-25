"""
Asset Manager - Gestión de assets JS y CSS
"""
import os
import sys
from pathlib import Path
from typing import Optional


class AssetManager:
    """
    Gestor de assets (JS/CSS) con caching.
    """
    
    _js_cache = None
    _css_cache = None
    _d3_cache = None
    
    @classmethod
    def get_base_path(cls) -> Path:
        """Retorna la ruta base del paquete BESTLIB"""
        return Path(__file__).parent.parent
    
    @classmethod
    def load_js(cls, force_reload: bool = False) -> str:
        """
        Carga y cachea el archivo matrix.js.
        
        Args:
            force_reload (bool): Si True, fuerza recarga del cache
        
        Returns:
            str: Contenido del archivo JS
        
        Raises:
            TypeError: Si force_reload no es bool
        """
        if not isinstance(force_reload, bool):
            raise TypeError(f"force_reload debe ser bool, recibido: {type(force_reload).__name__}")
        
        if cls._js_cache is None or force_reload:
            js_path = cls.get_base_path() / "matrix.js"
            if js_path.exists():
                try:
                    with open(js_path, "r", encoding="utf-8") as f:
                        cls._js_cache = f.read()
                except (FileNotFoundError, PermissionError) as e:
                    print(f"⚠️ [AssetManager] Error al leer {js_path}: {e}")
                    cls._js_cache = ""
                except UnicodeDecodeError as e:
                    print(f"⚠️ [AssetManager] Error de encoding en {js_path}: {e}")
                    cls._js_cache = ""
            else:
                print(f"⚠️ [AssetManager] matrix.js no encontrado en: {js_path}")
                cls._js_cache = ""
        
        return cls._js_cache
    
    @classmethod
    def load_css(cls, force_reload: bool = False) -> str:
        """
        Carga y cachea el archivo style.css.
        
        Args:
            force_reload (bool): Si True, fuerza recarga del cache
        
        Returns:
            str: Contenido del archivo CSS
        
        Raises:
            TypeError: Si force_reload no es bool
        """
        if not isinstance(force_reload, bool):
            raise TypeError(f"force_reload debe ser bool, recibido: {type(force_reload).__name__}")
        
        if cls._css_cache is None or force_reload:
            css_path = cls.get_base_path() / "style.css"
            if css_path.exists():
                try:
                    with open(css_path, "r", encoding="utf-8") as f:
                        cls._css_cache = f.read()
                except (FileNotFoundError, PermissionError) as e:
                    print(f"⚠️ [AssetManager] Error al leer {css_path}: {e}")
                    cls._css_cache = ""
                except UnicodeDecodeError as e:
                    print(f"⚠️ [AssetManager] Error de encoding en {css_path}: {e}")
                    cls._css_cache = ""
            else:
                print(f"⚠️ [AssetManager] style.css no encontrado en: {css_path}")
                cls._css_cache = ""
        
        return cls._css_cache
    
    @classmethod
    def load_d3(cls, force_reload: bool = False) -> str:
        """
        Carga y cachea el archivo d3.min.js.
        
        Args:
            force_reload (bool): Si True, fuerza recarga del cache
        
        Returns:
            str: Contenido del archivo D3.js
        
        Raises:
            TypeError: Si force_reload no es bool
        """
        if not isinstance(force_reload, bool):
            raise TypeError(f"force_reload debe ser bool, recibido: {type(force_reload).__name__}")
        
        if cls._d3_cache is None or force_reload:
            d3_path = cls.get_base_path() / "d3.min.js"
            if d3_path.exists():
                try:
                    with open(d3_path, "r", encoding="utf-8") as f:
                        cls._d3_cache = f.read()
                except (FileNotFoundError, PermissionError) as e:
                    print(f"⚠️ [AssetManager] Error al leer {d3_path}: {e}")
                    cls._d3_cache = ""
                except UnicodeDecodeError as e:
                    print(f"⚠️ [AssetManager] Error de encoding en {d3_path}: {e}")
                    cls._d3_cache = ""
            else:
                print(f"⚠️ [AssetManager] d3.min.js no encontrado en: {d3_path}")
                cls._d3_cache = ""
        
        return cls._d3_cache
    
    @classmethod
    def clear_cache(cls) -> None:
        """Limpia el cache de assets"""
        cls._js_cache = None
        cls._css_cache = None
        cls._d3_cache = None
    
    @classmethod
    def get_all_assets(cls) -> dict:
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
    def is_colab(cls) -> bool:
        """
        Detecta si el código se está ejecutando en Google Colab.
        
        Returns:
            bool: True si está en Colab, False en caso contrario
        """
        return "google.colab" in sys.modules
    
    @classmethod
    def ensure_colab_assets_loaded(cls) -> bool:
        """
        Carga automáticamente los assets (d3.min.js, style.css) en Google Colab.
        matrix.js se incluye directamente en el JS generado, no se carga por separado.
        
        Solo se ejecuta si está en Colab y si los assets no han sido cargados previamente.
        
        Returns:
            bool: True si los assets se cargaron exitosamente, False en caso contrario
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

