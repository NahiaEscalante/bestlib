"""
Sistema de Variables Reactivas para BESTLIB
Permite que los datos se actualicen automáticamente sin re-ejecutar celdas
"""

import ipywidgets as widgets
from traitlets import List, Dict, Int, observe


class ReactiveData(widgets.Widget):
    """
    Widget reactivo que mantiene datos sincronizados entre celdas.
    
    Uso:
        data = ReactiveData()
        
        # En cualquier celda, puedes observar cambios:
        data.observe(lambda change: print(f"Nuevos datos: {change['new']}"))
        
        # Desde JavaScript (vía comm):
        data.items = [{'x': 1, 'y': 2}, ...]
        
        # Los observadores se ejecutan automáticamente
    """
    
    # Traits que se sincronizan con JavaScript
    items = List(Dict()).tag(sync=True)
    count = Int(0).tag(sync=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._callbacks = []
    
    def on_change(self, callback):
        """
        Registra un callback que se ejecuta cuando los datos cambian.
        
        Args:
            callback: Función que recibe (items, count) como argumentos
        """
        self._callbacks.append(callback)
    
    @observe('items')
    def _items_changed(self, change):
        """Se ejecuta automáticamente cuando items cambia"""
        new_items = change['new']
        self.count = len(new_items)
        
        # Ejecutar callbacks registrados
        for callback in self._callbacks:
            try:
                callback(new_items, self.count)
            except Exception as e:
                print(f"Error en callback: {e}")
    
    def update(self, items):
        """Actualiza los items manualmente desde Python"""
        self.items = items
        self.count = len(items)
    
    def clear(self):
        """Limpia los datos"""
        self.items = []
        self.count = 0
    
    def get_items(self):
        """Retorna los items actuales"""
        return self.items
    
    def get_count(self):
        """Retorna el número de items"""
        return self.count


class SelectionModel(ReactiveData):
    """
    Modelo reactivo especializado para selecciones de brush.
    
    Uso en BESTLIB:
        selection = SelectionModel()
        
        # Registrar callback
        def on_select(items, count):
            print(f"✅ {count} puntos seleccionados")
            # Hacer análisis automático
            
        selection.on_change(on_select)
        
        # Conectar con MatrixLayout
        layout.connect_selection(selection)
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = []  # Historial de selecciones
    
    @observe('items')
    def _items_changed(self, change):
        """Guarda historial de selecciones"""
        super()._items_changed(change)
        new_items = change['new']
        if new_items:
            self.history.append({
                'timestamp': self._get_timestamp(),
                'items': new_items,
                'count': len(new_items)
            })
    
    def _get_timestamp(self):
        """Retorna timestamp actual"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_history(self):
        """Retorna historial de selecciones"""
        return self.history
    
    def get_last_selection(self):
        """Retorna la última selección"""
        if self.history:
            return self.history[-1]
        return None


def create_reactive_variable(name="data"):
    """
    Factory function para crear variables reactivas rápidamente.
    
    Args:
        name: Nombre de la variable (solo para debugging)
    
    Returns:
        ReactiveData instance
    """
    var = ReactiveData()
    var.name = name
    return var
