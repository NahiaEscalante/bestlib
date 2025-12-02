"""Star Coordinates Chart"""
from .base import ChartBase
from ..core.exceptions import ChartError, DataError

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


class StarCoordinatesChart(ChartBase):
    @property
    def chart_type(self):
        return 'star_coordinates'
    
    def validate_data(self, data, features=None, **kwargs):
        if not features:
            raise ChartError("features es requerido para star coordinates")
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            missing = [f for f in features if f not in data.columns]
            if missing:
                raise DataError(f"Faltan columnas: {missing}")
    
    def prepare_data(self, data, features=None, class_col=None, **kwargs):
        records = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            cols = list(features)
            if class_col:
                cols.append(class_col)
            subset = data[cols].dropna()
            records = subset.to_dict('records')
        else:
            for item in data or []:
                if not all(f in item for f in features):
                    continue
                rec = {f: item[f] for f in features}
                if class_col:
                    rec[class_col] = item.get(class_col)
                records.append(rec)
        return records
    
    def get_spec(self, data, features=None, class_col=None, **kwargs):
        self.validate_data(data, features=features)
        star_data = self.prepare_data(data, features=features, class_col=class_col)
        if not star_data:
            raise ChartError("No se pudieron preparar datos para star coordinates")
        spec = {
            'type': self.chart_type,
            'data': star_data,
            'features': features,
        }
        if class_col:
            spec['class_col'] = class_col
        if kwargs:
            spec['options'] = kwargs
        return spec

