"""
Inicialización específica para DeepNote
"""
import sys
import os


def is_deepnote():
    """
    Detecta si el código está corriendo en DeepNote.
    
    Returns:
        bool: True si está en DeepNote, False en caso contrario
    """
    try:
        # Verificar variables de entorno específicas de DeepNote
        if os.environ.get('DEEPNOTE_PROJECT_ID') or os.environ.get('DEEPNOTE_ENVIRONMENT'):
            return True
        
        # Verificar si estamos en un entorno Jupyter
        from IPython import get_ipython
        ip = get_ipython()
        
        if ip is None:
            return False
        
        # DeepNote usa Jupyter estándar, así que verificamos características comunes
        # Si estamos en Jupyter y no es Colab, podría ser DeepNote
        try:
            import google.colab
            # Si podemos importar google.colab, estamos en Colab, no DeepNote
            return False
        except ImportError:
            # No estamos en Colab, podría ser DeepNote u otro entorno Jupyter
            # Verificar si hay características de DeepNote
            if hasattr(ip, 'kernel') and ip.kernel:
                # Verificar si hay widgets disponibles (DeepNote generalmente los tiene)
                try:
                    import ipywidgets
                    # Si hay ipywidgets y no estamos en Colab, podría ser DeepNote
                    return True
                except ImportError:
                    return False
        
        return False
            
    except Exception:
        return False


def initialize_deepnote():
    """
    Inicializa BESTLIB para DeepNote.
    Habilita widgetsnbextension y jupyterlab manager para ipywidgets.
    
    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario
    """
    try:
        from IPython import get_ipython
        from IPython.display import display, HTML, Javascript
        
        ip = get_ipython()
        if ip is None:
            return False
        
        # 1. Habilitar widgetsnbextension (para Jupyter Notebook clásico)
        # Esto es necesario para que los widgets funcionen correctamente
        try:
            js_widgets = """
            (function() {
                // Intentar cargar widgetsnbextension
                if (typeof require !== 'undefined') {
                    require(['base/js/utils'], function(utils) {
                        try {
                            utils.load_extensions('widgets/notebook/js/extension');
                            console.log('✅ [BESTLIB] widgetsnbextension habilitado');
                        } catch(e) {
                            console.log('ℹ️ [BESTLIB] widgetsnbextension ya cargado o no necesario');
                        }
                    });
                }
            })();
            """
            display(Javascript(js_widgets))
        except Exception as e:
            global _debug
            if _debug:
                print(f"⚠️ [DeepNote] No se pudo habilitar widgetsnbextension: {e}")
        
        # 2. Activar jupyterlab manager para ipywidgets
        # Esto es necesario para JupyterLab y entornos modernos
        try:
            js_jupyterlab = """
            (function() {
                // Activar JupyterLab widgets manager
                if (typeof require !== 'undefined') {
                    require(['@jupyter-widgets/base'], function(widgets) {
                        console.log('✅ [BESTLIB] JupyterLab widgets manager disponible');
                    });
                }
                // También verificar si ya está disponible globalmente
                if (typeof window !== 'undefined' && window.Jupyter && window.Jupyter.WidgetManager) {
                    console.log('✅ [BESTLIB] WidgetManager ya disponible');
                }
            })();
            """
            display(Javascript(js_jupyterlab))
        except Exception as e:
            global _debug
            if _debug:
                print(f"⚠️ [DeepNote] No se pudo activar jupyterlab manager: {e}")
        
        # 3. Asegurar que ipywidgets esté correctamente inicializado
        try:
            import ipywidgets as widgets
            # Verificar que widgets esté funcionando
            if hasattr(widgets, 'Widget'):
                # Widgets está disponible
                pass
        except ImportError:
            global _debug
            if _debug:
                print("⚠️ [DeepNote] ipywidgets no está disponible")
        
        return True
        
    except Exception as e:
        if _debug:
            print(f"⚠️ [DeepNote] Error en inicialización: {e}")
        return False


# Variable global para debug
_debug = False


def set_debug(enabled):
    """Activa/desactiva mensajes de debug"""
    global _debug
    _debug = enabled


def ensure_deepnote_ready():
    """
    Asegura que DeepNote esté listo para usar BESTLIB.
    Ejecuta inicialización si es necesario.
    
    Returns:
        bool: True si DeepNote está listo, False en caso contrario
    """
    if not is_deepnote():
        return False
    
    # Intentar inicializar
    return initialize_deepnote()

