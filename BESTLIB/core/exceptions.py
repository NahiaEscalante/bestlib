"""
Jerarquía de excepciones para BESTLIB
"""
import logging
import sys
from typing import Optional, Type, Tuple

# Configurar logger para BESTLIB
_logger = logging.getLogger('BESTLIB')

# Configurar handler por defecto si no existe
if not _logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    _logger.addHandler(handler)
    _logger.setLevel(logging.WARNING)  # Por defecto solo warnings y errores


def get_logger():
    """
    Obtiene el logger centralizado de BESTLIB.
    
    Returns:
        logging.Logger: Logger configurado para BESTLIB
    """
    return _logger


class BestlibError(Exception):
    """Excepción base para BESTLIB"""
    pass


class LayoutError(BestlibError):
    """Error en layout"""
    pass


class ChartError(BestlibError):
    """Error en gráfico"""
    pass


class DataError(BestlibError):
    """Error en datos"""
    pass


class RenderError(BestlibError):
    """Error en renderizado"""
    pass


class CommunicationError(BestlibError):
    """Error en comunicación JS ↔ Python"""
    pass


def safe_execute(
    func,
    *args,
    expected_exceptions: Tuple[Type[Exception], ...] = (),
    error_message: Optional[str] = None,
    default_return=None,
    log_error: bool = True,
    **kwargs
):
    """
    Ejecuta una función de forma segura, capturando solo excepciones esperadas.
    
    Args:
        func: Función a ejecutar
        *args: Argumentos posicionales para la función
        expected_exceptions: Tupla de excepciones que se esperan y deben capturarse
        error_message: Mensaje de error personalizado
        default_return: Valor a retornar si ocurre una excepción esperada
        log_error: Si True, registra errores inesperados
        **kwargs: Argumentos con nombre para la función
    
    Returns:
        Resultado de la función o default_return si ocurre excepción esperada
    
    Raises:
        Cualquier excepción no incluida en expected_exceptions
    """
    try:
        return func(*args, **kwargs)
    except expected_exceptions as e:
        if log_error and error_message:
            _logger.warning(f"{error_message}: {e}")
        elif log_error:
            _logger.warning(f"Excepción esperada en {func.__name__}: {e}")
        return default_return
    except Exception as e:
        # Excepción inesperada - siempre registrar y re-raise
        error_msg = error_message or f"Error inesperado en {func.__name__}"
        _logger.error(f"{error_msg}: {e}", exc_info=True)
        raise

