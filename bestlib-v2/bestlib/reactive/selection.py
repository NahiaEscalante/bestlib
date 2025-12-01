"""
Selection Model - Modelo reactivo para selecciones
"""
try:
    import ipywidgets as widgets
    from traitlets import List, Dict, Int, observe
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False
    widgets = None

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


def _items_to_dataframe(items):
    """
    Convierte una lista de diccionarios a un DataFrame de pandas.
    
    Args:
        items: Lista de diccionarios o DataFrame
    
    Returns:
        DataFrame de pandas si items no está vacío, DataFrame vacío si items está vacío,
        o None si pandas no está disponible
    """
    if not HAS_PANDAS:
        if items:
            print("⚠️ Advertencia: pandas no está disponible. Los datos no se pueden convertir a DataFrame.")
        return None
    
    if HAS_PANDAS and isinstance(items, pd.DataFrame):
        return items.copy()
    
    if not items:
        return pd.DataFrame()
    
    try:
        if isinstance(items, list):
            if len(items) == 0:
                return pd.DataFrame()
            if len(items) > 0 and isinstance(items[0], dict):
                return pd.DataFrame(items)
            else:
                return pd.DataFrame(items)
        else:
            return pd.DataFrame([items] if not isinstance(items, (list, tuple)) else items)
    except Exception as e:
        print(f"⚠️ Error al convertir items a DataFrame: {e}")
        return pd.DataFrame()


class ReactiveData(widgets.Widget if HAS_WIDGETS else object):
    """
    Widget reactivo que mantiene datos sincronizados entre celdas.
    
    Uso:
        data = ReactiveData()
        
        # En cualquier celda, puedes observar cambios:
        data.on_change(lambda items, count: print(f"Nuevos datos: {count} items"))
        
        # Desde JavaScript (vía comm):
        data.items = [{'x': 1, 'y': 2}, ...]
        
        # Los observadores se ejecutan automáticamente
    """
    
    if HAS_WIDGETS:
        # Traits que se sincronizan con JavaScript
        items = List(Dict()).tag(sync=True)
        count = Int(0).tag(sync=True)
    
    def __init__(self, **kwargs):
        if HAS_WIDGETS:
            super().__init__(**kwargs)
        else:
            # Fallback si ipywidgets no está disponible
            self.items = kwargs.get('items', [])
            self.count = kwargs.get('count', 0)
        self._callbacks = []
    
    def on_change(self, callback):
        """
        Registra un callback que se ejecuta cuando los datos cambian.
        
        Args:
            callback: Función que recibe (items, count) como argumentos
        """
        # Verificar que el callback no esté ya registrado para evitar duplicados
        callback_id = id(callback)
        for existing_callback in self._callbacks:
            if id(existing_callback) == callback_id:
                return
        self._callbacks.append(callback)
    
    def _items_changed(self, change):
        """Se ejecuta automáticamente cuando items cambia"""
        if isinstance(change, dict):
            new_items = change.get('new', [])
        else:
            new_items = change if not hasattr(change, 'new') else change.new
        
        self.count = len(new_items) if new_items else 0
        
        # Ejecutar callbacks registrados
        callbacks_to_execute = list(self._callbacks)
        for callback in callbacks_to_execute:
            try:
                callback(new_items, self.count)
            except Exception as e:
                print(f"Error en callback: {e}")
    
    if HAS_WIDGETS:
        @observe('items')
        def _observe_items(self, change):
            """Wrapper para traitlets observe"""
            self._items_changed(change)
    
    def update(self, items):
        """
        Actualiza los items manualmente desde Python.
        
        Args:
            items: Lista de items a actualizar
        """
        # Flag para evitar actualizaciones múltiples simultáneas
        if hasattr(self, '_updating') and self._updating:
            return
        
        self._updating = True
        
        try:
            if items is None:
                items = []
            else:
                items = list(items)
            
            new_count = len(items)
            
            # Solo actualizar si hay cambio real (evitar loops infinitos)
            if self.items != items or self.count != new_count:
                self.items = items
                self.count = new_count
                # NOTA: NO llamar callbacks manualmente aquí porque @observe('items') ya los ejecutará
        finally:
            self._updating = False
    
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
    
    def to_dataframe(self):
        """Convierte items a DataFrame de pandas"""
        return _items_to_dataframe(self.items)


class SelectionModel(ReactiveData):
    """
    Modelo reactivo especializado para selecciones de brush.
    
    Uso en BESTLIB:
        selection = SelectionModel()
        
        # Registrar callback
        def on_select(items, count):
            print(f"✅ {count} puntos seleccionados")
            
        selection.on_change(on_select)
        
        # Conectar con MatrixLayout
        layout.connect_selection(selection)
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = []
    
    def _items_changed(self, change):
        """Guarda historial de selecciones"""
        super()._items_changed(change)
        
        if isinstance(change, dict):
            new_items = change.get('new', [])
        else:
            new_items = change if not hasattr(change, 'new') else change.new
        
        if new_items:
            self.history.append({
                'timestamp': self._get_timestamp(),
                'items': new_items,
                'count': len(new_items)
            })
    
    def _get_timestamp(self):
        """Obtiene timestamp actual"""
        import time
        return time.time()
    
    def get_history(self):
        """Retorna el historial de selecciones"""
        return self.history
    
    def clear_history(self):
        """Limpia el historial de selecciones"""
        self.history = []

