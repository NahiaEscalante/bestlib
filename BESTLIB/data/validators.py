"""
Validadores de datos para BESTLIB
"""
from ..core.exceptions import DataError
from ._imports import ensure_pandas

pd = ensure_pandas()
HAS_PANDAS = pd is not None


def validate_data_structure(data, required_type=None):
    """
    Valida que los datos tengan el formato correcto.
    
    Args:
        data: Datos a validar
        required_type: Tipo esperado ('DataFrame' o 'list')
    
    Raises:
        DataError: Si los datos no tienen el formato correcto
    """
    if required_type == 'DataFrame':
        if not HAS_PANDAS:
            raise DataError("pandas no está instalado. Instala con: pip install pandas")
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


def validate_columns(data, required_cols, required_type=None):
    """
    Valida que los datos tengan las columnas/keys requeridas.
    
    Args:
        data: DataFrame o lista de diccionarios
        required_cols: Lista de columnas/keys requeridas
        required_type: Tipo esperado ('DataFrame' o 'list')
    
    Raises:
        DataError: Si faltan columnas/keys requeridas
    """
    if required_type == 'DataFrame':
        if not HAS_PANDAS or not isinstance(data, pd.DataFrame):
            raise DataError("Datos deben ser DataFrame de pandas")
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


def validate_data_types(data, column_types=None):
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


def validate_scatter_data(data, x_col, y_col):
    """
    Valida datos para scatter plot.
    
    Args:
        data: DataFrame o lista de diccionarios
        x_col: Nombre de columna para eje X
        y_col: Nombre de columna para eje Y
    
    Raises:
        DataError: Si los datos no son válidos
    """
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        validate_data_structure(data, required_type='DataFrame')
        validate_columns(data, [x_col, y_col], required_type='DataFrame')
    else:
        validate_data_structure(data, required_type='list')
        validate_columns(data, [x_col, y_col], required_type='list')


def validate_bar_data(data, category_col, value_col=None):
    """
    Valida datos para bar chart.
    
    Args:
        data: DataFrame o lista de diccionarios
        category_col: Nombre de columna categórica
        value_col: Nombre de columna numérica (opcional)
    
    Raises:
        DataError: Si los datos no son válidos
    """
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        validate_data_structure(data, required_type='DataFrame')
        required = [category_col]
        if value_col:
            required.append(value_col)
        validate_columns(data, required, required_type='DataFrame')
    else:
        validate_data_structure(data, required_type='list')
        required = [category_col]
        if value_col:
            required.append(value_col)
        validate_columns(data, required, required_type='list')

