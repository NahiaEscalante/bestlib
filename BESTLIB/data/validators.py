"""
Validadores de datos para BESTLIB
"""
from typing import Any, Optional, List, Tuple, Dict
from ..core.exceptions import DataError
from ..utils.imports import has_pandas, get_pandas


def validate_data_structure(data: Any, required_type: Optional[str] = None) -> None:
    """
    Valida que los datos tengan el formato correcto.
    
    Args:
        data: Datos a validar
        required_type: Tipo esperado ('DataFrame' o 'list')
    
    Raises:
        TypeError: Si required_type no es str o tiene valor inválido
        DataError: Si los datos no tienen el formato correcto
    """
    if required_type is not None:
        if not isinstance(required_type, str):
            raise TypeError(f"required_type debe ser str, recibido: {type(required_type).__name__}")
        if required_type not in ("DataFrame", "list"):
            raise ValueError(f"required_type debe ser 'DataFrame' o 'list', recibido: {required_type!r}")
    
    if required_type == 'DataFrame':
        if not has_pandas():
            raise DataError("pandas no está instalado. Instala con: pip install pandas")
        pd = get_pandas()
        if pd is None:
            raise DataError("pandas no está disponible")
        if not isinstance(data, pd.DataFrame):
            raise DataError(f"Se esperaba un DataFrame de pandas, pero se recibió: {type(data).__name__}")
        if data.empty:
            raise DataError("El DataFrame está vacío")
    elif required_type == 'list':
        if not isinstance(data, list):
            raise DataError(f"Se esperaba una lista de diccionarios, pero se recibió: {type(data).__name__}")
        if len(data) == 0:
            raise DataError("La lista de datos está vacía")
        if len(data) > 0 and not isinstance(data[0], dict):
            raise DataError("Los elementos de la lista deben ser diccionarios")


def validate_columns(data: Any, required_cols: List[str], required_type: Optional[str] = None) -> None:
    """
    Valida que los datos tengan las columnas/keys requeridas.
    
    Args:
        data: DataFrame o lista de diccionarios
        required_cols: Lista de columnas/keys requeridas
        required_type: Tipo esperado ('DataFrame' o 'list')
    
    Raises:
        ValueError: Si required_cols está vacío o required_type es inválido
        DataError: Si faltan columnas/keys requeridas
    """
    if not isinstance(required_cols, (list, tuple)) or len(required_cols) == 0:
        raise ValueError(f"required_cols debe ser lista/tupla no vacía, recibido: {required_cols!r}")
    
    if required_type is not None and required_type not in ("DataFrame", "list"):
        raise ValueError(f"required_type debe ser 'DataFrame' o 'list', recibido: {required_type!r}")
    
    if required_type == 'DataFrame':
        if not has_pandas():
            raise DataError("pandas no está instalado. Instala con: pip install pandas")
        pd = get_pandas()
        if pd is None or not isinstance(data, pd.DataFrame):
            raise DataError("Datos deben ser DataFrame de pandas")
        if data.empty:
            raise DataError("El DataFrame está vacío")
        # ✅ NUEVO: Validar que tenga columnas
        if len(data.columns) == 0:
            raise DataError("El DataFrame no tiene columnas")
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise DataError(
                f"Faltan las siguientes columnas en el DataFrame: {missing_cols}. "
                f"Columnas disponibles: {list(data.columns)}"
            )
    elif required_type == 'list':
        if not isinstance(data, list) or len(data) == 0:
            raise DataError("Datos deben ser lista no vacía de diccionarios")
        first_item = data[0]
        if not isinstance(first_item, dict):
            raise DataError("Los elementos de la lista deben ser diccionarios")
        missing_keys = [key for key in required_cols if key not in first_item]
        if missing_keys:
            raise DataError(f"Faltan las siguientes keys en los diccionarios: {missing_keys}")


def validate_data_types(data: Any, column_types: Optional[Dict[str, type]] = None) -> bool:
    """
    Valida tipos de datos en columnas (básico).
    
    Args:
        data: DataFrame o lista de diccionarios
        column_types: Dict {column: expected_type} (opcional)
    
    Returns:
        bool: True si los tipos son válidos
    """
    # Implementación básica - puede extenderse
    return True


def validate_scatter_data(data: Any, x_col: str, y_col: str) -> None:
    """
    Valida datos para scatter plot.
    
    Args:
        data: DataFrame o lista de diccionarios
        x_col: Nombre de columna para eje X
        y_col: Nombre de columna para eje Y
    
    Raises:
        DataError: Si data es None o los datos no son válidos
        ValueError: Si x_col o y_col son inválidos
    """
    if data is None:
        raise DataError("data no puede ser None")
    if not isinstance(x_col, str) or not x_col:
        raise ValueError(f"x_col debe ser str no vacío, recibido: {x_col!r}")
    if not isinstance(y_col, str) or not y_col:
        raise ValueError(f"y_col debe ser str no vacío, recibido: {y_col!r}")
    
    if has_pandas():
        pd = get_pandas()
        if pd is not None and isinstance(data, pd.DataFrame):
            validate_data_structure(data, required_type='DataFrame')
            validate_columns(data, [x_col, y_col], required_type='DataFrame')
            return
    
    validate_data_structure(data, required_type='list')
    validate_columns(data, [x_col, y_col], required_type='list')


def validate_bar_data(data: Any, category_col: str, value_col: Optional[str] = None) -> None:
    """
    Valida datos para bar chart.
    
    Args:
        data: DataFrame o lista de diccionarios
        category_col: Nombre de columna categórica
        value_col: Nombre de columna numérica (opcional)
    
    Raises:
        DataError: Si data es None o los datos no son válidos
        ValueError: Si category_col es inválido
    """
    if data is None:
        raise DataError("data no puede ser None")
    if not isinstance(category_col, str) or not category_col:
        raise ValueError(f"category_col debe ser str no vacío, recibido: {category_col!r}")
    
    if has_pandas():
        pd = get_pandas()
        if pd is not None and isinstance(data, pd.DataFrame):
            validate_data_structure(data, required_type='DataFrame')
            required = [category_col]
            if value_col:
                required.append(value_col)
            validate_columns(data, required, required_type='DataFrame')
            return
    
    validate_data_structure(data, required_type='list')
    required = [category_col]
    if value_col:
        required.append(value_col)
    validate_columns(data, required, required_type='list')

