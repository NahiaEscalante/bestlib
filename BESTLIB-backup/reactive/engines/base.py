"""
Base class for communication engines
"""
from abc import ABC, abstractmethod


class CommEngineBase(ABC):
    """
    Clase base abstracta para engines de comunicación.
    Define el contrato que deben cumplir todos los engines.
    """
    
    @property
    @abstractmethod
    def engine_type(self):
        """Tipo de engine ('jupyter', 'colab', 'js-only')"""
        pass
    
    @abstractmethod
    def is_available(self):
        """
        Verifica si el engine está disponible en el entorno actual.
        
        Returns:
            bool: True si está disponible
        """
        pass
    
    @abstractmethod
    def register_comm(self, comm_target="bestlib_matrix"):
        """
        Registra el comm target.
        
        Args:
            comm_target (str): Nombre del comm target
        
        Returns:
            bool: True si el registro fue exitoso
        """
        pass
    
    @abstractmethod
    def send_event(self, div_id, event_type, payload):
        """
        Envía un evento desde JavaScript a Python.
        
        Args:
            div_id (str): ID del div contenedor
            event_type (str): Tipo de evento
            payload (dict): Datos del evento
        """
        pass
    
    @abstractmethod
    def get_js_code(self):
        """
        Retorna el código JavaScript necesario para este engine.
        
        Returns:
            str: Código JavaScript
        """
        pass

