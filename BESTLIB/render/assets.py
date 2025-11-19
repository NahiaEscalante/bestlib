"""
Asset Manager - Gestión de assets JS y CSS
"""
import os
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

