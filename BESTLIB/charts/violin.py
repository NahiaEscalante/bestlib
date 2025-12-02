"""Violin Chart"""
from collections import defaultdict

from .base import ChartBase
from ..core.exceptions import ChartError, DataError

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


class ViolinChart(ChartBase):
    @property
    def chart_type(self):
        return 'violin'
    
    def validate_data(self, data, value_col=None, **kwargs):
        if not value_col:
            raise ChartError("value_col es requerido para violin plot")
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if value_col not in data.columns:
                raise DataError(f"Columna '{value_col}' no encontrada en los datos")
    
    def prepare_data(self, data, value_col=None, category_col=None, **kwargs):
        groups = defaultdict(list)
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            cols = [value_col]
            if category_col:
                cols.append(category_col)
            subset = data[cols].dropna()
            for _, row in subset.iterrows():
                cat = row[category_col] if category_col else 'All'
                groups[str(cat)].append(float(row[value_col]))
        else:
            for item in data or []:
                if value_col not in item:
                    continue
                cat = item.get(category_col, 'All') if category_col else 'All'
                try:
                    groups[str(cat)].append(float(item[value_col]))
                except (TypeError, ValueError):
                    continue
        return [{'category': cat, 'values': values} for cat, values in groups.items()]
    
    def get_spec(self, data, value_col=None, category_col=None, **kwargs):
        self.validate_data(data, value_col=value_col, category_col=category_col)
        violin_data = self.prepare_data(data, value_col=value_col, category_col=category_col)
        if not violin_data:
            raise ChartError("No se pudieron preparar datos para violin plot")
        spec = {
            'type': self.chart_type,
            'data': violin_data,
            'value_col': value_col,
        }
        if category_col:
            spec['category_col'] = category_col
        if kwargs:
            spec['options'] = kwargs
        return spec

