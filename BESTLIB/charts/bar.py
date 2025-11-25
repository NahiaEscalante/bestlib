"""
Bar Chart para BESTLIB
"""
from .base import ChartBase
from ..data.preparators import prepare_bar_data
from ..data.validators import validate_bar_data
from ..utils.figsize import process_figsize_in_kwargs
from ..core.exceptions import ChartError, DataError
from typing import Any, Dict, List, Optional


class BarChart(ChartBase):
    """Gráfico de Barras"""
    
    @property
    def chart_type(self):
        return 'bar'
    
    def validate_data(self, data: Any, category_col: Optional[str] = None, **kwargs) -> None:
        """
        Valida datos para bar chart.
        
        Args:
            data: DataFrame o lista de diccionarios
            category_col: Nombre de columna para categorías
            **kwargs: Otros parámetros
        
        Raises:
            ChartError: Si los datos no son válidos o los parámetros son inválidos.
        """
        if data is None:
            raise ChartError("data cannot be None")
        if not isinstance(category_col, str) or not category_col:
            raise ChartError("category_col must be non-empty str")
        
        try:
            validate_bar_data(data, category_col, value_col=kwargs.get('value_col'))
        except DataError as e:
            raise ChartError(f"Datos inválidos para bar chart: {e}")
    
    def prepare_data(self, data: Any, category_col: Optional[str] = None, value_col: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Prepara datos para bar chart.
        
        Args:
            data: DataFrame o lista de diccionarios
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional)
            **kwargs: Otros parámetros
        
        Returns:
            list: Datos preparados para bar chart
        """
        return prepare_bar_data(data, category_col=category_col, value_col=value_col)
    
    def get_spec(self, data: Any, category_col: Optional[str] = None, value_col: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Genera spec para bar chart.
        
        Args:
            data: DataFrame o lista de diccionarios
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional)
            **kwargs: Opciones adicionales
        
        Returns:
            dict: Spec conforme a BESTLIB Visualization Spec
        
        Raises:
            ChartError: Si los datos o parámetros son inválidos.
        """
        if data is None:
            raise ChartError("data cannot be None")
        self.validate_data(data, category_col=category_col, **kwargs)
        bar_data = self.prepare_data(data, category_col=category_col, value_col=value_col, **kwargs)
        
        process_figsize_in_kwargs(kwargs)
        
        if 'xLabel' not in kwargs and category_col:
            kwargs['xLabel'] = category_col
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = value_col if value_col else 'Count'
        
        spec = {
            'type': self.chart_type,
            'data': bar_data,
        }
        
        encoding = {}
        if category_col:
            encoding['x'] = {'field': category_col}
        if value_col:
            encoding['y'] = {'field': value_col}
        
        if encoding:
            spec['encoding'] = encoding
        
        options = {}
        for key in ['color', 'colorMap', 'axes', 'xLabel', 'yLabel', 'figsize', 'interactive']:
            if key in kwargs:
                options[key] = kwargs.pop(key)
        
        if options:
            spec['options'] = options
        
        spec.update(kwargs)
        return spec

