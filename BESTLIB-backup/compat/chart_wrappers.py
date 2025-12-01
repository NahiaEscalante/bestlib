"""
Wrappers de compatibilidad hacia atrás para métodos map_*
"""
import warnings
from ..charts.registry import ChartRegistry


def _deprecation_warning(old_method, new_method):
    """Genera warning de deprecación"""
    warnings.warn(
        f"{old_method} está deprecado. Use {new_method} en su lugar.",
        DeprecationWarning,
        stacklevel=3
    )


def map_scatter(letter, data, x_col=None, y_col=None, category_col=None,
                size_col=None, color_col=None, **kwargs):
    """
    Wrapper de compatibilidad para map_scatter.
    
    DEPRECATED: Use ChartRegistry.get('scatter').get_spec() en su lugar.
    """
    _deprecation_warning(
        "MatrixLayout.map_scatter()",
        "ChartRegistry.get('scatter').get_spec()"
    )
    
    chart = ChartRegistry.get('scatter')
    spec = chart.get_spec(
        data,
        x_col=x_col,
        y_col=y_col,
        category_col=category_col,
        size_col=size_col,
        color_col=color_col,
        **kwargs
    )
    
    # Para compatibilidad, retornar spec que puede usarse en MatrixLayout._map
    return spec


def map_barchart(letter, data, category_col=None, value_col=None, **kwargs):
    """Wrapper de compatibilidad para map_barchart"""
    _deprecation_warning(
        "MatrixLayout.map_barchart()",
        "ChartRegistry.get('bar').get_spec()"
    )
    
    chart = ChartRegistry.get('bar')
    spec = chart.get_spec(
        data,
        category_col=category_col,
        value_col=value_col,
        **kwargs
    )
    return spec


def map_histogram(letter, data, value_col=None, bins=10, **kwargs):
    """Wrapper de compatibilidad para map_histogram"""
    _deprecation_warning(
        "MatrixLayout.map_histogram()",
        "ChartRegistry.get('histogram').get_spec()"
    )
    
    chart = ChartRegistry.get('histogram')
    spec = chart.get_spec(
        data,
        value_col=value_col,
        bins=bins,
        **kwargs
    )
    return spec


def map_boxplot(letter, data, category_col=None, value_col=None, **kwargs):
    """Wrapper de compatibilidad para map_boxplot"""
    _deprecation_warning(
        "MatrixLayout.map_boxplot()",
        "ChartRegistry.get('boxplot').get_spec()"
    )
    
    chart = ChartRegistry.get('boxplot')
    spec = chart.get_spec(
        data,
        category_col=category_col,
        value_col=value_col,
        **kwargs
    )
    return spec


def map_heatmap(letter, data, x_col=None, y_col=None, value_col=None, **kwargs):
    """Wrapper de compatibilidad para map_heatmap"""
    _deprecation_warning(
        "MatrixLayout.map_heatmap()",
        "ChartRegistry.get('heatmap').get_spec()"
    )
    
    chart = ChartRegistry.get('heatmap')
    spec = chart.get_spec(
        data,
        x_col=x_col,
        y_col=y_col,
        value_col=value_col,
        **kwargs
    )
    return spec


def map_line(letter, data, x_col=None, y_col=None, series_col=None, **kwargs):
    """Wrapper de compatibilidad para map_line"""
    _deprecation_warning(
        "MatrixLayout.map_line()",
        "ChartRegistry.get('line').get_spec()"
    )
    
    chart = ChartRegistry.get('line')
    spec = chart.get_spec(
        data,
        x_col=x_col,
        y_col=y_col,
        series_col=series_col,
        **kwargs
    )
    return spec


def map_pie(letter, data, category_col=None, value_col=None, **kwargs):
    """Wrapper de compatibilidad para map_pie"""
    _deprecation_warning(
        "MatrixLayout.map_pie()",
        "ChartRegistry.get('pie').get_spec()"
    )
    
    chart = ChartRegistry.get('pie')
    spec = chart.get_spec(
        data,
        category_col=category_col,
        value_col=value_col,
        **kwargs
    )
    return spec


def map_grouped_barchart(letter, data, main_col=None, sub_col=None, value_col=None, **kwargs):
    """Wrapper de compatibilidad para map_grouped_barchart"""
    _deprecation_warning(
        "MatrixLayout.map_grouped_barchart()",
        "ChartRegistry.get('grouped_bar').get_spec()"
    )
    
    chart = ChartRegistry.get('grouped_bar')
    spec = chart.get_spec(
        data,
        main_col=main_col,
        sub_col=sub_col,
        value_col=value_col,
        **kwargs
    )
    return spec

