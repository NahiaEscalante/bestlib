"""
Transformadores de datos para BESTLIB
"""
# Import helpers compartidos
from ._imports import ensure_pandas, ensure_numpy
from ..utils.json import sanitize_for_json

pd = ensure_pandas()
np = ensure_numpy()
HAS_PANDAS = pd is not None
HAS_NUMPY = np is not None


def dataframe_to_dicts(df):
    """
    Convierte DataFrame a lista de diccionarios.
    
    Args:
        df: DataFrame de pandas
    
    Returns:
        list: Lista de diccionarios
    """
    if not HAS_PANDAS or not isinstance(df, pd.DataFrame):
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
    if not HAS_PANDAS:
        raise ValueError("pandas no está instalado")
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

