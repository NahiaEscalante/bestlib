"""
Utilidades para sanitización JSON
"""


def sanitize_for_json(obj):
    """
    Convierte recursivamente tipos numpy y no serializables a tipos JSON puros.
    
    Args:
        obj: Objeto a sanitizar
    
    Returns:
        Objeto sanitizado compatible con JSON
    """
    try:
        import numpy as _np  # opcional
    except Exception:
        _np = None

    if obj is None:
        return None
    if isinstance(obj, (str, bool, int, float)):
        return int(obj) if type(obj).__name__ in ("int64", "int32") else (float(obj) if type(obj).__name__ in ("float32", "float64") else obj)
    if _np is not None:
        if isinstance(obj, _np.integer):
            return int(obj)
        if isinstance(obj, _np.floating):
            return float(obj)
        if isinstance(obj, _np.ndarray):
            return sanitize_for_json(obj.tolist())
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]
    # Fallback a string para objetos desconocidos
    return str(obj)

