"""
Helper para detección y manejo de pandas corrupto

Centraliza la lógica de importación defensiva de pandas que estaba duplicada
en ~20 módulos diferentes.
"""
import logging
import sys

logger = logging.getLogger('BESTLIB.pandas')

# Cache global
_HAS_PANDAS = None
_pd = None


def get_pandas():
    """
    Obtiene pandas de forma segura, manejando el caso de pandas corrupto.
    
    Este helper centraliza la lógica de importación defensiva de pandas
    que aparecía duplicada en múltiples módulos.
    
    Returns:
        tuple: (HAS_PANDAS: bool, pd: module or None)
        
    Examples:
        >>> HAS_PANDAS, pd = get_pandas()
        >>> if HAS_PANDAS:
        >>>     df = pd.DataFrame({'x': [1, 2, 3]})
    """
    global _HAS_PANDAS, _pd
    
    # Si ya está en cache, retornar
    if _HAS_PANDAS is not None:
        return _HAS_PANDAS, _pd
    
    try:
        # Verificar que pandas no esté parcialmente inicializado (bug conocido)
        if 'pandas' in sys.modules:
            try:
                pd_test = sys.modules['pandas']
                _ = pd_test.__version__  # Verificar que está completo
            except (AttributeError, ImportError) as e:
                logger.warning(f"Pandas detectado corrupto, limpiando módulos: {e}")
                
                # Limpiar pandas corrupto del cache de módulos
                del sys.modules['pandas']
                
                # También limpiar submódulos relacionados
                modules_to_remove = [k for k in list(sys.modules.keys()) 
                                    if k.startswith('pandas.')]
                for mod in modules_to_remove:
                    try:
                        del sys.modules[mod]
                    except Exception:
                        pass
        
        # Intentar importar pandas
        import pandas as pd
        
        # Verificar que está completamente inicializado
        _ = pd.__version__
        
        _HAS_PANDAS = True
        _pd = pd
        logger.debug(f"Pandas {pd.__version__} disponible y funcionando")
        
    except (ImportError, ModuleNotFoundError) as e:
        # Pandas no está instalado, esto es esperado
        logger.debug(f"Pandas no está instalado: {e}")
        _HAS_PANDAS = False
        _pd = None
        
    except Exception as e:
        # Error inesperado
        logger.error(f"Error inesperado al importar pandas: {e}")
        _HAS_PANDAS = False
        _pd = None
    
    return _HAS_PANDAS, _pd


def reset_pandas_cache():
    """
    Resetea el cache de pandas.
    
    Útil para testing o cuando se necesita forzar re-importación.
    """
    global _HAS_PANDAS, _pd
    _HAS_PANDAS = None
    _pd = None

