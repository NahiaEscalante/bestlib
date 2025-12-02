"""
Validadores simples para specs de BESTLIB.
"""
from ..core.exceptions import ChartError

def validate_spec(spec):
    if not isinstance(spec, dict):
        raise ChartError("El spec debe ser un diccionario")
    if 'type' not in spec:
        raise ChartError("El spec debe incluir 'type'")
    if 'data' not in spec:
        raise ChartError("El spec debe incluir 'data'")
    return spec

