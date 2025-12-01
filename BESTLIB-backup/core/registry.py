"""
Registry global de componentes para BESTLIB
"""


class Registry:
    """
    Registry global para componentes de BESTLIB.
    Permite registrar y descubrir componentes dinámicamente.
    """
    
    _registries = {}  # {type_name: {component_name: component_class}}
    
    @classmethod
    def register(cls, type_name: str, component_name: str, component_class: type):
        """
        Registra un componente.
        
        Args:
            type_name (str): Tipo de componente (ej: 'chart', 'layout')
            component_name (str): Nombre del componente (ej: 'scatter', 'bar')
            component_class (type): Clase del componente
        """
        if type_name not in cls._registries:
            cls._registries[type_name] = {}
        
        cls._registries[type_name][component_name] = component_class
    
    @classmethod
    def get(cls, type_name: str, component_name: str):
        """
        Obtiene un componente registrado.
        
        Args:
            type_name (str): Tipo de componente
            component_name (str): Nombre del componente
        
        Returns:
            type: Clase del componente
        
        Raises:
            ValueError: Si el componente no está registrado
        """
        if type_name not in cls._registries:
            raise ValueError(f"Tipo '{type_name}' no está registrado")
        
        if component_name not in cls._registries[type_name]:
            available = list(cls._registries[type_name].keys())
            raise ValueError(
                f"Componente '{component_name}' no está registrado en '{type_name}'. "
                f"Disponibles: {available}"
            )
        
        return cls._registries[type_name][component_name]
    
    @classmethod
    def list_components(cls, type_name: str):
        """
        Lista todos los componentes de un tipo.
        
        Args:
            type_name (str): Tipo de componente
        
        Returns:
            list: Lista de nombres de componentes
        """
        if type_name not in cls._registries:
            return []
        
        return list(cls._registries[type_name].keys())
    
    @classmethod
    def is_registered(cls, type_name: str, component_name: str) -> bool:
        """
        Verifica si un componente está registrado.
        
        Args:
            type_name (str): Tipo de componente
            component_name (str): Nombre del componente
        
        Returns:
            bool: True si está registrado
        """
        return (
            type_name in cls._registries and
            component_name in cls._registries[type_name]
        )
    
    @classmethod
    def get_all_registries(cls):
        """Retorna todos los registries"""
        return cls._registries.copy()

