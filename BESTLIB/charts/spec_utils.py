"""
Validadores simples para specs de BESTLIB.
"""
from ..core.exceptions import ChartError

def validate_spec(spec):
    """
    Valida que un spec tenga la estructura correcta.
    
    Algunos tipos de gráficos usan estructuras alternativas a 'data':
    - heatmap: usa 'cells'
    - line/line_plot: usa 'series'
    - grouped_bar: usa 'rows', 'groups', 'series'
    - step_plot: usa 'series'
    """
    if not isinstance(spec, dict):
        raise ChartError("El spec debe ser un diccionario")
    if 'type' not in spec:
        raise ChartError("El spec debe incluir 'type'")
    
    # Tipos con campos alternativos a 'data'
    alternative_fields = {
        'heatmap': ['cells', 'data'],
        'line': ['series', 'data'],
        'line_plot': ['series', 'data'],
        'grouped_bar': ['rows', 'series', 'data'],
        'step_plot': ['series', 'data'],
    }
    
    chart_type = spec.get('type')
    if chart_type in alternative_fields:
        if not any(f in spec for f in alternative_fields[chart_type]):
            raise ChartError(f"Spec de '{chart_type}' requiere alguno de: {alternative_fields[chart_type]}")
    elif 'data' not in spec:
        raise ChartError("El spec debe incluir 'data'")
    
    return spec

