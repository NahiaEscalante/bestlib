"""
Utilidades para sanitización JSON
"""
import math


def _is_nan_or_inf(value):
    """Verifica si un valor es NaN o Inf de forma segura."""
    if isinstance(value, float):
        return math.isnan(value) or math.isinf(value)
    try:
        import numpy as np
        if isinstance(value, (np.floating, np.integer)):
            return np.isnan(value) or np.isinf(value)
    except:
        pass
    return False


def _safe_float(value, default=0.0):
    """
    Convierte un valor a float de forma segura, manejando NaN e Inf.
    
    Args:
        value: Valor a convertir
        default: Valor por defecto si es NaN o Inf
    
    Returns:
        float: Valor convertido o default si es inválido
    """
    try:
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (ValueError, TypeError):
        return default


def sanitize_for_json(obj, replace_invalid_with=None):
    """
    Convierte recursivamente tipos numpy y no serializables a tipos JSON puros.
    Maneja NaN e Inf reemplazándolos con valores válidos.
    
    Args:
        obj: Objeto a sanitizar
        replace_invalid_with: Valor para reemplazar NaN/Inf (None = usar 0.0 para números)
    
    Returns:
        Objeto sanitizado compatible con JSON
    """
    try:
        import numpy as _np  # opcional
    except Exception:
        _np = None

    if obj is None:
        return None
    
    # Manejar booleanos primero (antes de int porque bool es subclase de int)
    if isinstance(obj, bool):
        return obj
    
    # Manejar strings
    if isinstance(obj, str):
        return obj
    
    # Manejar enteros
    if isinstance(obj, int) and not isinstance(obj, bool):
        return obj
    
    # Manejar floats con validación de NaN/Inf
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return replace_invalid_with if replace_invalid_with is not None else 0.0
        return obj
    
    # Manejar tipos numpy
    if _np is not None:
        # Numpy integers
        if isinstance(obj, _np.integer):
            return int(obj)
        
        # Numpy floats con validación de NaN/Inf
        if isinstance(obj, _np.floating):
            float_val = float(obj)
            if math.isnan(float_val) or math.isinf(float_val):
                return replace_invalid_with if replace_invalid_with is not None else 0.0
            return float_val
        
        # Numpy arrays
        if isinstance(obj, _np.ndarray):
            return sanitize_for_json(obj.tolist(), replace_invalid_with)
        
        # Numpy bool
        if isinstance(obj, _np.bool_):
            return bool(obj)
    
    # Manejar diccionarios
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v, replace_invalid_with) for k, v in obj.items()}
    
    # Manejar listas, tuplas, sets
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v, replace_invalid_with) for v in obj]
    
    # Manejar tipos especiales por nombre de clase (para tipos numpy con nombres específicos)
    type_name = type(obj).__name__
    if type_name in ("int64", "int32", "int16", "int8", "uint64", "uint32", "uint16", "uint8"):
        return int(obj)
    if type_name in ("float64", "float32", "float16"):
        float_val = float(obj)
        if math.isnan(float_val) or math.isinf(float_val):
            return replace_invalid_with if replace_invalid_with is not None else 0.0
        return float_val
    
    # Fallback a string para objetos desconocidos
    return str(obj)

