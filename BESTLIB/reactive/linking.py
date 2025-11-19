"""
Link Manager - Gestor de vistas enlazadas para BESTLIB
"""
from ..core.exceptions import BestlibError


class LinkManager:
    """
    Gestor de vistas enlazadas.
    
    Permite conectar múltiples gráficos para que compartan selecciones y estados.
    """
    
    def __init__(self):
        """Inicializa el gestor de enlaces"""
        self._links = {}  # {view_id: [linked_view_ids]}
        self._link_callbacks = {}  # {link_id: callback}
        self._selection_state = {}  # {view_id: selected_items}
    
    def link_views(self, view_id1, view_id2, bidirectional=True):
        """
        Enlaza dos vistas para compartir selecciones.
        
        Args:
            view_id1 (str): ID de la primera vista
            view_id2 (str): ID de la segunda vista
            bidirectional (bool): Si True, el enlace es bidireccional
        """
        if view_id1 not in self._links:
            self._links[view_id1] = []
        if view_id2 not in self._links:
            self._links[view_id2] = []
        
        if view_id2 not in self._links[view_id1]:
            self._links[view_id1].append(view_id2)
        
        if bidirectional and view_id1 not in self._links[view_id2]:
            self._links[view_id2].append(view_id1)
    
    def unlink_views(self, view_id1, view_id2):
        """
        Desenlaza dos vistas.
        
        Args:
            view_id1 (str): ID de la primera vista
            view_id2 (str): ID de la segunda vista
        """
        if view_id1 in self._links:
            if view_id2 in self._links[view_id1]:
                self._links[view_id1].remove(view_id2)
        
        if view_id2 in self._links:
            if view_id1 in self._links[view_id2]:
                self._links[view_id2].remove(view_id1)
    
    def update_selection(self, view_id, selected_items):
        """
        Actualiza la selección de una vista y propaga a vistas enlazadas.
        
        Args:
            view_id (str): ID de la vista
            selected_items: Items seleccionados
        """
        # Guardar estado de selección
        self._selection_state[view_id] = selected_items
        
        # Propagación a vistas enlazadas
        if view_id in self._links:
            for linked_view_id in self._links[view_id]:
                # Evitar propagación circular
                if linked_view_id != view_id:
                    link_id = f"{view_id}->{linked_view_id}"
                    if link_id in self._link_callbacks:
                        try:
                            self._link_callbacks[link_id](linked_view_id, selected_items)
                        except Exception as e:
                            print(f"Error en callback de enlace '{link_id}': {e}")
    
    def register_link_callback(self, view_id1, view_id2, callback):
        """
        Registra un callback para un enlace específico.
        
        Args:
            view_id1 (str): ID de la primera vista
            view_id2 (str): ID de la segunda vista
            callback (callable): Función callback que recibe (view_id, selected_items)
        """
        link_id = f"{view_id1}->{view_id2}"
        self._link_callbacks[link_id] = callback
    
    def get_linked_views(self, view_id):
        """
        Obtiene las vistas enlazadas a una vista.
        
        Args:
            view_id (str): ID de la vista
        
        Returns:
            list: Lista de IDs de vistas enlazadas
        """
        return self._links.get(view_id, []).copy()
    
    def get_selection(self, view_id):
        """
        Obtiene la selección actual de una vista.
        
        Args:
            view_id (str): ID de la vista
        
        Returns:
            Items seleccionados o None
        """
        return self._selection_state.get(view_id)
    
    def clear_selection(self, view_id):
        """Limpia la selección de una vista"""
        if view_id in self._selection_state:
            del self._selection_state[view_id]

