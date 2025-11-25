"""
Utilidades para importación segura de dependencias opcionales.
Evita manipulación peligrosa de sys.modules.
"""
import sys
from typing import Optional, Tuple

# Variables globales para estado de importación
_HAS_PANDAS: Optional[bool] = None
_pd_module = None


def safe_import_pandas() -> Tuple[bool, Optional[object]]:
    """
    Importa pandas de forma segura sin manipular sys.modules.
    
    Returns:
        Tuple[bool, Optional[object]]: (HAS_PANDAS, pd_module)
            - HAS_PANDAS: True si pandas está disponible
            - pd_module: Módulo pandas o None
    """
    global _HAS_PANDAS, _pd_module
    
    # Si ya se intentó importar, retornar resultado cacheado
    if _HAS_PANDAS is not None:
        return _HAS_PANDAS, _pd_module
    
    try:
        # Intentar importar pandas normalmente
        # Si pandas está corrupto, dejar que falle con un error claro
        import pandas as pd
        
        # Verificar que pandas esté completamente inicializado
        _ = pd.__version__
        
        _HAS_PANDAS = True
        _pd_module = pd
        return True, pd
        
    except ImportError:
        # pandas no está instalado
        _HAS_PANDAS = False
        _pd_module = None
        return False, None
    except (AttributeError, ModuleNotFoundError) as e:
        # pandas está corrupto o no se puede inicializar
        # NO manipular sys.modules - dejar que el error se propague
        _HAS_PANDAS = False
        _pd_module = None
        # Log el error pero no fallar silenciosamente
        if hasattr(sys, 'stderr'):
            print(
                f"⚠️ [BESTLIB] Advertencia: pandas está instalado pero no se puede inicializar: {e}",
                file=sys.stderr
            )
        return False, None
    except Exception as e:
        # Error inesperado - registrar pero no fallar
        _HAS_PANDAS = False
        _pd_module = None
        if hasattr(sys, 'stderr'):
            print(
                f"⚠️ [BESTLIB] Error inesperado al importar pandas: {e}",
                file=sys.stderr
            )
        return False, None


def get_pandas() -> Optional[object]:
    """
    Obtiene el módulo pandas si está disponible.
    
    Returns:
        Módulo pandas o None
    """
    _, pd = safe_import_pandas()
    return pd


def has_pandas() -> bool:
    """
    Verifica si pandas está disponible.
    
    Returns:
        True si pandas está disponible, False en caso contrario
    """
    has_pd, _ = safe_import_pandas()
    return has_pd

