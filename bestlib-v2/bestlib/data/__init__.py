"""
Data module - Procesamiento de datos para BESTLIB
"""
from .preparators import (
    prepare_scatter_data,
    prepare_bar_data,
    prepare_histogram_data,
    prepare_boxplot_data,
    prepare_heatmap_data,
    prepare_line_data,
    prepare_pie_data,
    prepare_grouped_bar_data
)
from .validators import (
    validate_data_structure,
    validate_columns,
    validate_data_types,
    validate_scatter_data,
    validate_bar_data
)
from .transformers import (
    dataframe_to_dicts,
    dicts_to_dataframe,
    normalize_types,
    sanitize_for_json as sanitize_data_for_json
)
from .aggregators import (
    group_by_category,
    bin_numeric_data,
    calculate_statistics
)

__all__ = [
    'prepare_scatter_data',
    'prepare_bar_data',
    'prepare_histogram_data',
    'prepare_boxplot_data',
    'prepare_heatmap_data',
    'prepare_line_data',
    'prepare_pie_data',
    'prepare_grouped_bar_data',
    'validate_data_structure',
    'validate_columns',
    'validate_data_types',
    'validate_scatter_data',
    'validate_bar_data',
    'dataframe_to_dicts',
    'dicts_to_dataframe',
    'normalize_types',
    'sanitize_data_for_json',
    'group_by_category',
    'bin_numeric_data',
    'calculate_statistics'
]

