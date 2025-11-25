"""
Clase base abstracta para todos los gráficos de BESTLIB
"""
from abc import ABC, abstractmethod
from ..core.exceptions import ChartError


class ChartBase(ABC):
    """
    Clase base abstracta para todos los gráficos.
    Define el contrato que deben cumplir todos los gráficos.
    """
    
    @property
    @abstractmethod
    def chart_type(self):
        """
        Tipo de gráfico.
        
        Returns:
            str: Tipo de gráfico (ej: 'scatter', 'bar')
        """
        pass
    
    @abstractmethod
    def validate_data(self, data, **kwargs):
        """
        Valida que los datos sean adecuados para este gráfico.
        
        Args:
            data: DataFrame o lista de diccionarios
            **kwargs: Parámetros específicos del gráfico
        
        Raises:
            ChartError: Si los datos no son válidos
        """
        pass
    
    @abstractmethod
    def prepare_data(self, data, **kwargs):
        """
        Prepara datos para el gráfico.
        
        Args:
            data: DataFrame o lista de diccionarios
            **kwargs: Parámetros específicos del gráfico
        
        Returns:
            Datos preparados en formato estándar
        """
        pass
    
    @abstractmethod
    def get_spec(self, data, **kwargs):
        """
        Genera la especificación del gráfico (BESTLIB Visualization Spec).
        
        Args:
            data: DataFrame o lista de diccionarios
            **kwargs: Parámetros específicos del gráfico
        
        Returns:
            dict: Spec con 'type', 'data', y opciones
        """
        pass
    
    def get_js_renderer(self) -> str:
        """
        Retorna el nombre de la función JS que renderiza este gráfico.
        
        Returns:
            str: Nombre de función JS (ej: 'renderScatter')
        
        Raises:
            ChartError: Si chart_type no es str no vacío.
        """
        chart_type = self.chart_type
        if not isinstance(chart_type, str) or not chart_type:
            raise ChartError(f"chart_type must be non-empty str, received: {chart_type!r}")
        # Convertir snake_case a PascalCase
        parts = chart_type.split('_')
        pascal_case = ''.join(part.capitalize() for part in parts)
        return f"render{pascal_case}"

