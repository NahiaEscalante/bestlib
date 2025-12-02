"""Parallel Coordinates Chart"""
from .base import ChartBase
from ..core.exceptions import ChartError, DataError

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


class ParallelCoordinatesChart(ChartBase):
    @property
    def chart_type(self):
        return 'parallel_coordinates'
    
    def validate_data(self, data, dimensions=None, **kwargs):
        if not dimensions:
            raise ChartError("dimensions es requerido para parallel coordinates")
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            missing = [d for d in dimensions if d not in data.columns]
            if missing:
                raise DataError(f"Faltan columnas: {missing}")
    
    def prepare_data(self, data, dimensions=None, category_col=None, **kwargs):
        records = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            cols = list(dimensions)
            if category_col:
                cols.append(category_col)
            subset = data[cols].dropna()
            records = subset.to_dict('records')
        else:
            for item in data or []:
                if not all(dim in item for dim in dimensions):
                    continue
                rec = {dim: item[dim] for dim in dimensions}
                if category_col:
                    rec[category_col] = item.get(category_col)
                records.append(rec)
        return records
    
    def get_spec(self, data, dimensions=None, category_col=None, **kwargs):
        self.validate_data(data, dimensions=dimensions)
        parallel_data = self.prepare_data(data, dimensions=dimensions, category_col=category_col)
        if not parallel_data:
            raise ChartError("No se pudieron preparar datos para parallel coordinates")
        spec = {
            'type': self.chart_type,
            'data': parallel_data,
            'dimensions': dimensions,
        }
        if category_col:
            spec['category_col'] = category_col
        if kwargs:
            spec['options'] = kwargs
        return spec

