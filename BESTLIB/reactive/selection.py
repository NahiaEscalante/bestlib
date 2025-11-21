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
    ✅ MEJORADO: Validación exhaustiva y mejor manejo de errores.
    
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
    
    # Si ya es un DataFrame, retornar copia
    if HAS_PANDAS and isinstance(items, pd.DataFrame):
        return items.copy()
    
    # Si es None o vacío, retornar DataFrame vacío
    if not items:
        return pd.DataFrame()
    
    # ✅ CORRECCIÓN: Validar que items sea una lista
    if not isinstance(items, list):
        print(f"⚠️ Error: items debe ser lista, recibido: {type(items)}")
        # Intentar convertir de todas formas
        try:
            items = list(items) if hasattr(items, '__iter__') else [items]
        except Exception as e:
            print(f"⚠️ Error al convertir items a lista: {e}")
            return pd.DataFrame()
    
    if len(items) == 0:
        return pd.DataFrame()
    
    # ✅ CORRECCIÓN: Validar que todos los items sean diccionarios
    # Si algunos no lo son, intentar convertirlos o filtrarlos
    valid_items = []
    for i, item in enumerate(items):
        if isinstance(item, dict):
            # Validar que el dict no esté vacío y tenga al menos una key válida
            if item and len(item) > 0:
                valid_items.append(item)
            else:
                print(f"⚠️ Advertencia: Item {i} es un diccionario vacío, omitiendo")
        elif item is None:
            print(f"⚠️ Advertencia: Item {i} es None, omitiendo")
        else:
            # Intentar convertir a dict si es posible
            try:
                if hasattr(item, '__dict__'):
                    valid_items.append(item.__dict__)
                elif hasattr(item, '_asdict'):  # namedtuple
                    valid_items.append(item._asdict())
                else:
                    print(f"⚠️ Advertencia: Item {i} no es diccionario (tipo: {type(item)}), omitiendo")
            except Exception as e:
                print(f"⚠️ Error al convertir item {i} a diccionario: {e}")
    
    if len(valid_items) == 0:
        print("⚠️ Advertencia: No hay items válidos para convertir a DataFrame")
        return pd.DataFrame()
    
    # ✅ CORRECCIÓN: Intentar conversión con mejor manejo de errores
    try:
        df = pd.DataFrame(valid_items)
        
        # Validar que el DataFrame no esté vacío si había items válidos
        if df.empty and len(valid_items) > 0:
            print(f"⚠️ Advertencia: DataFrame resultante está vacío aunque había {len(valid_items)} items válidos")
            # Intentar debug: mostrar primer item
            if len(valid_items) > 0:
                print(f"   Primer item válido: {list(valid_items[0].keys())[:5]}...")
        
        return df
    except Exception as e:
        print(f"⚠️ Error al convertir items a DataFrame: {e}")
        print(f"   Items tipo: {type(items)}, Longitud: {len(items)}")
        if len(valid_items) > 0:
            print(f"   Primer item válido tipo: {type(valid_items[0])}")
            if isinstance(valid_items[0], dict):
                print(f"   Primer item keys: {list(valid_items[0].keys())[:10]}")
        
        # ✅ MEJORADO: Re-raise en modo debug para facilitar debugging
        import sys
        if hasattr(sys, '_getframe') and '--debug' in sys.argv:
            raise
        
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
        ✅ CORRECCIÓN: Ahora maneja DataFrames correctamente.
        
        Args:
            items: Lista de diccionarios, DataFrame de pandas, o None
        """
        # Flag para evitar actualizaciones múltiples simultáneas
        if hasattr(self, '_updating') and self._updating:
            return
        
        self._updating = True
        
        try:
            if items is None:
                items_list = []
            elif HAS_PANDAS and isinstance(items, pd.DataFrame):
                # ✅ CORRECCIÓN CRÍTICA: Convertir DataFrame a lista de diccionarios
                # traitlets.List(Dict()) espera lista de dicts, no DataFrame
                if items.empty:
                    items_list = []
                else:
                    items_list = items.to_dict('records')
            elif isinstance(items, list):
                # ✅ CORRECCIÓN: Validar que todos los elementos sean diccionarios
                items_list = []
                for item in items:
                    if isinstance(item, dict):
                        items_list.append(item)
                    elif HAS_PANDAS and isinstance(item, pd.Series):
                        # Convertir Series a dict
                        items_list.append(item.to_dict())
                    else:
                        # Intentar convertir a dict
                        try:
                            if hasattr(item, '__dict__'):
                                items_list.append(item.__dict__)
                            elif hasattr(item, '_asdict'):
                                items_list.append(item._asdict())
                            else:
                                # Último recurso: crear dict con el item
                                items_list.append({'value': item})
                        except Exception as e:
                            print(f"⚠️ [SelectionModel] Error convirtiendo item a dict: {e}")
                            continue
            else:
                # Intentar convertir a lista
                try:
                    items_list = list(items) if hasattr(items, '__iter__') else [items]
                except Exception:
                    items_list = []
            
            new_count = len(items_list)
            
            # ✅ CORRECCIÓN: Validar que items_list sea lista de diccionarios para traitlets
            # traitlets.List(Dict()) requiere que todos los elementos sean dicts
            valid_items = []
            for item in items_list:
                if isinstance(item, dict):
                    valid_items.append(item)
                else:
                    # Intentar convertir a dict
                    try:
                        if HAS_PANDAS and isinstance(item, pd.Series):
                            valid_items.append(item.to_dict())
                        elif hasattr(item, '__dict__'):
                            valid_items.append(item.__dict__)
                        elif hasattr(item, '_asdict'):
                            valid_items.append(item._asdict())
                        else:
                            # Fallback: crear dict con el valor
                            valid_items.append({'value': item})
                    except Exception:
                        # Si no se puede convertir, omitir
                        continue
            
            # Solo actualizar si hay cambio real (evitar loops infinitos)
            if self.items != valid_items or self.count != len(valid_items):
                self.items = valid_items
                self.count = len(valid_items)
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

