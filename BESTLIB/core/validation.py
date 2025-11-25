"""
Sistema centralizado de validación para BESTLIB.

Proporciona funciones helper reutilizables para validación consistente
en todo el código.
"""
from typing import Any, Optional, List, Dict, Union
from ..core.exceptions import DataError, ValueError as BestlibValueError
from ..utils.imports import has_pandas, get_pandas


def validate_dataframe(
    data: Any,
    required_cols: Optional[List[str]] = None,
    allow_empty: bool = False
) -> None:
    """
    Valida que data sea un DataFrame válido con las columnas requeridas.
    
    Args:
        data: Objeto a validar
        required_cols: Lista de columnas requeridas (opcional)
        allow_empty: Si True, permite DataFrame vacío
    
    Raises:
        DataError: Si data no es DataFrame válido o faltan columnas
        TypeError: Si required_cols no es lista o None
    """
    if not has_pandas():
        raise DataError("pandas no está instalado. Instala con: pip install pandas")
    
    pd = get_pandas()
    if pd is None:
        raise DataError("pandas no está disponible")
    
    if not isinstance(data, pd.DataFrame):
        raise DataError(f"Se esperaba un DataFrame de pandas, pero se recibió: {type(data).__name__}")
    
    # Validar que tenga columnas
    if not hasattr(data, 'columns') or len(data.columns) == 0:
        raise DataError("El DataFrame no tiene columnas")
    
    # Validar que no esté vacío (si no se permite)
    if not allow_empty and data.empty:
        raise DataError("El DataFrame está vacío")
    
    # Validar columnas requeridas
    if required_cols is not None:
        if not isinstance(required_cols, (list, tuple)):
            raise TypeError(f"required_cols debe ser lista o tupla, recibido: {type(required_cols).__name__}")
        
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise DataError(
                f"Faltan las siguientes columnas en el DataFrame: {missing_cols}. "
                f"Columnas disponibles: {list(data.columns)}"
            )


def validate_list_of_dicts(
    items: Any,
    required_keys: Optional[List[str]] = None,
    allow_empty: bool = False
) -> None:
    """
    Valida que items sea una lista de diccionarios con las keys requeridas.
    
    Args:
        items: Objeto a validar
        required_keys: Lista de keys requeridas (opcional)
        allow_empty: Si True, permite lista vacía
    
    Raises:
        DataError: Si items no es lista válida o faltan keys
        TypeError: Si required_keys no es lista o None
    """
    if not isinstance(items, list):
        raise DataError(f"Se esperaba una lista de diccionarios, pero se recibió: {type(items).__name__}")
    
    if not allow_empty and len(items) == 0:
        raise DataError("La lista de datos está vacía")
    
    if len(items) > 0:
        first_item = items[0]
        if not isinstance(first_item, dict):
            raise DataError("Los elementos de la lista deben ser diccionarios")
        
        # Validar keys requeridas
        if required_keys is not None:
            if not isinstance(required_keys, (list, tuple)):
                raise TypeError(f"required_keys debe ser lista o tupla, recibido: {type(required_keys).__name__}")
            
            missing_keys = [key for key in required_keys if key not in first_item]
            if missing_keys:
                raise DataError(f"Faltan las siguientes keys en los diccionarios: {missing_keys}")


def validate_numeric_range(
    value: Any,
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
    param_name: str = "value"
) -> None:
    """
    Valida que un valor numérico esté en un rango específico.
    
    Args:
        value: Valor a validar
        min_val: Valor mínimo permitido (opcional)
        max_val: Valor máximo permitido (opcional)
        param_name: Nombre del parámetro para mensajes de error
    
    Raises:
        TypeError: Si value no es numérico
        ValueError: Si value está fuera del rango permitido
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{param_name} debe ser int o float, recibido: {type(value).__name__}")
    
    import math
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{param_name} debe ser número finito, recibido: {value!r}")
    
    if min_val is not None and value < min_val:
        raise ValueError(f"{param_name} debe ser >= {min_val}, recibido: {value!r}")
    
    if max_val is not None and value > max_val:
        raise ValueError(f"{param_name} debe ser <= {max_val}, recibido: {value!r}")


def validate_string_param(
    value: Any,
    param_name: str,
    min_length: int = 1,
    max_length: Optional[int] = None,
    allow_none: bool = False
) -> None:
    """
    Valida que un parámetro sea un string válido.
    
    Args:
        value: Valor a validar
        param_name: Nombre del parámetro para mensajes de error
        min_length: Longitud mínima permitida
        max_length: Longitud máxima permitida (opcional)
        allow_none: Si True, permite None
    
    Raises:
        TypeError: Si value no es string (o None si allow_none=True)
        ValueError: Si value está vacío o fuera del rango de longitud
    """
    if allow_none and value is None:
        return
    
    if not isinstance(value, str):
        raise TypeError(f"{param_name} debe ser str, recibido: {type(value).__name__}")
    
    if len(value) < min_length:
        raise ValueError(f"{param_name} debe tener al menos {min_length} caracteres, recibido: {len(value)}")
    
    if max_length is not None and len(value) > max_length:
        raise ValueError(f"{param_name} debe tener como máximo {max_length} caracteres, recibido: {len(value)}")


def safe_get_first_item(items: Optional[List[Any]]) -> Optional[Any]:
    """
    Obtiene el primer elemento de una lista de forma segura.
    
    Args:
        items: Lista de elementos
    
    Returns:
        Primer elemento o None si la lista está vacía o es None
    """
    if not items or not isinstance(items, list) or len(items) == 0:
        return None
    return items[0]


def safe_dataframe(items: Optional[Any]) -> Optional[Any]:
    """
    Convierte items a DataFrame de forma segura.
    
    Args:
        items: Lista de diccionarios, DataFrame, o None
    
    Returns:
        DataFrame o None si pandas no está disponible o items es inválido
    """
    if not has_pandas():
        return None
    
    pd = get_pandas()
    if pd is None:
        return None
    
    if items is None:
        return pd.DataFrame()
    
    # Si ya es DataFrame, retornarlo
    if isinstance(items, pd.DataFrame):
        return items.copy()
    
    # Si es lista vacía, retornar DataFrame vacío
    if isinstance(items, list) and len(items) == 0:
        return pd.DataFrame()
    
    # Si es lista con elementos, validar y convertir
    if isinstance(items, list):
        if len(items) > 0:
            first_item = safe_get_first_item(items)
            if isinstance(first_item, dict):
                try:
                    return pd.DataFrame(items)
                except (ValueError, TypeError, KeyError):
                    return None
        return pd.DataFrame()
    
    return None

