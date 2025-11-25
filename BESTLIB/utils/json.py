"""
Utilidades para sanitización JSON
"""
from typing import Any, Set, Optional


def sanitize_for_json(obj: Any, _visited: Optional[Set[int]] = None) -> Any:
    """
    Convierte recursivamente tipos numpy y no serializables a tipos JSON puros.
    Previene recursión infinita con referencias circulares.
    
    Args:
        obj: Objeto a sanitizar
        _visited: Set de IDs de objetos visitados (uso interno)
    
    Returns:
        Objeto sanitizado compatible con JSON
    
    Raises:
        RecursionError: Si la estructura es demasiado profunda (protección del sistema)
    """
    if _visited is None:
        _visited = set()
    
    # Detectar referencias circulares
    obj_id = id(obj)
    if obj_id in _visited:
        return "<circular reference>"
    
    try:
        import numpy as _np  # opcional
    except Exception:
        _np = None

    if obj is None:
        return None
    
    if isinstance(obj, (str, bool, int, float)):
        try:
            type_name = type(obj).__name__
            if type_name in ("int64", "int32"):
                return int(obj)
            elif type_name in ("float32", "float64"):
                return float(obj)
            else:
                return obj
        except (ValueError, TypeError, OverflowError):
            # Si falla la conversión, retornar string
            return str(obj)
    
    if _np is not None:
        if isinstance(obj, _np.integer):
            return int(obj)
        if isinstance(obj, _np.floating):
            return float(obj)
        if isinstance(obj, _np.ndarray):
            _visited.add(obj_id)
            try:
                return sanitize_for_json(obj.tolist(), _visited)
            finally:
                _visited.discard(obj_id)
    
    if isinstance(obj, dict):
        _visited.add(obj_id)
        try:
            return {str(k): sanitize_for_json(v, _visited) for k, v in obj.items()}
        finally:
            _visited.discard(obj_id)
    
    if isinstance(obj, (list, tuple, set)):
        _visited.add(obj_id)
        try:
            return [sanitize_for_json(v, _visited) for v in obj]
        finally:
            _visited.discard(obj_id)
    
    # Fallback a string para objetos desconocidos
    return str(obj)

