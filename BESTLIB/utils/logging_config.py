"""
Configuración de logging para BESTLIB

Proporciona logging estructurado para reemplazar los print() statements
y mejorar el debugging.
"""
import logging
import sys


# Logger raíz de BESTLIB
_bestlib_logger = None


def get_logger(name='BESTLIB'):
    """
    Obtiene logger configurado para BESTLIB.
    
    Args:
        name (str): Nombre del logger. Por defecto 'BESTLIB'.
                   Para módulos específicos usar 'BESTLIB.module'
    
    Returns:
        logging.Logger: Logger configurado
        
    Examples:
        >>> from BESTLIB.utils.logging_config import get_logger
        >>> logger = get_logger('BESTLIB.charts')
        >>> logger.debug("Cargando scatter chart")
        >>> logger.warning("Chart no encontrado")
        >>> logger.error("Error crítico")
    """
    logger = logging.getLogger(name)
    
    # Solo configurar si no tiene handlers
    # (evita duplicar handlers en reimports de Jupyter)
    if not logger.handlers and name == 'BESTLIB':
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(name)s] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Por defecto, solo WARNING y superiores
        # El usuario puede cambiar con set_log_level()
        logger.setLevel(logging.WARNING)
    
    return logger


def set_log_level(level):
    """
    Establece el nivel de logging para BESTLIB.
    
    Args:
        level: Puede ser:
            - String: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
            - Int: logging.DEBUG, logging.INFO, etc.
            
    Examples:
        >>> from BESTLIB.utils.logging_config import set_log_level
        >>> set_log_level('DEBUG')  # Ver todos los mensajes
        >>> set_log_level('WARNING')  # Solo warnings y errores
    """
    logger = get_logger('BESTLIB')
    
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.WARNING)
    
    logger.setLevel(level)
    
    # Propagar a todos los sub-loggers
    for handler in logger.handlers:
        handler.setLevel(level)


def enable_debug():
    """
    Habilita modo debug (equivalente a MatrixLayout.set_debug(True)).
    
    Examples:
        >>> from BESTLIB.utils.logging_config import enable_debug
        >>> enable_debug()
    """
    set_log_level('DEBUG')


def disable_debug():
    """
    Deshabilita modo debug.
    
    Examples:
        >>> from BESTLIB.utils.logging_config import disable_debug
        >>> disable_debug()
    """
    set_log_level('WARNING')


# Inicializar logger raíz al importar el módulo
_bestlib_logger = get_logger('BESTLIB')

