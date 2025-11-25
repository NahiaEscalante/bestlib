"""
Transformadores de datos para BESTLIB
"""
# ✅ MED-003: Eliminado HAS_PANDAS - usar has_pandas() y get_pandas() siempre
from ..utils.imports import has_pandas, get_pandas
from ..utils.json import sanitize_for_json


def dataframe_to_dicts(df):
    """
    Convierte DataFrame a lista de diccionarios.
    
    Args:
        df: DataFrame de pandas
    
    Returns:
        list: Lista de diccionarios
    """
    # ✅ MED-003: Usar has_pandas() y get_pandas()
    if not has_pandas():
        raise ValueError("pandas no está instalado")
    pd = get_pandas()
    if pd is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Requiere DataFrame de pandas")
    return df.to_dict('records')


def dicts_to_dataframe(dicts):
    """
    Convierte lista de diccionarios a DataFrame.
    
    Args:
        dicts: Lista de diccionarios
    
    Returns:
        DataFrame: DataFrame de pandas
    """
    # ✅ MED-003: Usar has_pandas() y get_pandas()
    if not has_pandas():
        raise ValueError("pandas no está instalado")
    pd = get_pandas()
    if pd is None:
        raise ValueError("pandas no está disponible")
    if not isinstance(dicts, list):
        raise ValueError("Requiere lista de diccionarios")
    return pd.DataFrame(dicts)


def normalize_types(data):
    """
    Normaliza tipos numpy/pandas a tipos Python nativos.
    
    Args:
        data: Datos a normalizar (cualquier tipo)
    
    Returns:
        Datos normalizados
    """
    return sanitize_for_json(data)


def sanitize_for_json(obj):
    """
    Sanitiza datos para serialización JSON.
    Alias para utils.json.sanitize_for_json.
    """
    from ..utils.json import sanitize_for_json as _sanitize
    return _sanitize(obj)

