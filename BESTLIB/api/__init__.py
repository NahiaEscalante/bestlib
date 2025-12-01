# BESTLIB API Module

"""
Módulo API público de BESTLIB con funciones helper de alto nivel.
"""

from typing import Dict, Any, Optional
import pandas as pd
from ..layouts.matrix import MatrixLayout
from ..layouts.reactive import ReactiveMatrixLayout


def create_dashboard(
    layout_str: str,
    charts: Dict[str, Dict[str, Any]],
    reactive: bool = False,
    link_all: bool = False
):
    """
    Crea un dashboard completo de forma simplificada.
    
    Args:
        layout_str: String ASCII del layout
        charts: Diccionario {cell_name: chart_spec}
        reactive: Si usar ReactiveMatrixLayout
        link_all: Si enlazar todas las vistas automáticamente
        
    Returns:
        MatrixLayout o ReactiveMatrixLayout configurado
        
    Example:
        >>> dashboard = create_dashboard(
        ...     "scatter | bar",
        ...     {
        ...         'scatter': {'type': 'scatter', 'data': df, 'x_col': 'x', 'y_col': 'y'},
        ...         'bar': {'type': 'bar', 'data': df, 'x_col': 'category'}
        ...     },
        ...     reactive=True,
        ...     link_all=True
        ... )
        >>> dashboard.render()
    """
    LayoutClass = ReactiveMatrixLayout if reactive else MatrixLayout
    
    kwargs = {}
    if reactive and link_all:
        kwargs['link_all'] = link_all
        
    layout = LayoutClass(layout_str, **kwargs)
    
    for cell_name, chart_spec in charts.items():
        layout[cell_name] = chart_spec
        
    return layout


def quick_scatter(data: pd.DataFrame, x_col: str, y_col: str, **kwargs):
    """
    Crea rápidamente un scatter plot simple.
    
    Args:
        data: DataFrame con los datos
        x_col: Nombre de columna para eje X
        y_col: Nombre de columna para eje Y
        **kwargs: Opciones adicionales
        
    Returns:
        MatrixLayout con un scatter plot
        
    Example:
        >>> quick_scatter(df, 'age', 'income').render()
    """
    layout = MatrixLayout("scatter")
    layout['scatter'] = {
        'type': 'scatter',
        'data': data,
        'x_col': x_col,
        'y_col': y_col,
        **kwargs
    }
    return layout


def quick_bar(data: pd.DataFrame, x_col: str, y_col: Optional[str] = None, **kwargs):
    """
    Crea rápidamente un gráfico de barras.
    
    Args:
        data: DataFrame con los datos
        x_col: Nombre de columna para categorías
        y_col: Nombre de columna para valores (opcional)
        **kwargs: Opciones adicionales
        
    Returns:
        MatrixLayout con un bar chart
    """
    layout = MatrixLayout("bar")
    spec = {
        'type': 'bar',
        'data': data,
        'x_col': x_col,
        **kwargs
    }
    if y_col:
        spec['y_col'] = y_col
    layout['bar'] = spec
    return layout


def quick_histogram(data: pd.DataFrame, column: str, bins: int = 30, **kwargs):
    """
    Crea rápidamente un histograma.
    
    Args:
        data: DataFrame con los datos
        column: Nombre de columna a visualizar
        bins: Número de bins
        **kwargs: Opciones adicionales
        
    Returns:
        MatrixLayout con un histograma
    """
    layout = MatrixLayout("histogram")
    layout['histogram'] = {
        'type': 'histogram',
        'data': data,
        'column': column,
        'bins': bins,
        **kwargs
    }
    return layout


__all__ = [
    'create_dashboard',
    'quick_scatter',
    'quick_bar',
    'quick_histogram',
]
