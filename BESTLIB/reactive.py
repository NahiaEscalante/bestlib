"""
Sistema de Variables Reactivas para BESTLIB
Permite que los datos se actualicen automáticamente sin re-ejecutar celdas
"""

try:
    import ipywidgets as widgets
    from traitlets import List, Dict, Int, observe
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False
    widgets = None
    # Crear stubs para traitlets si no está disponible
    try:
        from traitlets import List, Dict, Int, observe
    except ImportError:
        # Crear stubs funcionales para traitlets
        class _TraitStub:
            def __init__(self, *args, **kwargs):
                self._value = kwargs.get('default', [] if 'List' in str(type(self)) else 0)
            def tag(self, **kwargs):
                return self
            def __call__(self, *args, **kwargs):
                return _TraitStub()
        
        class ListStub(_TraitStub):
            def __call__(self, *args, **kwargs):
                return ListStub()
        
        class DictStub(_TraitStub):
            def __call__(self, *args, **kwargs):
                return DictStub()
        
        class IntStub(_TraitStub):
            def __call__(self, *args, **kwargs):
                return IntStub()
        
        List = ListStub
        Dict = DictStub
        Int = IntStub
        
        def observe(*args, **kwargs):
            def decorator(func):
                return func
            return decorator

# Import de pandas de forma defensiva para evitar errores de importación circular
import sys  # sys siempre está disponible, importarlo fuera del try
HAS_PANDAS = False
pd = None
try:
    # Verificar que pandas no esté parcialmente inicializado
    if 'pandas' in sys.modules:
        # Si pandas ya está en sys.modules pero corrupto, intentar limpiarlo
        try:
            pd_test = sys.modules['pandas']
            # Intentar acceder a un atributo básico para verificar si está corrupto
            _ = pd_test.__version__
        except (AttributeError, ImportError):
            # Pandas está corrupto, limpiarlo
            del sys.modules['pandas']
            # También limpiar submódulos relacionados
            modules_to_remove = [k for k in list(sys.modules.keys()) if k.startswith('pandas.')]
            for mod in modules_to_remove:
                try:
                    del sys.modules[mod]
                except:
                    pass
    
    # Ahora intentar importar pandas
    import pandas as pd
    # Verificar que pandas esté completamente inicializado
    _ = pd.__version__
    HAS_PANDAS = True
except (ImportError, AttributeError, ModuleNotFoundError, Exception):
    # Si pandas no está disponible o está corrupto, continuar sin él
    HAS_PANDAS = False
    pd = None

# Helper function para importar MatrixLayout de forma robusta
def _get_matrix_layout():
    """Importa MatrixLayout de forma robusta (absoluto o relativo)"""
    try:
        from BESTLIB.matrix import MatrixLayout
        return MatrixLayout
    except ImportError:
        try:
            from BESTLIB.layouts.matrix import MatrixLayout
            return MatrixLayout
        except ImportError:
            try:
                from .matrix import MatrixLayout
                return MatrixLayout
            except ImportError:
                try:
                    from .layouts.matrix import MatrixLayout
                    return MatrixLayout
                except ImportError:
                    raise ImportError(
                        "No se pudo importar MatrixLayout. "
                        "Asegúrate de que BESTLIB esté correctamente instalado."
                    )


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
        # Si pandas no está disponible, retornar None y dar warning
        if items:
            print("⚠️ Advertencia: pandas no está disponible. Los datos no se pueden convertir a DataFrame.")
        return None
    
    # Si ya es un DataFrame, retornarlo
    if HAS_PANDAS and isinstance(items, pd.DataFrame):
        return items.copy()
    
    # Si es None o lista vacía, retornar DataFrame vacío
    if not items:
        return pd.DataFrame()
    
    # OPTIMIZACIÓN: Convertir lista de diccionarios a DataFrame de forma más eficiente
    try:
        if isinstance(items, list):
            if len(items) == 0:
                return pd.DataFrame()
            # OPTIMIZACIÓN: Para listas grandes, verificar solo el primer elemento
            # en lugar de todos los elementos
            if len(items) > 0 and isinstance(items[0], dict):
                # Todos parecen ser diccionarios, convertir directamente
                return pd.DataFrame(items)
            else:
                # Si hay items que no son diccionarios, intentar convertir de todas formas
                return pd.DataFrame(items)
        else:
            # Si no es lista ni DataFrame, intentar convertir
            return pd.DataFrame([items] if not isinstance(items, (list, tuple)) else items)
    except Exception as e:
        print(f"⚠️ Error al convertir items a DataFrame: {e}")
        print(f"   Items tipo: {type(items)}, Longitud: {len(items) if hasattr(items, '__len__') else 'N/A'}")
        # En caso de error, retornar DataFrame vacío
        return pd.DataFrame()


class ReactiveData(widgets.Widget if HAS_WIDGETS else object):
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
        # CRÍTICO: Verificar que el callback no esté ya registrado para evitar duplicados
        # Comparar por referencia de función (closure) usando id()
        callback_id = id(callback)
        for existing_callback in self._callbacks:
            if id(existing_callback) == callback_id:
                # Callback ya está registrado, no agregar duplicado
                return
        self._callbacks.append(callback)
    
    @observe('items')
    def _items_changed(self, change):
        """Se ejecuta automáticamente cuando items cambia"""
        new_items = change['new']
        self.count = len(new_items)
        
        # Ejecutar callbacks registrados
        # CRÍTICO: Usar una copia de la lista para evitar problemas si se modifican durante la ejecución
        callbacks_to_execute = list(self._callbacks)
        for callback in callbacks_to_execute:
            try:
                callback(new_items, self.count)
            except Exception as e:
                print(f"Error en callback: {e}")
    
    def update(self, items):
        """Actualiza los items manualmente desde Python"""
        # SIEMPRE mostrar para debugging
        print(f"🟡 [ReactiveData.update] Actualizando ID: {id(self)}")
        print(f"   - Items type: {type(items)}")
        print(f"   - Items count: {len(items) if hasattr(items, '__len__') else '?'}")
        print(f"   - Callbacks registrados: {len(self._callbacks)}")
        
        # CRÍTICO: Flag para evitar actualizaciones múltiples simultáneas
        # PERO: Solo bloquear si realmente hay una actualización en progreso
        # No bloquear si el flag existe pero está en False
        if hasattr(self, '_updating') and self._updating:
            # Ya hay una actualización en progreso, ignorar esta llamada
            print(f"   ⚠️ Actualización ya en progreso, ignorando")
            return
        self._updating = True
        
        try:
            # Convertir a lista si es necesario y asegurar que sea una nueva referencia
            if items is None:
                items = []
            else:
                items = list(items)  # Crear nueva lista para forzar cambio
            
            # Actualizar count primero
            new_count = len(items)
            print(f"   - Nuevo count: {new_count}")
            
            # Solo actualizar si hay cambio real (evitar loops infinitos)
            if self.items != items or self.count != new_count:
                self.items = items
                self.count = new_count
                # NOTA: NO llamar callbacks manualmente aquí porque @observe('items') ya los ejecutará
                # Llamar callbacks manualmente aquí causaría que se ejecuten DOS VECES:
                # 1. Una vez aquí (manual)
                # 2. Una vez en _items_changed() (automático por @observe)
                # Esto es lo que estaba causando la duplicación del boxplot
        finally:
            # CRÍTICO: Resetear flag después de completar, incluso si hay una excepción
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


class ReactiveMatrixLayout:
    """
    Versión reactiva de MatrixLayout que actualiza automáticamente los datos
    e integra LinkedViews dentro de la matriz ASCII.
    
    Uso:
        from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
        import pandas as pd
        
        # Crear modelo de selección
        selection = SelectionModel()
        
        # Crear layout reactivo con vistas enlazadas
        layout = ReactiveMatrixLayout("SB", selection_model=selection)
        
        # Agregar scatter plot (vista principal)
        layout.add_scatter('S', df, x_col='edad', y_col='salario', category_col='dept', interactive=True)
        
        # Agregar bar chart enlazado (se actualiza automáticamente)
        layout.add_barchart('B', category_col='dept')
        
        layout.display()
        
        # Los datos seleccionados contienen filas completas del DataFrame
        selected_rows = selection.get_items()  # Lista de diccionarios con todas las columnas
    """
    
    _debug = False  # Modo debug para ver mensajes detallados
    
    @classmethod
    def set_debug(cls, enabled: bool):
        """
        Activa/desactiva mensajes de debug.
        
        Args:
            enabled (bool): Si True, activa mensajes detallados de debug.
                           Si False, solo muestra errores críticos.
        
        Ejemplo:
            ReactiveMatrixLayout.set_debug(True)  # Activar debug
            layout = ReactiveMatrixLayout("AS\nHX")
            # ... código ...
            ReactiveMatrixLayout.set_debug(False)  # Desactivar debug
        """
        cls._debug = bool(enabled)
    
    def __init__(self, ascii_layout=None, selection_model=None, figsize=None, row_heights=None, col_widths=None, gap=None, cell_padding=None, max_width=None):
        """
        Crea un MatrixLayout con soporte reactivo y LinkedViews integrado.
        
        Args:
            ascii_layout: Layout ASCII (opcional)
            selection_model: Instancia de SelectionModel para reactividad
            figsize: Tamaño global de gráficos (width, height) en pulgadas o píxeles
            row_heights: Lista de alturas por fila (px o fr)
            col_widths: Lista de anchos por columna (px, fr, o ratios)
            gap: Espaciado entre celdas en píxeles (default: 12px)
            cell_padding: Padding de celdas en píxeles (default: 15px)
            max_width: Ancho máximo del layout en píxeles (default: 1200px)
        """
        MatrixLayout = _get_matrix_layout()
        
        # Crear instancia base de MatrixLayout con parámetros de layout
        self._layout = MatrixLayout(
            ascii_layout, 
            figsize=figsize,
            row_heights=row_heights,
            col_widths=col_widths,
            gap=gap,
            cell_padding=cell_padding,
            max_width=max_width
        )
        
        # Modelo reactivo
        self.selection_model = selection_model or SelectionModel()
        
        # Conectar el modelo reactivo
        self._layout.connect_selection(self.selection_model)
        
        # Sistema de vistas enlazadas
        self._views = {}  # {view_id: view_config}
        self._data = None  # DataFrame o lista de diccionarios
        self._selected_data = pd.DataFrame() if HAS_PANDAS else []  # Datos seleccionados actualmente (DataFrame)
        self._view_letters = {}  # {view_id: letter} - mapeo de vista a letra del layout
        self._barchart_callbacks = {}  # {letter: callback_func} - para evitar duplicados
        self._barchart_cell_ids = {}  # {letter: cell_id} - IDs de celdas de bar charts
        self._boxplot_callbacks = {}  # {letter: callback_func} - para evitar duplicados en boxplots
        self._scatter_selection_models = {}  # {scatter_letter: SelectionModel} - Modelos por scatter
        self._barchart_to_scatter = {}  # {barchart_letter: scatter_letter} - Enlaces scatter->bar
        self._linked_charts = {}  # {chart_letter: {'type': str, 'linked_to': str, 'callback': func}} - Gráficos enlazados genéricos
        # Sistema genérico de vistas principales (no solo scatter plots)
        self._primary_view_models = {}  # {view_letter: SelectionModel} - Modelos por vista principal
        self._primary_view_types = {}  # {view_letter: 'scatter'|'barchart'|'histogram'|'grouped_barchart'} - Tipo de vista
        # Sistema para guardar selecciones en variables Python accesibles
        self._selection_variables = {}  # {view_letter: variable_name} - Variables donde guardar selecciones
    
    def set_data(self, data):
        """
        Establece los datos originales para todas las vistas enlazadas.
        
        Args:
            data: DataFrame de pandas o lista de diccionarios
        """
        self._data = data
        return self
    
    def add_scatter(self, letter, data=None, x_col=None, y_col=None, category_col=None, interactive=True, **kwargs):
        """
        Agrega un scatter plot a la matriz con soporte para DataFrames.
        
        Args:
            letter: Letra del layout ASCII donde irá el scatter plot
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            category_col: Nombre de columna para categorías (opcional)
            interactive: Si True, habilita brush selection
            **kwargs: Argumentos adicionales (colorMap, pointRadius, axes, etc.)
        
        Returns:
            self para encadenamiento
        """
        if data is not None:
            self._data = data
        elif self._data is None:
            raise ValueError("Debe proporcionar datos con data= o usar set_data() primero")
        
        # Crear un SelectionModel específico para este scatter plot
        # Esto permite que cada scatter plot actualice solo sus bar charts asociados
        scatter_selection = SelectionModel()
        self._scatter_selection_models[letter] = scatter_selection
        
        # Crear un handler personalizado para este scatter plot específico
        # El handler se conecta directamente al layout principal pero filtra por letra
        MatrixLayout = _get_matrix_layout()
        
        # Crear handler que filtra eventos por letra del scatter
        # Usar closure para capturar la letra
        scatter_letter_capture = letter
        scatter_selection_capture = scatter_selection
        
        def scatter_handler(payload):
            """Handler que actualiza el SelectionModel de este scatter plot Y el modelo principal"""
            # ✅ CORRECCIÓN: Validar items primero
            items = payload.get('items', [])
            if not isinstance(items, list):
                if self._debug or MatrixLayout._debug:
                    print(f"⚠️ [ReactiveMatrixLayout] items no es lista: {type(items)}")
                items = []
            
            # ✅ CORRECCIÓN: Filtrado más flexible
            # Aceptar tanto __scatter_letter__ como __view_letter__ para compatibilidad
            event_scatter_letter = payload.get('__scatter_letter__') or payload.get('__view_letter__')
            if event_scatter_letter is not None and event_scatter_letter != scatter_letter_capture:
                # Este evento no es para este scatter plot, ignorar
                if (self._debug or MatrixLayout._debug) and event_scatter_letter is not None:
                    print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: esperado '{scatter_letter_capture}', recibido '{event_scatter_letter}'")
                return
            
            if self._debug or MatrixLayout._debug:
                print(f"✅ [ReactiveMatrixLayout] Evento recibido para scatter '{scatter_letter_capture}': {len(items)} items")
            
            # ✅ CORRECCIÓN: Validar conversión a DataFrame
            items_df = _items_to_dataframe(items)
            if items_df is None or (hasattr(items_df, 'empty') and items_df.empty and len(items) > 0):
                if self._debug or MatrixLayout._debug:
                    print(f"⚠️ [ReactiveMatrixLayout] Error al convertir {len(items)} items a DataFrame")
                # Continuar con lista como fallback
            
            # ✅ CORRECCIÓN: Usar DataFrame si está disponible, sino lista
            data_to_update = items_df if items_df is not None and not (hasattr(items_df, 'empty') and items_df.empty) else items
            
            # Actualizar el SelectionModel específico de este scatter plot
            # Esto disparará los callbacks registrados (como update_barchart)
            scatter_selection_capture.update(data_to_update)
            
            # IMPORTANTE: También actualizar el selection_model principal para que selected_data se actualice
            # Esto asegura que los datos seleccionados estén disponibles globalmente
            self.selection_model.update(data_to_update)
            
            # Actualizar también _selected_data con DataFrame para que el usuario pueda acceder fácilmente
            self._selected_data = items_df if items_df is not None else items
        
        # Registrar handler en el layout principal
        # Nota: Usamos el mismo layout pero cada scatter tiene su propio SelectionModel
        # El JavaScript enviará __scatter_letter__ en el payload
        self._layout.on('select', scatter_handler)
        
        # Configurar el scatter plot en el mapping
        # IMPORTANTE: Agregar __scatter_letter__ ANTES de crear el spec para asegurar que esté disponible
        kwargs_with_identifier = kwargs.copy()
        kwargs_with_identifier['__scatter_letter__'] = letter
        kwargs_with_identifier['__selection_model_id__'] = id(scatter_selection)
        
        # ✅ CORRECCIÓN: Remover interactive de kwargs si existe para evitar duplicados
        kwargs_with_identifier.pop('interactive', None)  # Remover si existe
        kwargs_with_identifier['interactive'] = interactive  # Agregar el valor correcto
        
        # Crear scatter plot spec con identificadores incluidos
        scatter_spec = MatrixLayout.map_scatter(
            letter, 
            self._data, 
            x_col=x_col, 
            y_col=y_col, 
            category_col=category_col,
            **kwargs_with_identifier  # ✅ interactive ya está aquí
        )
        
        # Asegurar que los identificadores estén en el spec guardado
        if scatter_spec:
            scatter_spec['__scatter_letter__'] = letter
            scatter_spec['__selection_model_id__'] = id(scatter_selection)
            MatrixLayout._map[letter] = scatter_spec
            
            # Debug: verificar que el spec tiene los identificadores
            if self._debug or MatrixLayout._debug:
                print(f"✅ [ReactiveMatrixLayout] Scatter plot '{letter}' configurado con __scatter_letter__={scatter_spec.get('__scatter_letter__')}")
        
        # Registrar vista para sistema de enlace
        view_id = f"scatter_{letter}"
        self._views[view_id] = {
            'type': 'scatter',
            'letter': letter,
            'x_col': x_col,
            'y_col': y_col,
            'category_col': category_col,
            'interactive': interactive,
            'kwargs': kwargs,
            'selection_model': scatter_selection  # Guardar el modelo de selección específico
        }
        self._view_letters[view_id] = letter
        
        return self
    
    def add_barchart(self, letter, category_col=None, value_col=None, linked_to=None, interactive=None, selection_var=None, **kwargs):
        """
        Agrega un bar chart que puede ser vista principal o enlazada.
        
        Args:
            letter: Letra del layout ASCII donde irá el bar chart
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional, si no se especifica cuenta)
            linked_to: Letra de la vista principal que debe actualizar este bar chart (opcional)
                      Si no se especifica y interactive=True, este bar chart será vista principal
            interactive: Si True, permite seleccionar barras. Si es None, se infiere de linked_to
            selection_var: Nombre de variable Python donde guardar selecciones (ej: 'selected_data')
            **kwargs: Argumentos adicionales (color, colorMap, axes, etc.)
        
        Returns:
            self para encadenamiento
        
        Ejemplos:
            # Bar chart como vista principal (genera selecciones)
            layout.add_barchart('B1', category_col='dept', interactive=True, selection_var='my_selection')
            
            # Bar chart enlazado a scatter plot
            layout.add_scatter('S', df, ...)
            layout.add_barchart('B2', category_col='dept', linked_to='S')
            
            # Bar chart enlazado a otro bar chart
            layout.add_barchart('B1', category_col='dept', interactive=True)
            layout.add_barchart('B2', category_col='subcategory', linked_to='B1')
        """
        # Importar MatrixLayout al inicio para evitar UnboundLocalError
        MatrixLayout = _get_matrix_layout()
        
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero para establecer los datos")
        
        # Determinar si será vista principal o enlazada
        if linked_to is None:
            # Si no hay linked_to, NO es vista enlazada
            # Solo es vista principal si interactive=True se especifica EXPLÍCITAMENTE
            if interactive is None:
                # Por defecto, NO interactivo y NO enlazado (gráfico estático)
                interactive = False
                is_primary = False
            else:
                # Si el usuario especificó interactive explícitamente, respetarlo
                is_primary = interactive
        else:
            # Si hay linked_to, es una vista enlazada
            is_primary = False
            if interactive is None:
                interactive = False  # Por defecto, no interactivo si está enlazado
        
        # Si es vista principal, crear su propio SelectionModel
        if is_primary:
            barchart_selection = SelectionModel()
            self._primary_view_models[letter] = barchart_selection
            self._primary_view_types[letter] = 'barchart'
            
            # Guardar variable de selección si se especifica
            if selection_var:
                self._selection_variables[letter] = selection_var
                # Crear variable en el namespace del usuario (inicializar como DataFrame vacío)
                import __main__
                empty_df = pd.DataFrame() if HAS_PANDAS else []
                setattr(__main__, selection_var, empty_df)
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de bar chart '{letter}' como {df_type}")
            
            # Flag para prevenir actualizaciones recursivas del bar chart
            barchart_update_flag = f'_barchart_updating_{letter}'
            if not hasattr(self, '_barchart_update_flags'):
                self._barchart_update_flags = {}
            self._barchart_update_flags[barchart_update_flag] = False
            
            # Crear handler para eventos de selección del bar chart
            def barchart_handler(payload):
                """Handler que actualiza el SelectionModel de este bar chart"""
                # ✅ CORRECCIÓN: Validar items primero
                items = payload.get('items', [])
                if not isinstance(items, list):
                    if self._debug or MatrixLayout._debug:
                        print(f"⚠️ [ReactiveMatrixLayout] items no es lista: {type(items)}")
                    items = []
                
                # ✅ CORRECCIÓN: Filtrado más flexible
                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                if event_letter is not None and event_letter != letter:
                    return
                
                # CRÍTICO: Prevenir procesamiento si estamos actualizando el bar chart
                # Verificar flag de actualización del bar chart
                if self._barchart_update_flags.get(barchart_update_flag, False):
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Bar chart '{letter}' está siendo actualizado, ignorando evento")
                    return
                
                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Evento recibido para bar chart '{letter}': {len(items)} items")
                
                # CRÍTICO: Prevenir actualizaciones recursivas
                # Marcar flag ANTES de actualizar el SelectionModel
                self._barchart_update_flags[barchart_update_flag] = True
                
                try:
                    # ✅ CORRECCIÓN: Validar conversión a DataFrame
                    items_df = _items_to_dataframe(items)
                    if items_df is None or (hasattr(items_df, 'empty') and items_df.empty and len(items) > 0):
                        if self._debug or MatrixLayout._debug:
                            print(f"⚠️ [ReactiveMatrixLayout] Error al convertir {len(items)} items a DataFrame")
                        # Continuar con lista como fallback
                    
                    # ✅ CORRECCIÓN: Usar DataFrame si está disponible, sino lista
                    data_to_update = items_df if items_df is not None and not (hasattr(items_df, 'empty') and items_df.empty) else items
                    
                    # IMPORTANTE: Actualizar el SelectionModel de este bar chart
                    # Esto disparará callbacks registrados (como update_pie para el pie chart 'P')
                    # El callback update_pie NO debe causar que el bar chart se re-renderice
                    barchart_selection.update(data_to_update)
                    
                    # Actualizar también el selection_model principal
                    self.selection_model.update(data_to_update)
                    
                    # Guardar DataFrame en _selected_data para que el usuario pueda acceder fácilmente
                    self._selected_data = items_df if items_df is not None else items
                    
                    # Guardar en variable Python si se especificó (como DataFrame)
                    if selection_var:
                        import __main__
                        # Guardar como DataFrame para facilitar el trabajo del usuario
                        setattr(__main__, selection_var, items_df if items_df is not None else items)
                        if self._debug or MatrixLayout._debug:
                            count_msg = f"{len(items_df)} filas" if items_df is not None and hasattr(items_df, '__len__') else f"{len(items)} items"
                            print(f"💾 Selección guardada en variable '{selection_var}' como DataFrame: {count_msg}")
                finally:
                    # Reset flag después de un delay más largo para evitar bucles
                    # El delay debe ser lo suficientemente largo para que el pie chart termine de actualizarse
                    import threading
                    def reset_flag():
                        import time
                        time.sleep(0.8)  # Delay más largo para evitar bucles (debe ser > delay del pie chart)
                        self._barchart_update_flags[barchart_update_flag] = False
                    threading.Thread(target=reset_flag, daemon=True).start()
            
            # Registrar handler en el layout principal
            self._layout.on('select', barchart_handler)
            
            # Marcar el spec con identificador para enrutamiento
            kwargs['__view_letter__'] = letter
            kwargs['__is_primary_view__'] = True
            kwargs['interactive'] = True  # Forzar interactive para vista principal
        
        # Evitar registrar múltiples callbacks para la misma letra (solo si es enlazada)
        if not is_primary and letter in self._barchart_callbacks:
            if self._debug or MatrixLayout._debug:
                print(f"⚠️ Bar chart para '{letter}' ya está registrado. Ignorando registro duplicado.")
            return self
        
        # Si es vista enlazada, determinar a qué vista principal enlazar
        if not is_primary:
            # CRÍTICO: Si linked_to es None, NO enlazar automáticamente (gráfico estático)
            if linked_to is None:
                # Crear bar chart estático sin enlazar
                MatrixLayout.map_barchart(letter, self._data, category_col=category_col, value_col=value_col, **kwargs)
                return self
            
            # Buscar en scatter plots primero (compatibilidad hacia atrás)
            if linked_to in self._scatter_selection_models:
                primary_letter = linked_to
                primary_selection = self._scatter_selection_models[primary_letter]
            elif linked_to in self._primary_view_models:
                primary_letter = linked_to
                primary_selection = self._primary_view_models[primary_letter]
            else:
                # Si linked_to está especificado pero no existe, lanzar error
                raise ValueError(f"Vista principal '{linked_to}' no existe. Agrega la vista principal primero.")
            
            # Guardar el enlace
            self._barchart_to_scatter[letter] = primary_letter
            
            # Agregar __linked_to__ al spec para indicadores visuales en JavaScript
            kwargs['__linked_to__'] = primary_letter
        
        # Crear bar chart inicial con todos los datos
        MatrixLayout.map_barchart(
            letter,
            self._data,
            category_col=category_col,
            value_col=value_col,
            **kwargs
        )
        
        # Asegurar que __linked_to__ esté en el spec guardado (por si map_barchart no lo copió)
        if not is_primary and linked_to:
            if letter in MatrixLayout._map:
                MatrixLayout._map[letter]['__linked_to__'] = linked_to
        
        # Registrar vista para sistema de enlace
        view_id = f"barchart_{letter}"
        self._views[view_id] = {
            'type': 'barchart',
            'letter': letter,
            'category_col': category_col,
            'value_col': value_col,
            'kwargs': kwargs,
            'is_primary': is_primary
        }
        self._view_letters[view_id] = letter
        
        # Si es vista enlazada, configurar callback de actualización
        if not is_primary and linked_to:
            # Guardar parámetros para el callback (closure)
            barchart_params = {
                'letter': letter,
                'category_col': category_col,
                'value_col': value_col,
                'kwargs': kwargs.copy(),  # Copia para evitar mutaciones
                'layout_div_id': self._layout.div_id
            }
            
            # Debug: verificar que la vista principal existe
            if self._debug or MatrixLayout._debug:
                print(f"🔗 [ReactiveMatrixLayout] Registrando callback para bar chart '{letter}' enlazado a vista principal '{primary_letter}'")
                print(f"   - SelectionModel ID: {id(primary_selection)}")
                print(f"   - Callbacks actuales: {len(primary_selection._callbacks)}")
            
            # Configurar callback para actualizar bar chart cuando cambia selección
            def update_barchart(items, count):
                """Actualiza el bar chart cuando cambia la selección usando JavaScript"""
                try:
                    # Debug: verificar que el callback se está ejecutando
                    if self._debug or MatrixLayout._debug:
                        print(f"🔄 [ReactiveMatrixLayout] Callback ejecutado: Actualizando bar chart '{letter}' con {count} items seleccionados")
                    import json
                    from IPython.display import Javascript
                    import time
                    
                    # Usar datos seleccionados o todos los datos
                    data_to_use = self._data
                    if items and len(items) > 0:
                        # Convertir lista de dicts a DataFrame si es necesario
                        if HAS_PANDAS and isinstance(items[0], dict):
                            import pandas as pd
                            data_to_use = pd.DataFrame(items)
                        else:
                            data_to_use = items
                    else:
                        data_to_use = self._data
                    
                    # Preparar datos del bar chart
                    bar_data = self._prepare_barchart_data(
                        data_to_use, 
                        barchart_params['category_col'], 
                        barchart_params['value_col'],
                        barchart_params['kwargs']
                    )
                    
                    if not bar_data:
                        return
                    
                    # IMPORTANTE: NO actualizar el mapping aquí para evitar bucles infinitos
                    # Solo actualizar visualmente el gráfico con JavaScript
                    # El mapping solo se actualiza cuando es necesario (no en callbacks de actualización)
                    
                    # Crear JavaScript para actualizar el gráfico de forma más robusta
                    div_id = barchart_params['layout_div_id']
                    # Sanitizar para evitar numpy.int64 en JSON
                    bar_data_json = json.dumps(_sanitize_for_json(bar_data))
                    color_map = barchart_params['kwargs'].get('colorMap', {})
                    color_map_json = json.dumps(color_map)
                    default_color = barchart_params['kwargs'].get('color', '#4a90e2')
                    show_axes = barchart_params['kwargs'].get('axes', True)
                    
                    js_update = f"""
                (function() {{
                        // Flag para evitar actualizaciones múltiples simultáneas
                    if (window._bestlib_updating_{letter}) {{
                        return;
                    }}
                    window._bestlib_updating_{letter} = true;
                    
                    // Esperar a que D3 esté disponible con timeout
                    let attempts = 0;
                    const maxAttempts = 50; // 5 segundos máximo
                    
                    function updateBarchart() {{
                        attempts++;
                        if (!window.d3) {{
                            if (attempts < maxAttempts) {{
                            setTimeout(updateBarchart, 100);
                            return;
                            }} else {{
                                console.error('Timeout esperando D3.js');
                                window._bestlib_updating_{letter} = false;
                            return;
                            }}
                        }}
                        
                        const container = document.getElementById('{div_id}');
                        if (!container) {{
                            if (attempts < maxAttempts) {{
                                setTimeout(updateBarchart, 100);
                                return;
                            }} else {{
                                console.warn('No se encontró contenedor {div_id}');
                                window._bestlib_updating_{letter} = false;
                                return;
                            }}
                        }}
                        
                        // Buscar celda por data-letter attribute (más robusto)
                        const cells = container.querySelectorAll('.matrix-cell[data-letter="{letter}"]');
                        let targetCell = null;
                        
                        // Si hay múltiples celdas con la misma letra, buscar la que tiene barras
                        for (let cell of cells) {{
                            const svg = cell.querySelector('svg');
                            if (svg && svg.querySelector('.bar')) {{
                                targetCell = cell;
                                break;
                            }}
                        }}
                        
                        // Si no encontramos, usar la primera celda con la letra
                        if (!targetCell && cells.length > 0) {{
                            targetCell = cells[0];
                        }}
                        
                        if (!targetCell) {{
                            if (attempts < maxAttempts) {{
                                setTimeout(updateBarchart, 100);
                                return;
                            }} else {{
                                console.warn('No se encontró celda para bar chart {letter} después de ' + maxAttempts + ' intentos');
                                window._bestlib_updating_{letter} = false;
                            return;
                            }}
                        }}
                        
                        // CRÍTICO: Calcular dimensiones una sola vez de manera consistente
                        const dims = window.getChartDimensions ? 
                            window.getChartDimensions(targetCell, {{ type: 'barchart' }}, 400, 350) :
                            {{ width: Math.max(targetCell.clientWidth || 400, 200), height: 350 }};
                        const width = dims.width;
                        const height = dims.height;
                        
                        // CRÍTICO: NO limpiar toda la celda si no es necesario
                        // Solo limpiar si es la primera renderización o si realmente es necesario
                        const existingSvg = targetCell.querySelector('svg.bar-chart');
                        const existingBars = targetCell.querySelectorAll('.bar');
                        
                        let svg, g;
                        if (existingSvg && existingBars.length > 0) {{
                            // Usar SVG existente y actualizar solo los datos
                            svg = window.d3.select(existingSvg);
                            g = svg.select('g.chart-group');
                            if (g.empty()) {{
                                // Si no hay grupo, crear uno
                                g = svg.append('g').attr('class', 'chart-group');
                            }}
                        }} else {{
                            // Solo limpiar si no hay SVG existente
                        targetCell.innerHTML = '';
                        
                            svg = window.d3.select(targetCell)
                                .append('svg')
                                .attr('class', 'bar-chart')
                                .attr('width', width)
                                .attr('height', height);
                            
                            g = svg.append('g')
                                .attr('class', 'chart-group');
                        }}
                        const margin = {{ top: 20, right: 20, bottom: 40, left: 50 }};
                        const chartWidth = width - margin.left - margin.right;
                        const chartHeight = height - margin.top - margin.bottom;
                        
                        // Actualizar dimensiones del SVG
                        svg.attr('width', width).attr('height', height);
                        g.attr('transform', `translate(${{margin.left}},${{margin.top}})`);
                        
                        const data = {bar_data_json};
                        const colorMap = {color_map_json};
                        
                        if (data.length === 0) {{
                            if (existingBars.length === 0) {{
                            targetCell.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos</div>';
                            }}
                            window._bestlib_updating_{letter} = false;
                            return;
                        }}
                        
                        const x = window.d3.scaleBand()
                            .domain(data.map(d => d.category))
                            .range([0, chartWidth])
                            .padding(0.2);
                        
                        const y = window.d3.scaleLinear()
                            .domain([0, window.d3.max(data, d => d.value) || 100])
                            .nice()
                            .range([chartHeight, 0]);
                        
                        // Renderizar barras
                        // IMPORTANTE: Preservar los event listeners existentes si es posible
                        // Si las barras ya existen, usar update pattern en lugar de recrear
                        const bars = g.selectAll('.bar')
                            .data(data, d => d.category);  // Usar key function para mantener barras existentes
                        
                        // Remover barras que ya no existen
                        bars.exit().remove();
                        
                        // Agregar nuevas barras
                        const barsEnter = bars.enter()
                            .append('rect')
                            .attr('class', 'bar')
                            .attr('x', d => x(d.category))
                            .attr('y', chartHeight)
                            .attr('width', x.bandwidth())
                            .attr('height', 0)
                            .attr('fill', d => colorMap[d.category] || d.color || '{default_color}')
                            .style('cursor', 'pointer')
                            .on('click', function(event, d) {{
                                // CRÍTICO: Prevenir eventos durante actualización
                                // Verificar flag de actualización del bar chart
                                if (window._bestlib_updating_{letter}) {{
                                    event.stopPropagation();
                                    event.preventDefault();
                                    return false;
                                }}
                                
                                // CRÍTICO: Prevenir eventos si hay una actualización de pie chart en progreso
                                // Verificar flags de actualización de pie charts (pueden estar en otras letras)
                                const pieUpdateFlags = Object.keys(window).filter(key => key.startsWith('_bestlib_updating_pie_'));
                                for (let flag of pieUpdateFlags) {{
                                    if (window[flag]) {{
                                        event.stopPropagation();
                                        event.preventDefault();
                                        return false;
                                    }}
                                }}
                                
                                // IMPORTANTE: Detener propagación inmediatamente para evitar bucles
                                event.stopPropagation();
                                event.preventDefault();
                                
                                // Re-enviar evento con delay para evitar bucles inmediatos
                                const originalRows = d._original_rows || d._original_row || [d];
                                const items = Array.isArray(originalRows) ? originalRows : [originalRows];
                                
                                const viewLetter = '{letter}';
                                
                                // Usar setTimeout para evitar bucles inmediatos
                                setTimeout(() => {{
                                    // Verificar nuevamente antes de enviar el evento
                                    if (window._bestlib_updating_{letter}) {{
                                        return;
                                    }}
                                    
                                    // Verificar flags de actualización de pie charts
                                    const pieUpdateFlags = Object.keys(window).filter(key => key.startsWith('_bestlib_updating_pie_'));
                                    for (let flag of pieUpdateFlags) {{
                                        if (window[flag]) {{
                                            return;
                                        }}
                                    }}
                                    
                                    if (window.sendEvent && typeof window.sendEvent === 'function') {{
                                        window.sendEvent('{div_id}', 'select', {{
                                            type: 'select',
                                            items: items,
                                            indices: [data.indexOf(d)],
                                            original_items: [d],
                                            _original_rows: items,
                                            __view_letter__: viewLetter,
                                            __is_primary_view__: true
                                        }});
                                    }}
                                }}, 150);  // Delay más largo para evitar bucles
                                
                                return false;
                            }});
                        
                        // Actualizar barras existentes y nuevas
                        barsEnter.merge(bars)
                            .transition()
                            .duration(300)  // Transición más rápida para evitar bucles
                            .ease(window.d3.easeCubicOut)
                            .attr('x', d => x(d.category))
                            .attr('width', x.bandwidth())
                            .attr('y', d => y(d.value))
                            .attr('height', d => chartHeight - y(d.value))
                            .attr('fill', d => colorMap[d.category] || d.color || '{default_color}');
                        
                        // Renderizar ejes si se requiere (usar update pattern)
                        if ({str(show_axes).lower()}) {{
                            // Limpiar ejes existentes
                            g.selectAll('.x-axis, .y-axis').remove();
                            
                            const xAxis = g.append('g')
                                .attr('class', 'x-axis')
                                .attr('transform', `translate(0,${{chartHeight}})`)
                                .call(window.d3.axisBottom(x));
                            
                            xAxis.selectAll('text')
                                .style('font-size', '12px')
                                .style('font-weight', '600')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif');
                            
                            xAxis.selectAll('line, path')
                                .style('stroke', '#000000')
                                .style('stroke-width', '1.5px');
                            
                            const yAxis = g.append('g')
                                .attr('class', 'y-axis')
                                .call(window.d3.axisLeft(y).ticks(5));
                            
                            yAxis.selectAll('text')
                                .style('font-size', '12px')
                                .style('font-weight', '600')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif');
                            
                            yAxis.selectAll('line, path')
                                .style('stroke', '#000000')
                                .style('stroke-width', '1.5px');
                        }}
                        
                        // Reset flag al finalizar (con delay para evitar bucles)
                        setTimeout(() => {{
                        window._bestlib_updating_{letter} = false;
                        }}, 300);
                    }}
                    
                    updateBarchart();
                }})();
                """
                    
                    # Ejecutar JavaScript para actualizar solo el bar chart
                    # IMPORTANTE: Usar display_id para que Jupyter reemplace el output anterior
                    # en lugar de crear uno nuevo, lo que previene la duplicación
                    try:
                        from IPython.display import Javascript, display
                        display(Javascript(js_update), clear=False, display_id=f'barchart-update-{letter}', update=True)
                    except:
                        # Fallback si no está disponible
                        pass
                    
                except Exception as e:
                    if self._debug or MatrixLayout._debug:
                        print(f"⚠️ Error actualizando bar chart: {e}")
                        import traceback
                        traceback.print_exc()
                    # Asegurar que el flag se resetee incluso si hay error
                    js_reset_flag = f"""
                    <script>
                    if (window._bestlib_updating_{letter}) {{
                        window._bestlib_updating_{letter} = false;
                    }}
                    </script>
                    """
                    try:
                        from IPython.display import HTML
                        display(HTML(js_reset_flag))
                    except:
                        pass
            
            # Registrar callback en el modelo de selección de la vista principal
            primary_selection.on_change(update_barchart)
            
            # Marcar como callback registrado (solo para vistas enlazadas)
            self._barchart_callbacks[letter] = update_barchart
        
        # NOTA: self._barchart_callbacks[letter] solo se asigna para vistas enlazadas
        # Las vistas principales no necesitan este callback porque manejan sus propios eventos
        
        return self

    def add_grouped_barchart(self, letter, main_col=None, sub_col=None, value_col=None, linked_to=None, interactive=None, selection_var=None, **kwargs):
        """
        Agrega un grouped bar chart que puede ser vista principal o enlazada.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            main_col: Nombre de columna para grupos principales
            sub_col: Nombre de columna para sub-grupos (series)
            value_col: Nombre de columna para valores (opcional, si no se especifica cuenta)
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            interactive: Si True, permite seleccionar barras. Si es None, se infiere de linked_to
            selection_var: Nombre de variable Python donde guardar selecciones
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero")
        if main_col is None or sub_col is None:
            raise ValueError("main_col y sub_col son requeridos")
        
        # Determinar si será vista principal o enlazada
        if linked_to is None:
            # Si no hay linked_to, NO es vista enlazada
            # Solo es vista principal si interactive=True se especifica EXPLÍCITAMENTE
            if interactive is None:
                # Por defecto, NO interactivo y NO enlazado (gráfico estático)
                interactive = False
                is_primary = False
            else:
                # Si el usuario especificó interactive explícitamente, respetarlo
                is_primary = interactive
        else:
            is_primary = False
            if interactive is None:
                interactive = False
        
        # Si es vista principal, crear su propio SelectionModel
        if is_primary:
            grouped_selection = SelectionModel()
            self._primary_view_models[letter] = grouped_selection
            self._primary_view_types[letter] = 'grouped_barchart'
            
            if selection_var:
                self._selection_variables[letter] = selection_var
                import __main__
                empty_df = pd.DataFrame() if HAS_PANDAS else []
                setattr(__main__, selection_var, empty_df)
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de grouped bar chart '{letter}' como {df_type}")
            
            def grouped_handler(payload):
                event_letter = payload.get('__view_letter__')
                if event_letter != letter:
                    return
                
                items = payload.get('items', [])
                
                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Evento recibido para grouped bar chart '{letter}': {len(items)} items")
                
                # Convertir items a DataFrame antes de guardar
                items_df = _items_to_dataframe(items)
                
                grouped_selection.update(items)
                self.selection_model.update(items)
                self._selected_data = items_df if items_df is not None else items
                
                if selection_var:
                    import __main__
                    # Guardar como DataFrame para facilitar el trabajo del usuario
                    setattr(__main__, selection_var, items_df if items_df is not None else items)
                    if self._debug or MatrixLayout._debug:
                        count_msg = f"{len(items_df)} filas" if items_df is not None and hasattr(items_df, '__len__') else f"{len(items)} items"
                        print(f"💾 Selección guardada en variable '{selection_var}' como DataFrame: {count_msg}")
            
            self._layout.on('select', grouped_handler)
            
            kwargs['__view_letter__'] = letter
            kwargs['__is_primary_view__'] = True
            kwargs['interactive'] = True
        
        # Crear gráfico inicial
        MatrixLayout.map_grouped_barchart(letter, self._data, main_col=main_col, sub_col=sub_col, value_col=value_col, **kwargs)
        
        # Si es vista enlazada, configurar callback
        if not is_primary:
            if linked_to in self._scatter_selection_models:
                primary_letter = linked_to
                primary_selection = self._scatter_selection_models[primary_letter]
            elif linked_to in self._primary_view_models:
                primary_letter = linked_to
                primary_selection = self._primary_view_models[primary_letter]
            else:
                all_primary = {**self._scatter_selection_models, **self._primary_view_models}
                if not all_primary:
                    return self
                primary_letter = list(all_primary.keys())[-1]
                primary_selection = all_primary[primary_letter]
                if self._debug or MatrixLayout._debug:
                    print(f"💡 Grouped bar chart '{letter}' enlazado automáticamente a vista principal '{primary_letter}'")
            
            def update(items, count):
                data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
                try:
                    MatrixLayout.map_grouped_barchart(letter, data_to_use, main_col=main_col, sub_col=sub_col, value_col=value_col, **kwargs)
                except Exception:
                    pass
            primary_selection.on_change(update)
        
        return self
    
    def link_chart(self, letter, chart_type, linked_to=None, update_func=None, **kwargs):
        """
        Método genérico para enlazar cualquier tipo de gráfico a un scatter plot.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            chart_type: Tipo de gráfico ('bar', 'histogram', 'pie', 'boxplot', 'heatmap', etc.)
            linked_to: Letra del scatter plot que debe actualizar este gráfico (opcional)
            update_func: Función personalizada para actualizar el gráfico cuando cambia la selección
                       Debe recibir (items, count) como argumentos
            **kwargs: Argumentos adicionales específicos del tipo de gráfico
        
        Returns:
            self para encadenamiento
        
        Ejemplo:
            # Enlazar histograma
            layout.link_chart('H', 'histogram', linked_to='S', 
                             column='edad', bins=10)
            
            # Enlazar pie chart
            layout.link_chart('P', 'pie', linked_to='S',
                             category_col='departamento')
        """
        MatrixLayout = _get_matrix_layout()
        
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero para establecer los datos")
        
        # Determinar a qué scatter plot enlazar
        if linked_to:
            if linked_to not in self._scatter_selection_models:
                raise ValueError(f"Scatter plot '{linked_to}' no existe. Agrega el scatter plot primero.")
            scatter_letter = linked_to
        else:
            # Si no se especifica, usar el último scatter plot agregado
            if not self._scatter_selection_models:
                raise ValueError("No hay scatter plots disponibles. Agrega un scatter plot primero con add_scatter().")
            scatter_letter = list(self._scatter_selection_models.keys())[-1]
            if self._debug or MatrixLayout._debug:
                print(f"💡 Gráfico '{letter}' ({chart_type}) enlazado automáticamente a scatter '{scatter_letter}'")
        
        # Guardar información del gráfico enlazado
        self._linked_charts[letter] = {
            'type': chart_type,
            'linked_to': scatter_letter,
            'kwargs': kwargs.copy(),
            'update_func': update_func
        }
        
        # Crear función de actualización genérica si no se proporciona una personalizada
        if update_func is None:
            def generic_update(items, count):
                """Función genérica de actualización que puede ser extendida"""
                # Por defecto, actualizar el mapping del gráfico
                # Los gráficos específicos pueden sobrescribir este comportamiento
                if self._debug or MatrixLayout._debug:
                    print(f"🔄 Actualizando gráfico '{letter}' ({chart_type}) con {count} elementos seleccionados")
            
            update_func = generic_update
        
        # Registrar callback en el modelo de selección del scatter plot
        scatter_selection = self._scatter_selection_models[scatter_letter]
        scatter_selection.on_change(update_func)
        
        return self
    
    def add_histogram(self, letter, column=None, bins=20, linked_to=None, interactive=None, selection_var=None, **kwargs):
        """
        Agrega un histograma que puede ser vista principal o enlazada.
        
        Args:
            letter: Letra del layout ASCII donde irá el histograma
            column: Nombre de columna numérica para el histograma
            bins: Número de bins (default: 20)
            linked_to: Letra de la vista principal que debe actualizar este histograma (opcional)
                      Si no se especifica y interactive=True, este histograma será vista principal
            interactive: Si True, permite seleccionar bins. Si es None, se infiere de linked_to
            selection_var: Nombre de variable Python donde guardar selecciones (ej: 'selected_bins')
            **kwargs: Argumentos adicionales (color, axes, etc.)
        
        Returns:
            self para encadenamiento
        
        Ejemplos:
            # Histogram como vista principal
            layout.add_histogram('H1', column='age', interactive=True, selection_var='selected_age_range')
            
            # Histogram enlazado a bar chart
            layout.add_barchart('B', category_col='dept', interactive=True)
            layout.add_histogram('H2', column='salary', linked_to='B')
        """
        MatrixLayout = _get_matrix_layout()
        
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero para establecer los datos")
        
        if column is None:
            raise ValueError("Debe especificar 'column' para el histograma")
        
        # Determinar si será vista principal o enlazada
        if linked_to is None:
            # Si no hay linked_to, NO es vista enlazada
            # Solo es vista principal si interactive=True se especifica EXPLÍCITAMENTE
            if interactive is None:
                # Por defecto, NO interactivo y NO enlazado (gráfico estático)
                interactive = False
                is_primary = False
            else:
                # Si el usuario especificó interactive explícitamente, respetarlo
                is_primary = interactive
        else:
            is_primary = False
            if interactive is None:
                interactive = False
        
        # Si es vista principal, crear su propio SelectionModel
        if is_primary:
            histogram_selection = SelectionModel()
            self._primary_view_models[letter] = histogram_selection
            self._primary_view_types[letter] = 'histogram'
            
            # Guardar variable de selección si se especifica
            if selection_var:
                self._selection_variables[letter] = selection_var
                import __main__
                empty_df = pd.DataFrame() if HAS_PANDAS else []
                setattr(__main__, selection_var, empty_df)
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de histogram '{letter}' como {df_type}")
            
            # Crear handler para eventos de selección del histogram
            def histogram_handler(payload):
                """Handler que actualiza el SelectionModel de este histogram"""
                event_letter = payload.get('__view_letter__')
                if event_letter != letter:
                    return
                
                items = payload.get('items', [])
                
                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Evento recibido para histogram '{letter}': {len(items)} items")
                
                # Convertir items a DataFrame antes de guardar
                items_df = _items_to_dataframe(items)
                
                histogram_selection.update(items)
                self.selection_model.update(items)
                self._selected_data = items_df if items_df is not None else items
                
                # Guardar en variable Python si se especificó (como DataFrame)
                if selection_var:
                    import __main__
                    # Guardar como DataFrame para facilitar el trabajo del usuario
                    setattr(__main__, selection_var, items_df if items_df is not None else items)
                    if self._debug or MatrixLayout._debug:
                        count_msg = f"{len(items_df)} filas" if items_df is not None and hasattr(items_df, '__len__') else f"{len(items)} items"
                        print(f"💾 Selección guardada en variable '{selection_var}' como DataFrame: {count_msg}")
            
            self._layout.on('select', histogram_handler)
            
            kwargs['__view_letter__'] = letter
            kwargs['__is_primary_view__'] = True
            kwargs['interactive'] = True
        
        # Si es vista enlazada, determinar a qué vista principal enlazar
        if not is_primary:
            # CRÍTICO: Si linked_to es None, NO enlazar automáticamente (gráfico estático)
            if linked_to is None:
                # Crear histograma estático sin enlazar
                MatrixLayout.map_histogram(letter, self._data, value_col=column, bins=bins, **kwargs)
                return self
            
            # Buscar en scatter plots primero (compatibilidad hacia atrás)
            if linked_to in self._scatter_selection_models:
                primary_letter = linked_to
                primary_selection = self._scatter_selection_models[primary_letter]
            elif linked_to in self._primary_view_models:
                primary_letter = linked_to
                primary_selection = self._primary_view_models[primary_letter]
            else:
                # Si linked_to está especificado pero no existe, lanzar error
                raise ValueError(f"Vista principal '{linked_to}' no existe. Agrega la vista principal primero.")
            
            # Agregar __linked_to__ al spec para indicadores visuales en JavaScript
            kwargs['__linked_to__'] = primary_letter
            
            # Guardar parámetros
            hist_params = {
                'letter': letter,
                'column': column,
                'bins': bins,
                'kwargs': kwargs.copy(),
                'layout_div_id': self._layout.div_id,
                'interactive': interactive  # Guardar si es interactivo
            }
            
            # Función de actualización del histograma
            def update_histogram(items, count):
                """Actualiza el histograma cuando cambia la selección"""
                # CRÍTICO: Importar MatrixLayout al principio para evitar UnboundLocalError
                MatrixLayout = _get_matrix_layout()
                
                # CRÍTICO: Flag para evitar ejecuciones múltiples simultáneas
                if hasattr(update_histogram, '_executing') and update_histogram._executing:
                    if self._debug or MatrixLayout._debug:
                        print(f"   ⏭️ Histogram '{letter}' callback ya está ejecutándose, ignorando llamada duplicada")
                    return
                update_histogram._executing = True
                
                try:
                    import json
                    from IPython.display import Javascript
                    
                    if self._debug or MatrixLayout._debug:
                        print(f"   🔄 Histogram '{letter}' callback ejecutándose con {count} items")
                    
                    # Usar datos seleccionados o todos los datos
                    data_to_use = self._data
                    if items and len(items) > 0:
                        # Procesar items: extraer filas originales si están disponibles
                        processed_items = []
                        for item in items:
                            if isinstance(item, dict):
                                # Verificar si tiene _original_rows (viene de otro gráfico con múltiples filas)
                                if '_original_rows' in item and isinstance(item['_original_rows'], list):
                                    processed_items.extend(item['_original_rows'])
                                # Verificar si tiene _original_row (una sola fila)
                                elif '_original_row' in item:
                                    processed_items.append(item['_original_row'])
                                # Si no tiene _original_row/_original_rows, el item ya es una fila original
                                else:
                                    processed_items.append(item)
                            else:
                                processed_items.append(item)
                        
                        if processed_items:
                            if HAS_PANDAS and isinstance(processed_items[0], dict):
                                import pandas as pd
                                data_to_use = pd.DataFrame(processed_items)
                            else:
                                data_to_use = processed_items
                        else:
                            data_to_use = self._data
                    else:
                        data_to_use = self._data
                    
                    # Preparar datos para histograma
                    # IMPORTANTE: Almacenar filas originales para cada bin
                    if HAS_PANDAS and isinstance(data_to_use, pd.DataFrame):
                        # Obtener valores y filas originales
                        original_data = data_to_use.to_dict('records')
                        values_with_rows = []
                        for row in original_data:
                            val = row.get(column)
                            if val is not None:
                                try:
                                    val_float = float(val)
                                    values_with_rows.append((val_float, row))
                                except Exception:
                                    continue
                        values = [v for v, _ in values_with_rows]
                        rows_by_value = {v: r for v, r in values_with_rows}
                    else:
                        items = data_to_use if isinstance(data_to_use, list) else []
                        values = []
                        rows_by_value = {}
                        for item in items:
                            val = item.get(column)
                            if val is not None:
                                try:
                                    val_float = float(val)
                                    values.append(val_float)
                                    if val_float not in rows_by_value:
                                        rows_by_value[val_float] = []
                                    rows_by_value[val_float].append(item)
                                except Exception:
                                    continue
                    
                    if not values:
                        return
                    
                    # Calcular bins
                    try:
                        import numpy as np
                        hist, bin_edges = np.histogram(values, bins=bins)
                    except ImportError:
                        # Fallback: calcular bins manualmente si numpy no está disponible
                        min_val, max_val = min(values), max(values)
                        bin_width = (max_val - min_val) / bins if max_val > min_val else 1
                        hist = [0] * bins
                        bin_edges = [min_val + i * bin_width for i in range(bins + 1)]
                        
                        for val in values:
                            bin_idx = min(int((val - min_val) / bin_width), bins - 1) if bin_width > 0 else 0
                            hist[bin_idx] += 1
                    
                    # IMPORTANTE: Almacenar filas originales para cada bin
                    bin_rows = [[] for _ in range(len(bin_edges) - 1)]  # Lista de listas para cada bin
                    
                    if HAS_PANDAS and isinstance(data_to_use, pd.DataFrame):
                        # Para DataFrame: almacenar todas las filas originales que caen en cada bin
                        original_data = data_to_use.to_dict('records')
                        for row in original_data:
                            val = row.get(column)
                            if val is not None:
                                try:
                                    val_float = float(val)
                                    # Asignar bin
                                    idx = None
                                    for i in range(len(bin_edges) - 1):
                                        left, right = bin_edges[i], bin_edges[i + 1]
                                        if (val_float >= left and val_float < right) or (i == len(bin_edges) - 2 and val_float == right):
                                            idx = i
                                            break
                                    if idx is not None:
                                        bin_rows[idx].append(row)
                                except Exception:
                                    continue
                    else:
                        # Para lista de dicts: almacenar items originales
                        items = data_to_use if isinstance(data_to_use, list) else []
                        for item in items:
                            val = item.get(column)
                            if val is not None:
                                try:
                                    val_float = float(val)
                                    # Asignar bin
                                    idx = None
                                    for i in range(len(bin_edges) - 1):
                                        left, right = bin_edges[i], bin_edges[i + 1]
                                        if (val_float >= left and val_float < right) or (i == len(bin_edges) - 2 and val_float == right):
                                            idx = i
                                            break
                                    if idx is not None:
                                        bin_rows[idx].append(item)
                                except Exception:
                                    continue
                    
                    bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]
                    
                    # IMPORTANTE: Incluir _original_rows para cada bin
                    hist_data = [
                        {
                            'bin': float(center),
                            'count': int(len(bin_rows[i])),
                            '_original_rows': bin_rows[i]  # Almacenar todas las filas originales de este bin
                        }
                        for i, center in enumerate(bin_centers)
                    ]
                    
                    # IMPORTANTE: NO actualizar el mapping aquí para evitar bucles infinitos
                    # Solo actualizar visualmente el gráfico con JavaScript
                    # El mapping se actualiza cuando se crea inicialmente el histograma
                    # Los _original_rows ya están incluidos en hist_data
                    
                    # JavaScript para actualizar el gráfico (similar a bar chart)
                    div_id = hist_params['layout_div_id']
                    hist_data_json = json.dumps(_sanitize_for_json(hist_data))
                    default_color = kwargs.get('color', '#4a90e2')
                    show_axes = kwargs.get('axes', True)
                    x_label = json.dumps(kwargs.get('xLabel', 'Bin'))
                    y_label = json.dumps(kwargs.get('yLabel', 'Frequency'))
                    
                    js_update = f"""
                (function() {{
                    function updateHistogram() {{
                        if (!window.d3) {{
                            setTimeout(updateHistogram, 100);
                            return;
                        }}
                        
                        const container = document.getElementById('{div_id}');
                        if (!container) return;
                        
                        const cells = container.querySelectorAll('.matrix-cell[data-letter="{letter}"]');
                        let targetCell = null;
                        
                        for (let cell of cells) {{
                            const svg = cell.querySelector('svg');
                            if (svg) {{
                                targetCell = cell;
                                break;
                            }}
                        }}
                        
                        if (!targetCell && cells.length > 0) {{
                            targetCell = cells[0];
                        }}
                        
                        if (!targetCell) return;
                        
                        // CRÍTICO: Obtener dimensiones FIJAS de la celda (definidas por CSS/grid)
                        // NO usar getChartDimensions porque es reactivo y puede cambiar
                        // Usar getBoundingClientRect para obtener el tamaño real del contenedor
                        const cellRect = targetCell.getBoundingClientRect();
                        const cellWidth = cellRect.width || targetCell.clientWidth || 400;
                        const cellHeight = cellRect.height || targetCell.clientHeight || 350;
                        
                        // Guardar dimensiones fijas en la celda para reutilizar en futuras actualizaciones
                        if (!targetCell._fixedDimensions) {{
                            targetCell._fixedDimensions = {{ width: cellWidth, height: cellHeight }};
                        }}
                        
                        // Usar dimensiones fijas guardadas o las actuales
                        let width = targetCell._fixedDimensions.width || cellWidth;
                        let height = targetCell._fixedDimensions.height || cellHeight;
                        
                        // Usar la misma lógica de márgenes que el renderizado inicial
                        const isLargeDashboard = targetCell.closest('.matrix-layout') && 
                                                 targetCell.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
                        const defaultMargin = isLargeDashboard 
                            ? {{ top: 15, right: 15, bottom: 30, left: 35 }}
                            : {{ top: 20, right: 20, bottom: 40, left: 50 }};
                        const specForMargins = {{ xLabel: {x_label}, yLabel: {y_label} }};
                        const margin = window.calculateAxisMargins ? 
                            window.calculateAxisMargins(specForMargins, defaultMargin, width, height) :
                            defaultMargin;
                        
                        // 🔒 CORRECCIÓN: Calcular espacio necesario para etiquetas del eje X ANTES de limpiar
                        // Necesitamos saber si las etiquetas estarán rotadas para calcular el espacio
                        const data = {hist_data_json};
                        let needsRotation = false;
                        let extraHeightForXAxis = 50; // Valor por defecto seguro
                        let maxBinLabelLength = 0; // 🔒 Inicializar para evitar undefined
                        
                        if (data.length > 0) {{
                            const numBins = data.length;
                            maxBinLabelLength = Math.max(...data.map(d => String(d.bin).length), 0);
                            needsRotation = numBins > 8 || maxBinLabelLength > 8;
                            
                            // Calcular espacio adicional basado en si hay rotación
                            // Etiquetas rotadas a -45 grados necesitan más espacio (hasta 60-70px)
                            // Etiquetas normales necesitan menos (25-30px)
                            // + espacio para la etiqueta del eje X (20px)
                            const extraHeightForRotatedLabels = needsRotation ? 60 : 0; // Espacio para etiquetas rotadas (-45 grados)
                            const extraHeightForXAxisLabel = 20; // Espacio para la etiqueta "Sepal Length"
                            extraHeightForXAxis = extraHeightForRotatedLabels + extraHeightForXAxisLabel;
                        }}
                        
                        // CRÍTICO: El SVG debe caber dentro de la celda sin cambiar su tamaño
                        // Usar la altura de la celda como altura máxima del SVG
                        const svgHeight = Math.min(height, cellHeight);
                        
                        // Ajustar chartHeight para que el eje X quepa dentro del SVG
                        // Reducir chartHeight para dejar espacio para el eje X y sus etiquetas
                        let chartHeight = svgHeight - margin.top - margin.bottom - extraHeightForXAxis;
                        let chartWidth = width - margin.left - margin.right;
                        
                        // Asegurar dimensiones mínimas
                        const minChartWidth = 200;
                        const minChartHeight = 150;
                        if (chartWidth < minChartWidth) {{
                            chartWidth = minChartWidth;
                            width = chartWidth + margin.left + margin.right;
                        }}
                        if (chartHeight < minChartHeight) {{
                            // Si no cabe, reducir el espacio extra del eje X
                            const minRequiredHeight = margin.top + margin.bottom + minChartHeight;
                            if (svgHeight >= minRequiredHeight) {{
                                chartHeight = svgHeight - margin.top - margin.bottom;
                                // Ajustar extraHeightForXAxis para que quepa
                                extraHeightForXAxis = Math.max(20, svgHeight - margin.top - margin.bottom - chartHeight);
                            }} else {{
                                chartHeight = minChartHeight;
                            }}
                        }}
                        
                        // CRÍTICO: NO modificar estilos de la celda - mantener tamaño fijo del grid
                        // Limpiar solo el contenido, no cambiar dimensiones
                        targetCell.innerHTML = '';
                        
                        // data ya fue definido arriba para calcular needsRotation
                        
                        if (data.length === 0) {{
                            targetCell.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos</div>';
                            return;
                        }}
                        
                        // 🔒 CORRECCIÓN: Establecer dimensiones fijas en el SVG con viewBox para mejor escalado
                        // IMPORTANTE: Usar overflow: visible para que las etiquetas de ejes se vean
                        // El SVG debe caber dentro de la celda sin cambiar su tamaño
                        const svg = window.d3.select(targetCell)
                            .append('svg')
                            .attr('width', '100%')
                            .attr('height', '100%')
                            .attr('viewBox', `0 0 ${{width}} ${{svgHeight}}`)
                            .attr('preserveAspectRatio', 'xMidYMid meet')
                            .style('max-width', '100%')
                            .style('max-height', '100%')
                            .style('overflow', 'visible')
                            .style('display', 'block');
                        
                        const g = svg.append('g')
                            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
                        
                        // 🔒 CORRECCIÓN: Usar scaleLinear para histograma (los bins son valores numéricos continuos)
                        // Asegurar que los dominios se calculen correctamente incluso con datos extremos
                        const binValues = data.map(d => d.bin).sort((a, b) => a - b);
                        const minBin = binValues.length > 0 ? binValues[0] : 0;
                        const maxBin = binValues.length > 0 ? binValues[binValues.length - 1] : 1;
                        
                        // Calcular el ancho de cada bin basado en la diferencia entre bins consecutivos
                        // Si hay múltiples bins, usar la diferencia promedio; si no, calcular basado en el rango
                        let binSpacing;
                        if (binValues.length > 1) {{
                            // Calcular diferencias entre bins consecutivos y usar el promedio
                            const diffs = [];
                            for (let i = 1; i < binValues.length; i++) {{
                                diffs.push(binValues[i] - binValues[i-1]);
                            }}
                            binSpacing = diffs.reduce((a, b) => a + b, 0) / diffs.length;
                        }} else if (binValues.length === 1) {{
                            // Si solo hay un bin, usar un ancho razonable basado en el valor
                            binSpacing = Math.max(Math.abs(minBin) * 0.1, 1);
                        }} else {{
                            // Si no hay bins, usar un valor por defecto
                            binSpacing = 1;
                        }}
                        
                        // 🔒 CORRECCIÓN: Calcular dominio X asegurando que siempre sea válido
                        const xDomainMin = binValues.length > 0 ? minBin - binSpacing / 2 : 0;
                        const xDomainMax = binValues.length > 0 ? maxBin + binSpacing / 2 : 1;
                        const x = window.d3.scaleLinear()
                            .domain([xDomainMin, xDomainMax])
                            .range([0, chartWidth]);
                        
                        // 🔒 CORRECCIÓN: Calcular dominio Y asegurando que siempre sea válido y visible
                        const maxCount = window.d3.max(data, d => d.count) || 0;
                        // Si maxCount es 0, usar un valor mínimo para que el eje se muestre
                        const yDomainMax = maxCount > 0 ? maxCount : 1;
                        const y = window.d3.scaleLinear()
                            .domain([0, yDomainMax])
                            .nice()
                            .range([chartHeight, 0]);
                        
                        // 🔒 CORRECCIÓN: Calcular el ancho de cada barra en píxeles
                        // Usar el 90% del espaciado para dejar un pequeño gap entre barras
                        // Asegurar que el cálculo no falle incluso con datos extremos
                        let barWidthPixels;
                        if (binValues.length > 0 && binSpacing > 0) {{
                            const nextBinPos = x(minBin + binSpacing);
                            const currentBinPos = x(minBin);
                            barWidthPixels = Math.abs(nextBinPos - currentBinPos);
                        }} else {{
                            // Fallback: usar un ancho basado en el chartWidth
                            barWidthPixels = chartWidth / Math.max(data.length, 1);
                        }}
                        const barWidth = Math.max(barWidthPixels * 0.9, 1); // 90% del ancho para dejar espacio
                        
                        // IMPORTANTE: Agregar event listeners a las barras para interactividad
                        const bars = g.selectAll('.bar')
                            .data(data)
                            .enter()
                            .append('rect')
                            .attr('class', 'bar')
                            .attr('x', d => x(d.bin) - barWidth / 2)
                            .attr('y', chartHeight)
                            .attr('width', barWidth)
                            .attr('height', 0)
                            .attr('fill', '{default_color}')
                            .style('cursor', 'pointer')
                            .on('click', function(event, d) {{
                                // IMPORTANTE: Enviar todas las filas originales que corresponden a este bin
                                const originalRows = d._original_rows || d._original_row || (d._original_row ? [d._original_row] : null) || [];
                                
                                // Asegurar que originalRows sea un array
                                const items = Array.isArray(originalRows) && originalRows.length > 0 ? originalRows : [];
                                
                                // Si no hay filas originales, intentar enviar al menos información del bin
                                if (items.length === 0) {{
                                    console.warn(`[Histogram] No se encontraron filas originales para el bin ${{d.bin}}. Asegúrese de que los datos se prepararon correctamente.`);
                                    items.push({{ bin: d.bin, count: d.count }});
                                }}
                                
                                // Obtener letra de la vista
                                const viewLetter = '{letter}';
                                if (window.sendEvent && typeof window.sendEvent === 'function') {{
                                    window.sendEvent('{div_id}', 'select', {{
                                        type: 'select',
                                        items: items,  // Enviar todas las filas originales de este bin
                                        indices: [],
                                        original_items: [d],
                                        _original_rows: items,  // También incluir como _original_rows para compatibilidad
                                        __view_letter__: viewLetter,
                                        __is_primary_view__: false  // Histogram enlazado no es vista principal
                                    }});
                                }}
                            }})
                            .transition()
                            .duration(500)
                            .attr('y', d => y(d.count))
                            .attr('height', d => chartHeight - y(d.count));
                        
                        if ({str(show_axes).lower()}) {{
                            // 🔒 CORRECCIÓN: Detectar si necesitamos rotar etiquetas del eje X (ya calculado arriba)
                            const rotationAngle = needsRotation ? -45 : 0;
                            const numBins = data.length;
                            
                            // 🔒 CORRECCIÓN: Eje X - Asegurar que se muestre con valores y formato correcto
                            const xAxis = g.append('g')
                                .attr('class', 'x-axis')
                                .attr('transform', `translate(0,${{chartHeight}})`);
                            
                            // 🔒 CORRECCIÓN: Calcular número de ticks apropiado (máximo 10 para no saturar)
                            const numXTicks = Math.min(numBins, 10);
                            // Asegurar que maxBinLabelLength esté definido
                            const safeMaxBinLabelLength = maxBinLabelLength || 6;
                            const xAxisGenerator = window.d3.axisBottom(x)
                                .ticks(numXTicks)
                                .tickFormat(d => {{
                                    // Formato más corto para números largos
                                    if (typeof d === 'number') {{
                                        if (d % 1 === 0) return d.toString();
                                        return d.toFixed(safeMaxBinLabelLength > 6 ? 1 : 2);
                                    }}
                                    return String(d);
                                }});
                            
                            xAxis.call(xAxisGenerator);
                            
                            // Estilizar etiquetas del eje X
                            xAxis.selectAll('text')
                                .style('font-size', needsRotation ? '10px' : '11px')
                                .style('font-weight', '600')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif')
                                .attr('transform', rotationAngle !== 0 ? `rotate(${{rotationAngle}})` : null)
                                .style('text-anchor', rotationAngle !== 0 ? 'end' : 'middle')
                                .attr('dx', rotationAngle !== 0 ? '-0.5em' : '0')
                                .attr('dy', rotationAngle !== 0 ? '0.5em' : '0.7em')
                                .style('opacity', 1);  // 🔒 Asegurar que sean visibles
                            
                            // Estilizar líneas del eje X
                            xAxis.selectAll('line, path')
                                .style('stroke', '#000000')
                                .style('stroke-width', '1.5px')
                                .style('opacity', 1);  // 🔒 Asegurar que sean visibles
                            
                            // 🔒 CORRECCIÓN: Eje Y - Asegurar que se muestre con valores y formato correcto
                            const yAxis = g.append('g')
                                .attr('class', 'y-axis');
                            
                            const yAxisGenerator = window.d3.axisLeft(y)
                                .ticks(5)
                                .tickFormat(window.d3.format('d'));  // Formato numérico para el eje Y
                            
                            yAxis.call(yAxisGenerator);
                            
                            // Estilizar etiquetas del eje Y
                            yAxis.selectAll('text')
                                .style('font-size', '12px')
                                .style('font-weight', '600')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif')
                                .style('opacity', 1);  // 🔒 Asegurar que sean visibles
                            
                            // Estilizar líneas del eje Y
                            yAxis.selectAll('line, path')
                                .style('stroke', '#000000')
                                .style('stroke-width', '1.5px')
                                .style('opacity', 1);  // 🔒 Asegurar que sean visibles
                            
                            // Renderizar etiquetas de ejes
                            // Etiqueta del eje X (debajo del gráfico)
                            // CRÍTICO: Asegurar que la etiqueta quede dentro del SVG
                            const xLabelX = chartWidth / 2;
                            // Posicionar la etiqueta dentro del espacio disponible del SVG
                            // chartHeight + margin.bottom es donde termina el área del gráfico
                            // Usar el espacio calculado en extraHeightForXAxis
                            const spaceForRotatedLabels = needsRotation ? 45 : 0;
                            // Asegurar que xLabelY no exceda svgHeight - margin.top
                            const maxYLabelPosition = svgHeight - margin.top - 5; // 5px de margen de seguridad
                            const xLabelY = Math.min(
                                chartHeight + margin.bottom + spaceForRotatedLabels + 15,
                                maxYLabelPosition
                            );
                            
                            const xLabelText = g.append('text')
                                .attr('x', xLabelX)
                                .attr('y', xLabelY)
                                .attr('text-anchor', 'middle')
                                .style('font-size', '13px')
                                .style('font-weight', '700')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif')
                                .text({x_label});
                            
                            // Etiqueta del eje Y (a la izquierda del gráfico, rotada -90 grados)
                            const yLabelX = margin.left / 2;
                            const yLabelY = margin.top + chartHeight / 2;
                            
                            const yLabelText = svg.append('text')
                                .attr('x', yLabelX)
                                .attr('y', yLabelY)
                                .attr('text-anchor', 'middle')
                                .attr('dominant-baseline', 'central')
                                .style('font-size', '13px')
                                .style('font-weight', '700')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif')
                                .style('pointer-events', 'none')
                                .attr('transform', `rotate(-90 ${{yLabelX}} ${{yLabelY}})`)
                                .text({y_label});
                        }}
                        
                        // Renderizar título del gráfico si está especificado
                        const title = '{kwargs.get("title", "")}';
                        if (title && title.trim() !== '') {{
                            const titleFontSize = {kwargs.get("titleFontSize", 16)};
                            const titleY = margin.top - 10;
                            const titleX = chartWidth / 2;
                            
                            svg.append('text')
                                .attr('x', titleX + margin.left)
                                .attr('y', titleY)
                                .attr('text-anchor', 'middle')
                                .style('font-size', titleFontSize + 'px')
                                .style('font-weight', '700')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif')
                                .text(title);
                        }}
                    }}
                    
                    updateHistogram();
                }})();
                """
                    
                    # IMPORTANTE: Usar display_id para que Jupyter reemplace el output anterior
                    # en lugar de crear uno nuevo, lo que previene la duplicación
                    try:
                        from IPython.display import Javascript, display
                        display(Javascript(js_update), clear=False, display_id=f'histogram-update-{letter}', update=True)
                    except:
                        pass
                    
                except Exception as e:
                    # MatrixLayout ya está importado al principio de la función
                    if self._debug or MatrixLayout._debug:
                        print(f"⚠️ Error actualizando histograma: {e}")
                        import traceback
                        traceback.print_exc()
                finally:
                    # CRÍTICO: Resetear flag después de completar
                    update_histogram._executing = False
                    if self._debug or MatrixLayout._debug:
                        print(f"   ✅ Histogram '{letter}' callback completado")
            
            # Registrar callback en el modelo de selección de la vista principal
            primary_selection.on_change(update_histogram)
        
        # Crear histograma inicial con todos los datos
        MatrixLayout.map_histogram(letter, self._data, value_col=column, bins=bins, **kwargs)
        
        # Asegurar que __linked_to__ esté en el spec guardado (por si map_histogram no lo copió)
        if not is_primary and linked_to:
            if letter in MatrixLayout._map:
                MatrixLayout._map[letter]['__linked_to__'] = linked_to
        
        return self
    
    def add_boxplot(self, letter, column=None, category_col=None, linked_to=None, **kwargs):
        """
        Agrega un boxplot enlazado que se actualiza automáticamente cuando se selecciona en scatter.
        
        Args:
            letter: Letra del layout ASCII donde irá el boxplot
            column: Nombre de columna numérica para el boxplot
            category_col: Nombre de columna de categorías (opcional, para boxplot por categoría)
            linked_to: Letra del scatter plot que debe actualizar este boxplot (opcional)
            **kwargs: Argumentos adicionales (color, axes, etc.)
        
        Returns:
            self para encadenamiento
        """
        MatrixLayout = _get_matrix_layout()
        
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero para establecer los datos")
        
        if column is None:
            raise ValueError("Debe especificar 'column' para el boxplot")
        
        # Verificar si ya existe un callback para este boxplot (evitar duplicados)
        if letter in self._boxplot_callbacks:
            if self._debug or MatrixLayout._debug:
                print(f"⚠️ Boxplot para '{letter}' ya está registrado. Ignorando registro duplicado.")
            return self
        
        # Determinar a qué vista principal enlazar
        if linked_to:
            # Buscar en scatter plots primero (compatibilidad hacia atrás)
            if linked_to in self._scatter_selection_models:
                primary_letter = linked_to
                primary_selection = self._scatter_selection_models[primary_letter]
            elif linked_to in self._primary_view_models:
                primary_letter = linked_to
                primary_selection = self._primary_view_models[primary_letter]
            else:
                raise ValueError(f"Vista principal '{linked_to}' no existe. Vistas disponibles: scatter plots {list(self._scatter_selection_models.keys())}, vistas principales {list(self._primary_view_models.keys())}")
        else:
            # Si no se especifica, usar la última vista principal disponible
            all_primary = {**self._scatter_selection_models, **self._primary_view_models}
            if not all_primary:
                raise ValueError("No hay vistas principales disponibles. Agrega una vista principal primero (scatter, bar chart, etc.)")
            primary_letter = list(all_primary.keys())[-1]
            primary_selection = all_primary[primary_letter]
            if self._debug or MatrixLayout._debug:
                print(f"💡 Boxplot '{letter}' enlazado automáticamente a vista principal '{primary_letter}'")
        
        # Agregar __linked_to__ al spec para indicadores visuales en JavaScript
        if linked_to:
            kwargs['__linked_to__'] = primary_letter
        elif not linked_to and 'primary_letter' in locals():
            kwargs['__linked_to__'] = primary_letter
        
        # Guardar parámetros
        boxplot_params = {
            'letter': letter,
            'column': column,
            'category_col': category_col,
            'kwargs': kwargs.copy(),
            'layout_div_id': self._layout.div_id
        }
        
        # Función de actualización del boxplot
        def update_boxplot(items, count):
            """Actualiza el boxplot cuando cambia la selección"""
            # CRÍTICO: Importar MatrixLayout al principio para evitar UnboundLocalError
            MatrixLayout = _get_matrix_layout()
            
            # CRÍTICO: Flag para evitar ejecuciones múltiples simultáneas
            if hasattr(update_boxplot, '_executing') and update_boxplot._executing:
                if self._debug or MatrixLayout._debug:
                    print(f"   ⏭️ Boxplot '{letter}' callback ya está ejecutándose, ignorando llamada duplicada")
                return
            update_boxplot._executing = True
            
            try:
                import json
                from IPython.display import Javascript
                
                if self._debug or MatrixLayout._debug:
                    print(f"   🔄 Boxplot '{letter}' callback ejecutándose con {count} items")
                
                # Usar datos seleccionados o todos los datos
                # Si los items tienen _original_row, usar esos datos
                data_to_use = self._data
                if items and len(items) > 0:
                    # Extraer datos originales si están disponibles
                    processed_items = []
                    for item in items:
                        if isinstance(item, dict):
                            # Si tiene _original_row, usar esos datos
                            if '_original_row' in item:
                                processed_items.append(item['_original_row'])
                            elif '_original_rows' in item:
                                # Si hay múltiples filas originales
                                processed_items.extend(item['_original_rows'])
                            else:
                                processed_items.append(item)
                    
                    if processed_items:
                        if HAS_PANDAS and isinstance(processed_items[0], dict):
                            import pandas as pd
                            data_to_use = pd.DataFrame(processed_items)
                        else:
                            data_to_use = processed_items
                    else:
                        # Si no hay items procesados, usar todos los datos
                        data_to_use = self._data
                
                # Preparar datos para boxplot
                if HAS_PANDAS and isinstance(data_to_use, pd.DataFrame):
                    if category_col and category_col in data_to_use.columns:
                        # Boxplot por categoría
                        box_data = []
                        for cat in data_to_use[category_col].unique():
                            cat_data = data_to_use[data_to_use[category_col] == cat][column].dropna()
                            if len(cat_data) > 0:
                                q1 = cat_data.quantile(0.25)
                                median = cat_data.quantile(0.5)
                                q3 = cat_data.quantile(0.75)
                                iqr = q3 - q1
                                lower = max(q1 - 1.5 * iqr, cat_data.min())
                                upper = min(q3 + 1.5 * iqr, cat_data.max())
                                box_data.append({
                                    'category': cat,
                                    'q1': float(q1),
                                    'median': float(median),
                                    'q3': float(q3),
                                    'lower': float(lower),
                                    'upper': float(upper),
                                    'min': float(cat_data.min()),
                                    'max': float(cat_data.max())
                                })
                    else:
                        # Boxplot simple
                        values = data_to_use[column].dropna()
                        if len(values) > 0:
                            q1 = values.quantile(0.25)
                            median = values.quantile(0.5)
                            q3 = values.quantile(0.75)
                            iqr = q3 - q1
                            lower = max(q1 - 1.5 * iqr, values.min())
                            upper = min(q3 + 1.5 * iqr, values.max())
                            box_data = [{
                                'category': 'All',
                                'q1': float(q1),
                                'median': float(median),
                                'q3': float(q3),
                                'lower': float(lower),
                                'upper': float(upper),
                                'min': float(values.min()),
                                'max': float(values.max())
                            }]
                        else:
                            box_data = []
                else:
                    # Fallback para listas de diccionarios
                    values = [item.get(column, 0) for item in data_to_use if column in item]
                    if values:
                        sorted_vals = sorted(values)
                        n = len(sorted_vals)
                        q1 = sorted_vals[int(n * 0.25)]
                        median = sorted_vals[int(n * 0.5)]
                        q3 = sorted_vals[int(n * 0.75)]
                        iqr = q3 - q1
                        lower = max(q1 - 1.5 * iqr, min(values))
                        upper = min(q3 + 1.5 * iqr, max(values))
                        box_data = [{
                            'category': 'All',
                            'q1': float(q1),
                            'median': float(median),
                            'q3': float(q3),
                            'lower': float(lower),
                            'upper': float(upper),
                            'min': float(min(values)),
                            'max': float(max(values))
                        }]
                    else:
                        box_data = []
                
                if not box_data:
                    return
                
                # IMPORTANTE: NO actualizar el mapping aquí para evitar bucles infinitos y re-renderización del layout completo
                # Solo actualizar visualmente el gráfico con JavaScript
                # El mapping se actualiza cuando se crea inicialmente el boxplot
                # Actualizar el mapping global causa que el sistema detecte cambios y re-renderice todo el layout,
                # lo que resulta en duplicación de gráficos, especialmente en layouts grandes (3x3, etc.)
                
                # JavaScript para actualizar el gráfico
                div_id = boxplot_params['layout_div_id']
                box_data_json = json.dumps(_sanitize_for_json(box_data))
                default_color = kwargs.get('color', '#4a90e2')
                show_axes = kwargs.get('axes', True)
                x_label = json.dumps(kwargs.get('xLabel', 'Category'))
                y_label = json.dumps(kwargs.get('yLabel', 'Value'))
                
                js_update = f"""
                (function() {{
                    // Flag para evitar actualizaciones múltiples simultáneas
                    if (window._bestlib_updating_boxplot_{letter}) {{
                        return;
                    }}
                    window._bestlib_updating_boxplot_{letter} = true;
                    
                    function updateBoxplot() {{
                        if (!window.d3) {{
                            setTimeout(updateBoxplot, 100);
                            return;
                        }}
                        
                        const container = document.getElementById('{div_id}');
                        if (!container) {{
                            window._bestlib_updating_boxplot_{letter} = false;
                            return;
                        }}
                        
                        const cells = container.querySelectorAll('.matrix-cell[data-letter="{letter}"]');
                        let targetCell = null;
                        
                        // Buscar celda con SVG existente (más robusto)
                        for (let cell of cells) {{
                            const svg = cell.querySelector('svg');
                            if (svg) {{
                                targetCell = cell;
                                break;
                            }}
                        }}
                        
                        // Si no encontramos, usar la primera celda
                        if (!targetCell && cells.length > 0) {{
                            targetCell = cells[0];
                        }}
                        
                        if (!targetCell) {{
                            window._bestlib_updating_boxplot_{letter} = false;
                            return;
                        }}
                        
                        // CRÍTICO: Solo limpiar el contenido de la celda, NO tocar el contenedor principal
                        // Esto evita que se dispare un re-render del layout completo
                        // IMPORTANTE: Desconectar ResizeObserver temporalmente para evitar re-renders
                        if (targetCell._resizeObserver) {{
                            targetCell._resizeObserver.disconnect();
                        }}
                        
                        // En lugar de usar innerHTML = '', removemos solo el SVG existente
                        const existingSvg = targetCell.querySelector('svg');
                        if (existingSvg) {{
                            existingSvg.remove();
                        }}
                        // Limpiar cualquier otro contenido visual (divs, etc.) pero mantener la estructura de la celda
                        const otherContent = targetCell.querySelectorAll('div:not(.matrix-cell)');
                        otherContent.forEach(el => el.remove());
                        
                        // NO reconectar el ResizeObserver aquí - se reconectará después de renderizar si es necesario
                        
                        // CRÍTICO: Obtener dimensiones FIJAS de la celda (definidas por CSS/grid)
                        // NO usar getChartDimensions porque es reactivo y puede cambiar
                        // Usar getBoundingClientRect para obtener el tamaño real del contenedor
                        const cellRect = targetCell.getBoundingClientRect();
                        const cellWidth = cellRect.width || targetCell.clientWidth || 400;
                        const cellHeight = cellRect.height || targetCell.clientHeight || 350;
                        
                        // Guardar dimensiones fijas en la celda para reutilizar en futuras actualizaciones
                        if (!targetCell._fixedDimensions) {{
                            targetCell._fixedDimensions = {{ width: cellWidth, height: cellHeight }};
                        }}
                        
                        // Usar dimensiones fijas guardadas o las actuales
                        let width = targetCell._fixedDimensions.width || cellWidth;
                        let height = targetCell._fixedDimensions.height || cellHeight;
                        
                        // 🔒 CORRECCIÓN: Usar márgenes con padding adicional para el eje Y (evitar superposición)
                        const isLargeDashboard = targetCell.closest('.matrix-layout') && 
                                                 targetCell.closest('.matrix-layout').querySelectorAll('.matrix-cell').length >= 9;
                        // Aumentar margen izquierdo para separar el eje Y de los datos
                        const defaultMargin = isLargeDashboard 
                            ? {{ top: 15, right: 15, bottom: 30, left: 50 }}  // Aumentado de 35 a 50
                            : {{ top: 20, right: 20, bottom: 40, left: 60 }}; // Aumentado de 50 a 60
                        const specForMargins = {{ xLabel: {x_label}, yLabel: {y_label} }};
                        const margin = window.calculateAxisMargins ? 
                            window.calculateAxisMargins(specForMargins, defaultMargin, width, height) :
                            defaultMargin;
                        // 🔒 Asegurar que el margen izquierdo tenga mínimo suficiente para evitar superposición
                        margin.left = Math.max(margin.left, isLargeDashboard ? 50 : 60);
                        
                        // IMPORTANTE: Calcular espacio necesario para etiquetas del eje X ANTES de limpiar
                        // Necesitamos saber si las etiquetas estarán rotadas para calcular el espacio
                        const data = {box_data_json};
                        let needsRotation = false;
                        let extraHeightForXAxis = 50; // Valor por defecto seguro
                        
                        if (data.length > 0) {{
                            // Para boxplot, las etiquetas de categorías pueden ser largas
                            const maxCategoryLength = Math.max(...data.map(d => String(d.category).length), 0);
                            needsRotation = data.length > 3 || maxCategoryLength > 10;
                            
                            // Calcular espacio adicional basado en si hay rotación
                            // Etiquetas rotadas a -45 grados necesitan más espacio (hasta 60-70px)
                            // Etiquetas normales necesitan menos (25-30px)
                            // + espacio para la etiqueta del eje X (20px)
                            const extraHeightForRotatedLabels = needsRotation ? 60 : 0; // Espacio para etiquetas rotadas (-45 grados)
                            const extraHeightForXAxisLabel = 20; // Espacio para la etiqueta "Species"
                            extraHeightForXAxis = extraHeightForRotatedLabels + extraHeightForXAxisLabel;
                        }}
                        
                        // 🔒 CORRECCIÓN: Calcular svgHeight asegurando que incluya espacio para el eje X
                        // El SVG debe incluir el espacio para etiquetas rotadas y labels
                        const baseHeight = Math.min(height, cellHeight);
                        const svgHeight = baseHeight;
                        
                        // 🔒 CORRECCIÓN: Calcular chartHeight asegurando que el eje X quepa dentro del SVG
                        // Reducir chartHeight para dejar espacio para el eje X y sus etiquetas
                        let chartHeight = svgHeight - margin.top - margin.bottom - extraHeightForXAxis;
                        let chartWidth = width - margin.left - margin.right;
                        
                        // 🔒 CORRECCIÓN: Asegurar dimensiones mínimas y que todo quepa dentro del SVG
                        const minChartWidth = 200;
                        const minChartHeight = 150;
                        if (chartWidth < minChartWidth) {{
                            chartWidth = minChartWidth;
                            width = chartWidth + margin.left + margin.right;
                        }}
                        // Asegurar que chartHeight sea válido y que el eje X quepa
                        if (chartHeight < minChartHeight) {{
                            // Si no cabe, ajustar para que quepa el mínimo pero sin salirse del SVG
                            const minRequiredHeight = margin.top + margin.bottom + minChartHeight + extraHeightForXAxis;
                            if (svgHeight >= minRequiredHeight) {{
                                chartHeight = svgHeight - margin.top - margin.bottom - extraHeightForXAxis;
                            }} else {{
                                // Si aún no cabe, reducir extraHeightForXAxis pero mantener mínimo
                                const availableHeight = svgHeight - margin.top - margin.bottom;
                                chartHeight = Math.max(minChartHeight, availableHeight - extraHeightForXAxis);
                                // Ajustar extraHeightForXAxis para que quepa
                                extraHeightForXAxis = Math.max(20, availableHeight - chartHeight);
                            }}
                        }}
                        
                        // 🔒 CORRECCIÓN: Asegurar que chartHeight no sea negativo
                        chartHeight = Math.max(chartHeight, minChartHeight);
                        
                        // CRÍTICO: NO modificar estilos de la celda - mantener tamaño fijo del grid
                        // data ya fue definido arriba para calcular needsRotation
                        
                        if (data.length === 0) {{
                            targetCell.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos</div>';
                            window._bestlib_updating_boxplot_{letter} = false;
                            return;
                        }}
                        
                        // 🔒 CORRECCIÓN: Establecer SVG con viewBox para mejor escalado y ajuste al contenedor
                        // IMPORTANTE: Usar overflow: visible para que las etiquetas de ejes se vean
                        // El SVG debe caber dentro de la celda sin cambiar su tamaño
                        const svg = window.d3.select(targetCell)
                            .append('svg')
                            .attr('width', '100%')
                            .attr('height', '100%')
                            .attr('viewBox', `0 0 ${{width}} ${{svgHeight}}`)
                            .attr('preserveAspectRatio', 'xMidYMid meet')
                            .style('max-width', '100%')
                            .style('max-height', '100%')
                            .style('overflow', 'visible')
                            .style('display', 'block');
                        
                        const g = svg.append('g')
                            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
                        
                        const x = window.d3.scaleBand()
                            .domain(data.map(d => d.category))
                            .range([0, chartWidth])
                            .padding(0.2);
                        
                        // 🔒 CORRECCIÓN: Calcular dominio Y con padding para evitar que se pegue al eje
                        const yMin = window.d3.min(data, d => d.lower);
                        const yMax = window.d3.max(data, d => d.upper);
                        // Asegurar que el dominio sea válido (no NaN, no infinito)
                        const yDomainMin = (isFinite(yMin) && !isNaN(yMin)) ? yMin : 0;
                        const yDomainMax = (isFinite(yMax) && !isNaN(yMax)) ? yMax : (yDomainMin + 1);
                        // 🔒 Agregar padding al dominio Y (5% arriba y abajo) para separar de los bordes
                        const yRange = yDomainMax - yDomainMin;
                        const yPadding = yRange * 0.05; // 5% de padding
                        const yPaddedMin = yDomainMin - yPadding;
                        const yPaddedMax = yDomainMax + yPadding;
                        const y = window.d3.scaleLinear()
                            .domain([yPaddedMin, yPaddedMax])
                            .nice()
                            .range([chartHeight, 0]);
                        
                        // Dibujar boxplot para cada categoría
                        data.forEach((d, i) => {{
                            const xPos = x(d.category);
                            const boxWidth = x.bandwidth();
                            const centerX = xPos + boxWidth / 2;
                            
                            // Bigotes (whiskers)
                            g.append('line')
                                .attr('x1', centerX)
                                .attr('x2', centerX)
                                .attr('y1', y(d.lower))
                                .attr('y2', y(d.q1))
                                .attr('stroke', '#000')
                                .attr('stroke-width', 2);
                            
                            g.append('line')
                                .attr('x1', centerX)
                                .attr('x2', centerX)
                                .attr('y1', y(d.q3))
                                .attr('y2', y(d.upper))
                                .attr('stroke', '#000')
                                .attr('stroke-width', 2);
                            
                            // Caja (box)
                            g.append('rect')
                                .attr('x', xPos)
                                .attr('y', y(d.q3))
                                .attr('width', boxWidth)
                                .attr('height', y(d.q1) - y(d.q3))
                                .attr('fill', '{default_color}')
                                .attr('stroke', '#000')
                                .attr('stroke-width', 2);
                            
                            // Mediana (median line)
                            g.append('line')
                                .attr('x1', xPos)
                                .attr('x2', xPos + boxWidth)
                                .attr('y1', y(d.median))
                                .attr('y2', y(d.median))
                                .attr('stroke', '#fff')
                                .attr('stroke-width', 2);
                        }});
                        
                        if ({str(show_axes).lower()}) {{
                            // 🔒 CORRECCIÓN: Eje X - Asegurar que se muestre correctamente y no se salga del SVG
                            const xAxis = g.append('g')
                                .attr('class', 'x-axis')
                                .attr('transform', `translate(0,${{chartHeight}})`);
                            
                            const xAxisGenerator = window.d3.axisBottom(x);
                            xAxis.call(xAxisGenerator);
                            
                            // Estilizar etiquetas del eje X con rotación si es necesario
                            xAxis.selectAll('text')
                                .style('font-size', needsRotation ? '10px' : '12px')
                                .style('font-weight', '600')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif')
                                .attr('transform', needsRotation ? 'rotate(-45)' : null)
                                .style('text-anchor', needsRotation ? 'end' : 'middle')
                                .attr('dx', needsRotation ? '-0.5em' : '0')
                                .attr('dy', needsRotation ? '0.5em' : '0.7em')
                                .style('opacity', 1);  // Asegurar que sean visibles
                            
                            // Estilizar líneas del eje X
                            xAxis.selectAll('line, path')
                                .style('stroke', '#000000')
                                .style('stroke-width', '1.5px')
                                .style('opacity', 1);  // Asegurar que sean visibles
                            
                            // 🔒 CORRECCIÓN: Eje Y - Asegurar que se muestre correctamente
                            const yAxis = g.append('g')
                                .attr('class', 'y-axis');
                            
                            const yAxisGenerator = window.d3.axisLeft(y)
                                .ticks(5)
                                .tickFormat(window.d3.format('.2f'));  // Formato numérico para el eje Y
                            
                            yAxis.call(yAxisGenerator);
                            
                            // Estilizar etiquetas del eje Y
                            yAxis.selectAll('text')
                                .style('font-size', '12px')
                                .style('font-weight', '600')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif')
                                .style('opacity', 1);  // Asegurar que sean visibles
                            
                            // Estilizar líneas del eje Y
                            yAxis.selectAll('line, path')
                                .style('stroke', '#000000')
                                .style('stroke-width', '1.5px')
                                .style('opacity', 1);  // Asegurar que sean visibles
                            
                            // Renderizar etiquetas de ejes
                            // Etiqueta del eje X (debajo del gráfico)
                            // CRÍTICO: Asegurar que la etiqueta quede dentro del SVG
                            const xLabelX = chartWidth / 2;
                            // Posicionar la etiqueta dentro del espacio disponible del SVG
                            // chartHeight + margin.bottom es donde termina el área del gráfico
                            // Usar el espacio calculado en extraHeightForXAxis
                            const spaceForRotatedLabels = needsRotation ? 45 : 0;
                            // Asegurar que xLabelY no exceda svgHeight - margin.top
                            const maxYLabelPosition = svgHeight - margin.top - 5; // 5px de margen de seguridad
                            const xLabelY = Math.min(
                                chartHeight + margin.bottom + spaceForRotatedLabels + 15,
                                maxYLabelPosition
                            );
                            
                            const xLabelText = g.append('text')
                                .attr('x', xLabelX)
                                .attr('y', xLabelY)
                                .attr('text-anchor', 'middle')
                                .style('font-size', '13px')
                                .style('font-weight', '700')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif')
                                .text({x_label});
                            
                            // Etiqueta del eje Y (a la izquierda del gráfico, rotada -90 grados)
                            const yLabelX = margin.left / 2;
                            const yLabelY = margin.top + chartHeight / 2;
                            
                            const yLabelText = svg.append('text')
                                .attr('x', yLabelX)
                                .attr('y', yLabelY)
                                .attr('text-anchor', 'middle')
                                .attr('dominant-baseline', 'central')
                                .style('font-size', '13px')
                                .style('font-weight', '700')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif')
                                .style('pointer-events', 'none')
                                .attr('transform', `rotate(-90 ${{yLabelX}} ${{yLabelY}})`)
                                .text({y_label});
                        }}
                        
                        // Renderizar título del gráfico si está especificado
                        const title = '{kwargs.get("title", "")}';
                        if (title && title.trim() !== '') {{
                            const titleFontSize = {kwargs.get("titleFontSize", 16)};
                            const titleY = margin.top - 10;
                            const titleX = chartWidth / 2;
                            
                            svg.append('text')
                                .attr('x', titleX + margin.left)
                                .attr('y', titleY)
                                .attr('text-anchor', 'middle')
                                .style('font-size', titleFontSize + 'px')
                                .style('font-weight', '700')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif')
                                .text(title);
                        }}
                        
                        // IMPORTANTE: Marcar que esta celda ya no necesita ResizeObserver
                        // porque se está actualizando manualmente
                        targetCell._chartSpec = null;
                        targetCell._chartDivId = null;
                        
                        // Resetear flag después de completar la actualización
                        window._bestlib_updating_boxplot_{letter} = false;
                    }}
                    
                    updateBoxplot();
                }})();
                """
                
                try:
                    # CRÍTICO: En lugar de usar display(), ejecutar JavaScript directamente
                    # usando el comm existente para evitar que se dispare un re-render completo
                    # Esto previene la duplicación de la matriz
                    from IPython.display import Javascript, display
                    import uuid
                    
                    # Generar un ID único para este script para evitar duplicaciones
                    script_id = f'boxplot-update-{letter}-{uuid.uuid4().hex[:8]}'
                    
                    # IMPORTANTE: Usar display_id para que Jupyter reemplace el output anterior
                    # en lugar de crear uno nuevo, lo que previene la duplicación
                    display(Javascript(js_update), clear=False, display_id=f'boxplot-update-{letter}', update=True)
                    
                    if self._debug or MatrixLayout._debug:
                        print(f"   📤 JavaScript del boxplot '{letter}' ejecutado (display_id: boxplot-update-{letter})")
                except Exception as e:
                    MatrixLayout = _get_matrix_layout()
                    if self._debug or MatrixLayout._debug:
                        print(f"⚠️ Error ejecutando JavaScript del boxplot: {e}")
                        import traceback
                        traceback.print_exc()
                    
            except Exception as e:
                MatrixLayout = _get_matrix_layout()
                import traceback
                if self._debug or MatrixLayout._debug:
                    print(f"⚠️ Error actualizando boxplot: {e}")
                    traceback.print_exc()
            finally:
                # CRÍTICO: Resetear flag después de completar
                update_boxplot._executing = False
                if self._debug or MatrixLayout._debug:
                    print(f"   ✅ Boxplot '{letter}' callback completado")
        
        # Registrar callback en el SelectionModel de la vista principal
        primary_selection.on_change(update_boxplot)
        
        # Guardar referencia al callback para evitar duplicados
        self._boxplot_callbacks[letter] = update_boxplot
        
        # Debug: verificar que el callback se registró
        if self._debug or MatrixLayout._debug:
            print(f"🔗 [ReactiveMatrixLayout] Callback registrado para boxplot '{letter}' enlazado a vista principal '{primary_letter}'")
            print(f"   - SelectionModel ID: {id(primary_selection)}")
            print(f"   - Callbacks registrados: {len(primary_selection._callbacks)}")
            print(f"   - Boxplot callbacks guardados: {list(self._boxplot_callbacks.keys())}")
        
        # Crear boxplot inicial con todos los datos
        if HAS_PANDAS and isinstance(self._data, pd.DataFrame):
            if category_col and category_col in self._data.columns:
                box_data = []
                for cat in self._data[category_col].unique():
                    cat_data = self._data[self._data[category_col] == cat][column].dropna()
                    if len(cat_data) > 0:
                        q1 = cat_data.quantile(0.25)
                        median = cat_data.quantile(0.5)
                        q3 = cat_data.quantile(0.75)
                        iqr = q3 - q1
                        lower = max(q1 - 1.5 * iqr, cat_data.min())
                        upper = min(q3 + 1.5 * iqr, cat_data.max())
                        box_data.append({
                            'category': cat,
                            'q1': float(q1),
                            'median': float(median),
                            'q3': float(q3),
                            'lower': float(lower),
                            'upper': float(upper),
                            'min': float(cat_data.min()),
                            'max': float(cat_data.max())
                        })
            else:
                values = self._data[column].dropna()
                if len(values) > 0:
                    q1 = values.quantile(0.25)
                    median = values.quantile(0.5)
                    q3 = values.quantile(0.75)
                    iqr = q3 - q1
                    lower = max(q1 - 1.5 * iqr, values.min())
                    upper = min(q3 + 1.5 * iqr, values.max())
                    box_data = [{
                        'category': 'All',
                        'q1': float(q1),
                        'median': float(median),
                        'q3': float(q3),
                        'lower': float(lower),
                        'upper': float(upper),
                        'min': float(values.min()),
                        'max': float(values.max())
                    }]
                else:
                    box_data = []
        else:
            values = [item.get(column, 0) for item in self._data if column in item]
            if values:
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                q1 = sorted_vals[int(n * 0.25)]
                median = sorted_vals[int(n * 0.5)]
                q3 = sorted_vals[int(n * 0.75)]
                iqr = q3 - q1
                lower = max(q1 - 1.5 * iqr, min(values))
                upper = min(q3 + 1.5 * iqr, max(values))
                box_data = [{
                    'category': 'All',
                    'q1': float(q1),
                    'median': float(median),
                    'q3': float(q3),
                    'lower': float(lower),
                    'upper': float(upper),
                    'min': float(min(values)),
                    'max': float(max(values))
                }]
            else:
                box_data = []
        
        if box_data:
            boxplot_spec = {
                'type': 'boxplot',
                'data': box_data,
                'column': column,
                'category_col': category_col,
                **kwargs
            }
            # Asegurar que __linked_to__ esté en el spec si fue agregado antes
            if '__linked_to__' in kwargs:
                boxplot_spec['__linked_to__'] = kwargs['__linked_to__']
            MatrixLayout._map[letter] = boxplot_spec
        
        return self
    
    def _prepare_barchart_data(self, data, category_col, value_col, kwargs):
        """Helper para preparar datos del bar chart (incluyendo _original_rows)"""
        try:
            if HAS_PANDAS and isinstance(data, pd.DataFrame):
                if value_col and value_col in data.columns:
                    bar_data = data.groupby(category_col)[value_col].sum().reset_index()
                    bar_data = bar_data.rename(columns={category_col: 'category', value_col: 'value'})
                    bar_data = bar_data.to_dict('records')
                elif category_col and category_col in data.columns:
                    counts = data[category_col].value_counts()
                    bar_data = [{'category': cat, 'value': count} for cat, count in counts.items()]
                else:
                    return []
                
                # Agregar datos originales para referencia (IMPORTANTE para linked views)
                original_data = data.to_dict('records')
                for bar_item in bar_data:
                    # Encontrar todas las filas con esta categoría
                    matching_rows = [row for row in original_data if row.get(category_col) == bar_item['category']]
                    bar_item['_original_rows'] = matching_rows
            else:
                from collections import Counter
                if value_col:
                    from collections import defaultdict
                    sums = defaultdict(float)
                    for item in data:
                        cat = item.get(category_col, 'unknown')
                        val = item.get(value_col, 0)
                        sums[cat] += val
                    bar_data = [{'category': cat, 'value': val} for cat, val in sums.items()]
                else:
                    categories = Counter([item.get(category_col, 'unknown') for item in data])
                    bar_data = [{'category': cat, 'value': count} for cat, count in categories.items()]
                
                # Agregar datos originales
                original_data = data if isinstance(data, list) else []
                for bar_item in bar_data:
                    matching_rows = [row for row in original_data if row.get(category_col or 'category') == bar_item['category']]
                    bar_item['_original_rows'] = matching_rows
            
            # Obtener colorMap
            color_map = kwargs.get('colorMap', {})
            default_color = kwargs.get('color', '#4a90e2')
            for bar_item in bar_data:
                bar_item['color'] = color_map.get(bar_item['category'], default_color)
            
            return bar_data
        except Exception as e:
            MatrixLayout = _get_matrix_layout()
            import traceback
            if self._debug or MatrixLayout._debug:
                print(f"⚠️ Error preparando datos del bar chart: {e}")
                traceback.print_exc()
            return []
    
    def map(self, mapping):
        """Delega al MatrixLayout interno"""
        self._layout.map(mapping)
        return self
    
    def on(self, event, func):
        """Delega al MatrixLayout interno"""
        self._layout.on(event, func)
        return self

    # ==========================
    # Nuevos gráficos dependientes
    # ==========================
    def add_heatmap(self, letter, x_col=None, y_col=None, value_col=None, linked_to=None, **kwargs):
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        # initial render
        MatrixLayout.map_heatmap(letter, self._data, x_col=x_col, y_col=y_col, value_col=value_col, **kwargs)
        # link to selection
        if not self._scatter_selection_models:
            return self
        scatter_letter = linked_to or list(self._scatter_selection_models.keys())[-1]
        sel = self._scatter_selection_models[scatter_letter]
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                MatrixLayout.map_heatmap(letter, data_to_use, x_col=x_col, y_col=y_col, value_col=value_col, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self

    def add_correlation_heatmap(self, letter, linked_to=None, **kwargs):
        MatrixLayout = _get_matrix_layout()
        if not (HAS_PANDAS and isinstance(self._data, pd.DataFrame)):
            raise ValueError("add_correlation_heatmap requiere DataFrame")
        MatrixLayout.map_correlation_heatmap(letter, self._data, **kwargs)
        # link
        if not self._scatter_selection_models:
            return self
        scatter_letter = linked_to or list(self._scatter_selection_models.keys())[-1]
        sel = self._scatter_selection_models[scatter_letter]
        def update(items, count):
            df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
            if df is None:
                return
            try:
                MatrixLayout.map_correlation_heatmap(letter, df, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self

    def add_line(self, letter, x_col=None, y_col=None, series_col=None, linked_to=None, **kwargs):
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        MatrixLayout.map_line(letter, self._data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
        if not self._scatter_selection_models:
            return self
        scatter_letter = linked_to or list(self._scatter_selection_models.keys())[-1]
        sel = self._scatter_selection_models[scatter_letter]
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                MatrixLayout.map_line(letter, data_to_use, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self

    def add_pie(self, letter, category_col=None, value_col=None, linked_to=None, interactive=None, selection_var=None, **kwargs):
        """
        Agrega un pie chart que puede ser vista principal o enlazada.
        
        Args:
            letter: Letra del layout ASCII donde irá el pie chart
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional, si no se especifica cuenta)
            linked_to: Letra de la vista principal que debe actualizar este pie chart (opcional)
                      Si no se especifica y interactive=True, este pie chart será vista principal
            interactive: Si True, permite seleccionar segmentos. Si es None, se infiere de linked_to
            selection_var: Nombre de variable Python donde guardar selecciones (ej: 'selected_category')
            **kwargs: Argumentos adicionales (colorMap, axes, etc.)
        
        Returns:
            self para encadenamiento
        
        Ejemplos:
            # Pie chart como vista principal
            layout.add_pie('P1', category_col='dept', interactive=True, selection_var='selected_dept')
            
            # Pie chart enlazado a bar chart
            layout.add_barchart('B', category_col='dept', interactive=True)
            layout.add_pie('P2', category_col='dept', linked_to='B')
        """
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        
        # Determinar si será vista principal o enlazada
        if linked_to is None:
            # Si no hay linked_to, NO es vista enlazada
            # Solo es vista principal si interactive=True se especifica EXPLÍCITAMENTE
            if interactive is None:
                # Por defecto, NO interactivo y NO enlazado (gráfico estático)
                interactive = False
                is_primary = False
            else:
                # Si el usuario especificó interactive explícitamente, respetarlo
                is_primary = interactive
        else:
            is_primary = False
            if interactive is None:
                interactive = False
        
        # Si es vista principal, crear su propio SelectionModel
        if is_primary:
            pie_selection = SelectionModel()
            self._primary_view_models[letter] = pie_selection
            self._primary_view_types[letter] = 'pie'
            
            # Guardar variable de selección si se especifica
            if selection_var:
                self._selection_variables[letter] = selection_var
                import __main__
                empty_df = pd.DataFrame() if HAS_PANDAS else []
                setattr(__main__, selection_var, empty_df)
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de pie chart '{letter}' como {df_type}")
            
            # Crear handler para eventos de selección del pie chart
            def pie_handler(payload):
                """Handler que actualiza el SelectionModel de este pie chart"""
                event_letter = payload.get('__view_letter__')
                if event_letter != letter:
                    return
                
                items = payload.get('items', [])
                
                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Evento recibido para pie chart '{letter}': {len(items)} items")
                
                # Convertir items a DataFrame antes de guardar
                items_df = _items_to_dataframe(items)
                
                pie_selection.update(items)
                self.selection_model.update(items)
                self._selected_data = items_df if items_df is not None else items
                
                # Guardar en variable Python si se especificó (como DataFrame)
                if selection_var:
                    import __main__
                    # Guardar como DataFrame para facilitar el trabajo del usuario
                    setattr(__main__, selection_var, items_df if items_df is not None else items)
                    if self._debug or MatrixLayout._debug:
                        count_msg = f"{len(items_df)} filas" if items_df is not None and hasattr(items_df, '__len__') else f"{len(items)} items"
                        print(f"💾 Selección guardada en variable '{selection_var}' como DataFrame: {count_msg}")
            
            self._layout.on('select', pie_handler)
            
            kwargs['__view_letter__'] = letter
            kwargs['__is_primary_view__'] = True
            kwargs['interactive'] = True
        
        # Crear pie chart inicial con todos los datos
        MatrixLayout.map_pie(letter, self._data, category_col=category_col, value_col=value_col, **kwargs)
        
        # Asegurar que __linked_to__ esté en el spec guardado (por si map_pie no lo copió)
        if not is_primary and linked_to:
            if letter in MatrixLayout._map:
                MatrixLayout._map[letter]['__linked_to__'] = linked_to
        
        # Si es vista enlazada, configurar callback
        if not is_primary:
            # CRÍTICO: Si linked_to es None, NO enlazar automáticamente (gráfico estático)
            if linked_to is None:
                # Pie chart estático sin enlazar (ya se creó arriba)
                return self
            
            # Buscar en scatter plots primero (compatibilidad hacia atrás)
            if linked_to in self._scatter_selection_models:
                primary_letter = linked_to
                primary_selection = self._scatter_selection_models[primary_letter]
            elif linked_to in self._primary_view_models:
                primary_letter = linked_to
                primary_selection = self._primary_view_models[primary_letter]
            else:
                # Si linked_to está especificado pero no existe, lanzar error
                raise ValueError(f"Vista principal '{linked_to}' no existe. Agrega la vista principal primero.")
            
            # Agregar __linked_to__ al spec para indicadores visuales en JavaScript
            kwargs['__linked_to__'] = primary_letter
            
            # Flag para evitar actualizaciones recursivas del pie chart
            pie_update_flag = f'_pie_updating_{letter}'
            if not hasattr(self, '_update_flags'):
                self._update_flags = {}
            self._update_flags[pie_update_flag] = False
            
            # Cache para datos previos del pie chart para evitar actualizaciones innecesarias
            pie_data_cache_key = f'_pie_data_cache_{letter}'
            if not hasattr(self, '_pie_data_cache'):
                self._pie_data_cache = {}
            self._pie_data_cache[pie_data_cache_key] = None
            
            def update_pie(items, count):
                """Actualiza el pie chart cuando cambia la selección"""
                MatrixLayout = _get_matrix_layout()
                from collections import defaultdict
                import json
                from IPython.display import Javascript
                import traceback
                import hashlib
                
                # Prevenir actualizaciones recursivas
                if self._update_flags.get(pie_update_flag, False):
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Actualización de pie chart '{letter}' ya en progreso, ignorando...")
                    return
                
                self._update_flags[pie_update_flag] = True
                
                try:
                    if self._debug or MatrixLayout._debug:
                        print(f"🔄 [ReactiveMatrixLayout] Callback ejecutado: Actualizando pie chart '{letter}' con {count} items seleccionados")
                    
                    # Procesar items: los items del bar chart ya son las filas originales
                    # Cuando el bar chart envía eventos, items contiene directamente las filas originales
                    # de la categoría seleccionada (no necesitan extracción de _original_row)
                    data_to_use = self._data
                    if items and len(items) > 0:
                        # Los items pueden ser:
                        # 1. Filas originales directamente (del bar chart)
                        # 2. Diccionarios con _original_row o _original_rows
                        # 3. Lista vacía o None
                        processed_items = []
                        for item in items:
                            if isinstance(item, dict):
                                # Verificar si tiene _original_rows (viene del bar chart con múltiples filas)
                                if '_original_rows' in item and isinstance(item['_original_rows'], list):
                                    processed_items.extend(item['_original_rows'])
                                # Verificar si tiene _original_row (una sola fila)
                                elif '_original_row' in item:
                                    processed_items.append(item['_original_row'])
                                # Si no tiene _original_row/_original_rows, el item ya es una fila original
                                else:
                                    # Verificar si tiene las columnas esperadas (es una fila original)
                                    processed_items.append(item)
                            else:
                                processed_items.append(item)
                        
                        if processed_items:
                            if HAS_PANDAS and isinstance(processed_items[0], dict):
                                import pandas as pd
                                data_to_use = pd.DataFrame(processed_items)
                            else:
                                data_to_use = processed_items
                        else:
                            # Si no hay items procesados, usar todos los datos
                            data_to_use = self._data
                    else:
                        # Si no hay items, usar todos los datos
                        data_to_use = self._data
                    
                    # Validar que category_col existe en los datos
                    if HAS_PANDAS and isinstance(data_to_use, pd.DataFrame):
                        if category_col and category_col not in data_to_use.columns:
                            if self._debug or MatrixLayout._debug:
                                print(f"⚠️ Columna '{category_col}' no encontrada en datos. Columnas disponibles: {list(data_to_use.columns)}")
                            # Intentar usar todos los datos originales
                            data_to_use = self._data
                    
                    # IMPORTANTE: NO actualizar el mapping aquí para evitar bucles infinitos
                    # Solo actualizar visualmente el gráfico con JavaScript
                    # El mapping ya tiene los datos correctos desde la creación inicial
                    
                    # Re-renderizar el pie chart usando JavaScript (sin actualizar el mapping)
                    try:
                        # Preparar datos para el pie chart
                        # IMPORTANTE: Incluir _original_rows para cada categoría
                        # Esto permite que cuando se hace click en el pie chart, se envíen todas las filas originales
                        if HAS_PANDAS and isinstance(data_to_use, pd.DataFrame):
                            if category_col and category_col in data_to_use.columns:
                                # IMPORTANTE: Almacenar filas originales para cada categoría
                                original_data = data_to_use.to_dict('records')
                                category_rows = defaultdict(list)  # Diccionario: categoría -> lista de filas
                                
                                # Agrupar filas por categoría
                                for row in original_data:
                                    cat = row.get(category_col)
                                    if cat is not None:
                                        category_rows[str(cat)].append(row)
                                
                                if value_col and value_col in data_to_use.columns:
                                    # Calcular suma por categoría
                                    agg = data_to_use.groupby(category_col)[value_col].sum().reset_index()
                                    pie_data = [
                                        {
                                            'category': str(r[category_col]),
                                            'value': float(r[value_col]),
                                            '_original_rows': category_rows.get(str(r[category_col]), [])
                                        }
                                        for _, r in agg.iterrows()
                                    ]
                                else:
                                    # Contar por categoría
                                    counts = data_to_use[category_col].value_counts()
                                    pie_data = [
                                        {
                                            'category': str(cat),
                                            'value': int(cnt),
                                            '_original_rows': category_rows.get(str(cat), [])
                                        }
                                        for cat, cnt in counts.items()
                                    ]
                            else:
                                if self._debug or MatrixLayout._debug:
                                    print(f"⚠️ No se puede crear pie chart: columna '{category_col}' no encontrada")
                                return
                        else:
                            from collections import Counter, defaultdict
                            
                            # IMPORTANTE: Almacenar items originales para cada categoría
                            items = data_to_use if isinstance(data_to_use, list) else []
                            category_rows = defaultdict(list)  # Diccionario: categoría -> lista de items
                            
                            # Agrupar items por categoría
                            for it in items:
                                cat = it.get(category_col, 'unknown')
                                if cat is not None:
                                    category_rows[str(cat)].append(it)
                            
                            if value_col:
                                sums = defaultdict(float)
                                for item in items:
                                    cat = str(item.get(category_col, 'unknown'))
                                    val = item.get(value_col, 0)
                                    try:
                                        sums[cat] += float(val)
                                    except Exception:
                                        pass
                                pie_data = [
                                    {
                                        'category': k,
                                        'value': float(v),
                                        '_original_rows': category_rows.get(k, [])
                                    }
                                    for k, v in sums.items()
                                ]
                            else:
                                counts = Counter([str(item.get(category_col, 'unknown')) for item in items])
                                pie_data = [
                                    {
                                        'category': k,
                                        'value': int(v),
                                        '_original_rows': category_rows.get(k, [])
                                    }
                                    for k, v in counts.items()
                                ]
                        
                        if not pie_data:
                            self._update_flags[pie_update_flag] = False
                            return
                        
                        # Verificar si los datos han cambiado (evitar actualizaciones innecesarias)
                        try:
                            pie_data_str = json.dumps(pie_data, sort_keys=True)
                            pie_data_hash = hashlib.md5(pie_data_str.encode()).hexdigest()
                            if self._pie_data_cache.get(pie_data_cache_key) == pie_data_hash:
                                if self._debug or MatrixLayout._debug:
                                    print(f"⏭️ [ReactiveMatrixLayout] Datos del pie chart '{letter}' no han cambiado, ignorando actualización")
                                self._update_flags[pie_update_flag] = False
                                return
                            
                            # Actualizar cache
                            self._pie_data_cache[pie_data_cache_key] = pie_data_hash
                        except Exception:
                            pass  # Si hay error con el hash, continuar con la actualización
                        
                        # JavaScript para actualizar el pie chart (sin disparar eventos)
                        div_id = self._layout.div_id
                        pie_data_json = json.dumps(_sanitize_for_json(pie_data))
                        
                        # Flag para evitar actualizaciones múltiples simultáneas
                        update_flag_key = f'_bestlib_updating_pie_{letter}'
                        
                        js_update = f"""
                        (function() {{
                            // Flag para evitar actualizaciones múltiples simultáneas
                            if (window.{update_flag_key}) {{
                                console.log('⏭️ Actualización de pie chart {letter} ya en progreso, ignorando...');
                                return;
                            }}
                            window.{update_flag_key} = true;
                            
                            // CRÍTICO: Usar setTimeout con delay 0 para actualizar de forma asíncrona
                            // Esto evita que la actualización cause una re-renderización inmediata del layout
                            // NO usar requestAnimationFrame porque puede causar problemas de sincronización
                            setTimeout(function() {{
                                try {{
                                    if (!window.d3) {{
                                        window.{update_flag_key} = false;
                                        return;
                                    }}
                                    
                                    const container = document.getElementById('{div_id}');
                                    if (!container) {{
                                        window.{update_flag_key} = false;
                                        return;
                                    }}
                                    
                                    // CRÍTICO: Buscar SOLO la celda del pie chart (letra '{letter}')
                                    // IMPORTANTE: El pie chart está en una celda diferente al bar chart
                                    // NO buscar celdas con barras, solo celdas sin barras
                                    const cells = container.querySelectorAll('.matrix-cell[data-letter="{letter}"]');
                                    let targetCell = null;
                                    
                                    // Buscar la celda que NO tiene barras (es la del pie chart)
                                    // El bar chart está en otra celda, así que buscar celdas sin barras
                                    for (let cell of cells) {{
                                        const bars = cell.querySelectorAll('.bar');
                                        if (bars.length === 0) {{
                                            // Esta es la celda del pie chart (no tiene barras)
                                            targetCell = cell;
                                            break;
                                        }}
                                    }}
                                    
                                    // Si no encontramos una celda sin barras, usar la primera celda con la letra
                                    if (!targetCell && cells.length > 0) {{
                                        targetCell = cells[0];
                                    }}
                                    
                                    if (!targetCell) {{
                                        window.{update_flag_key} = false;
                                        return;
                                    }}
                                    
                                    // CRÍTICO: NO tocar otras celdas ni limpiar toda la celda
                                    // Solo actualizar el contenido del pie chart usando D3 update pattern
                                    // NO usar innerHTML = '' porque causa que el layout se re-renderice
                                    
                                    // CRÍTICO: Usar getChartDimensions() para calcular dimensiones de manera consistente
                                    const dims = window.getChartDimensions ? 
                                        window.getChartDimensions(targetCell, {{ type: 'pie' }}, 400, 400) :
                                        {{ width: Math.max(targetCell.clientWidth || 400, 200), height: Math.max(targetCell.clientHeight || 400, 200) }};
                                    const width = dims.width;
                                    const height = dims.height;
                                    const radius = Math.min(width, height) / 2 - 20;
                                    
                                    const data = {pie_data_json};
                                    
                                    if (data.length === 0) {{
                                        window.{update_flag_key} = false;
                                        return;
                                    }}
                                    
                                    // CRÍTICO: Buscar SVG existente del pie chart (tiene clase 'pie-chart-svg')
                                    // NO tocar SVGs del bar chart (tienen clase 'bar-chart' o tienen barras)
                                    let svg = window.d3.select(targetCell).select('svg.pie-chart-svg');
                                    let g;
                                    
                                    if (svg.empty()) {{
                                        // Crear nuevo SVG si no existe
                                        // IMPORTANTE: NO limpiar toda la celda, solo agregar el SVG del pie chart
                                        svg = window.d3.select(targetCell)
                                            .append('svg')
                                            .attr('class', 'pie-chart-svg')
                                            .attr('width', width)
                                            .attr('height', height)
                                            .style('position', 'absolute')
                                            .style('top', '0')
                                            .style('left', '0')
                                            .style('z-index', '1')
                                            .style('pointer-events', 'none');  // No interceptar eventos
                                        
                                        g = svg.append('g')
                                            .attr('class', 'pie-chart-group')
                                            .attr('transform', `translate(${{width / 2}},${{height / 2}})`);
                                    }} else {{
                                        // Usar SVG existente
                                        svg.attr('width', width).attr('height', height);
                                        
                                        g = svg.select('g.pie-chart-group');
                                        if (g.empty()) {{
                                            g = svg.append('g')
                                                .attr('class', 'pie-chart-group')
                                                .attr('transform', `translate(${{width / 2}},${{height / 2}})`);
                                        }} else {{
                                            g.attr('transform', `translate(${{width / 2}},${{height / 2}})`);
                                        }}
                                    }}
                                    
                                    const color = window.d3.scaleOrdinal(window.d3.schemeCategory10);
                                    
                                    const pie = window.d3.pie()
                                        .value(d => d.value || 0)
                                        .sort(null);
                                    
                                    const arc = window.d3.arc()
                                        .innerRadius(0)
                                        .outerRadius(radius);
                                    
                                    // CRÍTICO: Usar D3 update pattern para actualizar solo los arcs
                                    // NO limpiar todo el SVG, solo actualizar los datos
                                    const arcs = g.selectAll('.arc')
                                        .data(pie(data), d => d.data.category);  // Key function para identificar arcs
                                    
                                    // Remover arcs que ya no existen
                                    arcs.exit()
                                        .transition()
                                        .duration(150)
                                        .attr('opacity', 0)
                                        .remove();
                                    
                                    // Agregar nuevos arcs
                                    const arcsEnter = arcs.enter()
                                        .append('g')
                                        .attr('class', 'arc')
                                        .style('pointer-events', 'none')
                                        .attr('opacity', 0);
                                    
                                    arcsEnter.append('path')
                                        .attr('d', arc)
                                        .attr('fill', (d, i) => color(i))
                                        .attr('stroke', '#fff')
                                        .attr('stroke-width', 2)
                                        .style('pointer-events', 'none');
                                    
                                    arcsEnter.append('text')
                                        .attr('transform', d => `translate(${{arc.centroid(d)}})`)
                                        .attr('dy', '.35em')
                                        .style('text-anchor', 'middle')
                                        .style('font-size', '12px')
                                        .style('pointer-events', 'none')
                                        .text(d => d.data.category);
                                    
                                    // Actualizar arcs existentes y nuevos
                                    const arcsUpdate = arcsEnter.merge(arcs);
                                    
                                    arcsUpdate.select('path')
                                        .transition()
                                        .duration(200)
                                        .attr('d', arc)
                                        .attr('fill', (d, i) => color(i))
                                        .attr('opacity', 1);
                                    
                                    arcsUpdate.select('text')
                                        .transition()
                                        .duration(200)
                                        .attr('transform', d => `translate(${{arc.centroid(d)}})`)
                                        .attr('opacity', 1);
                                    
                                    // Reset flag después de actualizar (con delay más largo)
                                    setTimeout(() => {{
                                        window.{update_flag_key} = false;
                                    }}, 300);
                                }} catch (error) {{
                                    console.error('Error actualizando pie chart:', error);
                                    window.{update_flag_key} = false;
                                }}
                            }}, 0);  // Delay 0 para ejecutar en el siguiente ciclo del event loop
                        }})();
                        """
                        
                        # IMPORTANTE: Ejecutar JavaScript de forma directa sin causar re-renderización
                        # IMPORTANTE: Usar display_id para que Jupyter reemplace el output anterior
                        # en lugar de crear uno nuevo, lo que previene la duplicación
                        try:
                            from IPython.display import Javascript, display
                            # Ejecutar JavaScript directamente
                            display(Javascript(js_update), clear=False, display_id=f'piechart-update-{letter}', update=True)
                        except Exception as e:
                            if self._debug or MatrixLayout._debug:
                                print(f"⚠️ Error ejecutando JavaScript del pie chart: {e}")
                                import traceback
                                traceback.print_exc()
                    except Exception as e:
                        if self._debug or MatrixLayout._debug:
                            print(f"⚠️ Error actualizando pie chart con JavaScript: {e}")
                            traceback.print_exc()
                    finally:
                        # Reset flag después de un pequeño delay para evitar bucles
                        import threading
                        def reset_flag():
                            import time
                            time.sleep(0.15)  # Pequeño delay para evitar bucles
                            self._update_flags[pie_update_flag] = False
                        threading.Thread(target=reset_flag, daemon=True).start()
                except Exception as e:
                    if self._debug or MatrixLayout._debug:
                        print(f"⚠️ Error actualizando pie chart: {e}")
                        traceback.print_exc()
                    # Reset flag en caso de error
                    self._update_flags[pie_update_flag] = False
            
            # Registrar callback en el SelectionModel de la vista principal
            primary_selection.on_change(update_pie)
            
            # Debug: verificar que el callback se registró
            if self._debug or MatrixLayout._debug:
                print(f"🔗 [ReactiveMatrixLayout] Callback registrado para pie chart '{letter}' enlazado a vista principal '{primary_letter}'")
                print(f"   - SelectionModel ID: {id(primary_selection)}")
                print(f"   - Callbacks registrados: {len(primary_selection._callbacks)}")
        
        return self

    def add_violin(self, letter, value_col=None, category_col=None, bins=20, linked_to=None, **kwargs):
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        MatrixLayout.map_violin(letter, self._data, value_col=value_col, category_col=category_col, bins=bins, **kwargs)
        
        # Solo registrar callback si linked_to está especificado explícitamente
        if linked_to is None:
            # No enlazar automáticamente, hacer gráfico estático
            return self
        
        # Buscar vista principal especificada
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            raise ValueError(f"Vista principal '{linked_to}' no existe. Agrega la vista principal primero.")
        
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                MatrixLayout.map_violin(letter, data_to_use, value_col=value_col, category_col=category_col, bins=bins, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self

    def add_radviz(self, letter, features=None, class_col=None, linked_to=None, **kwargs):
        MatrixLayout = _get_matrix_layout()
        if not (HAS_PANDAS and isinstance(self._data, pd.DataFrame)):
            raise ValueError("add_radviz requiere DataFrame")
        MatrixLayout.map_radviz(letter, self._data, features=features, class_col=class_col, **kwargs)
        
        # Solo registrar callback si linked_to está especificado explícitamente
        if linked_to is None:
            # No enlazar automáticamente, hacer gráfico estático
            return self
        
        # Buscar vista principal especificada
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            raise ValueError(f"Vista principal '{linked_to}' no existe. Agrega la vista principal primero.")
        
        def update(items, count):
            df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
            if df is None:
                return
            try:
                MatrixLayout.map_radviz(letter, df, features=features, class_col=class_col, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self
    
    def add_star_coordinates(self, letter, features=None, class_col=None, linked_to=None, **kwargs):
        """
        Agrega Star Coordinates: similar a RadViz pero los nodos pueden moverse libremente por toda el área.
        
        Args:
            letter: Letra del layout ASCII
            features: Lista de columnas numéricas a usar (opcional, usa todas las numéricas por defecto)
            class_col: Columna para categorías (colorear puntos)
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        MatrixLayout = _get_matrix_layout()
        if not (HAS_PANDAS and isinstance(self._data, pd.DataFrame)):
            raise ValueError("add_star_coordinates requiere DataFrame")
        MatrixLayout.map_star_coordinates(letter, self._data, features=features, class_col=class_col, **kwargs)
        
        # Solo registrar callback si linked_to está especificado explícitamente
        if linked_to is None:
            # No enlazar automáticamente, hacer gráfico estático
            return self
        
        # Buscar vista principal especificada
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            raise ValueError(f"Vista principal '{linked_to}' no existe. Agrega la vista principal primero.")
        
        def update(items, count):
            df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
            if df is None:
                return
            try:
                MatrixLayout.map_star_coordinates(letter, df, features=features, class_col=class_col, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self
    
    def add_parallel_coordinates(self, letter, dimensions=None, category_col=None, linked_to=None, **kwargs):
        """
        Agrega Parallel Coordinates Plot con ejes arrastrables y reordenables.
        
        Args:
            letter: Letra del layout ASCII
            dimensions: Lista de columnas numéricas a usar como ejes (opcional, usa todas las numéricas por defecto)
            category_col: Columna para categorías (colorear líneas)
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        MatrixLayout = _get_matrix_layout()
        if not (HAS_PANDAS and isinstance(self._data, pd.DataFrame)):
            raise ValueError("add_parallel_coordinates requiere DataFrame")
        
        # 🔒 CORRECCIÓN: Agregar identificador para que el evento se maneje correctamente
        kwargs['__view_letter__'] = letter
        kwargs['__is_primary_view__'] = False  # Parallel coordinates no es vista principal por defecto
        
        MatrixLayout.map_parallel_coordinates(letter, self._data, dimensions=dimensions, category_col=category_col, **kwargs)
        
        # 🔒 CORRECCIÓN: Registrar handler específico para parallel coordinates que formatee los datos correctamente
        def parallel_coords_handler(payload):
            """Handler específico para parallel coordinates que formatea los datos de manera clara"""
            event_letter = payload.get('__view_letter__')
            # Solo procesar si el evento viene de este parallel coordinates
            if event_letter and event_letter != letter:
                return
            
            items = payload.get('items', [])
            count = payload.get('count', len(items))
            
            if count == 0:
                print("📊 No hay elementos seleccionados")
                return
            
            # 🔒 CORRECCIÓN: Formatear datos de manera clara y legible
            print(f"\n📊 Selección: {count} elemento(s)")
            print("=" * 60)
            
            # Mostrar los primeros elementos (máximo 5 para parallel coordinates)
            display_count = min(count, 5)
            for i, item in enumerate(items[:display_count]):
                print(f"\n[{i+1}]")
                # Filtrar y mostrar solo las dimensiones y categoría
                excluded_keys = {'index', '_original_row', '_original_rows', '__scatter_letter__', 
                                 '__is_primary_view__', '__view_letter__', 'type'}
                
                # Ordenar las claves para mostrar dimensiones primero, luego categoría
                sorted_keys = sorted([k for k in item.keys() if k not in excluded_keys and not isinstance(item[k], (list, tuple, set, dict))])
                
                # Mostrar dimensiones primero
                for key in sorted_keys:
                    value = item[key]
                    # Formatear valores numéricos con 2 decimales
                    if isinstance(value, (int, float)):
                        if isinstance(value, float):
                            print(f"   - {key}: {value:.2f}")
                        else:
                            print(f"   - {key}: {value}")
                    else:
                        print(f"   - {key}: {value}")
            
            if count > display_count:
                print(f"\n... y {count - display_count} elemento(s) más")
            print("=" * 60)
        
        # Registrar el handler específico para parallel coordinates
        self._layout.on('select', parallel_coords_handler)
        
        # Solo registrar callback si linked_to está especificado explícitamente
        if linked_to is None:
            # No enlazar automáticamente, hacer gráfico estático
            return self
        
        # Buscar vista principal especificada
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            raise ValueError(f"Vista principal '{linked_to}' no existe. Agrega la vista principal primero.")
        
        def update(items, count):
            df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
            if df is None:
                return
            try:
                MatrixLayout.map_parallel_coordinates(letter, df, dimensions=dimensions, category_col=category_col, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self
    
    def add_confusion_matrix(self, letter, y_true_col=None, y_pred_col=None, linked_to=None, normalize=True, **kwargs):
        """
        Agrega una matriz de confusión enlazada que se actualiza automáticamente 
        cuando cambia la selección en un scatter plot.

        Args:
            letter: Letra del layout ASCII donde irá la matriz.
            y_true_col: Columna con las etiquetas reales.
            y_pred_col: Columna con las etiquetas predichas.
            linked_to: Letra del scatter plot que controla este gráfico.
            normalize: Si True, muestra proporciones en lugar de conteos.
            **kwargs: Parámetros adicionales para MatrixLayout.map_confusion_matrix().

        Requiere que los datos provengan de un DataFrame de pandas.
        """
        MatrixLayout = _get_matrix_layout()
        if not (HAS_PANDAS and isinstance(self._data, pd.DataFrame)):
            raise ValueError("add_confusion_matrix requiere un DataFrame de pandas")
        if y_true_col is None or y_pred_col is None:
            raise ValueError("Debes especificar y_true_col y y_pred_col")

        try:
            from sklearn.metrics import confusion_matrix
        except ImportError:
            raise ImportError("scikit-learn es necesario para add_confusion_matrix")

        # Función auxiliar para graficar
        def render_confusion(df):
            y_true = df[y_true_col]
            y_pred = df[y_pred_col]
            labels = sorted(list(set(y_true) | set(y_pred)))
            cm = confusion_matrix(y_true, y_pred, labels=labels, normalize='true' if normalize else None)
            cm_df = pd.DataFrame(cm, index=labels, columns=labels)
            MatrixLayout.map_heatmap(
                letter, cm_df.reset_index().melt(id_vars='index', var_name='Pred', value_name='Value'),
                x_col='Pred', y_col='index', value_col='Value',
                colorMap=kwargs.get('colorMap', 'Blues'),
                **kwargs
            )

        # Render inicial
        render_confusion(self._data)

        # Enlace a scatter seleccionado
        if not self._scatter_selection_models:
            return self
        scatter_letter = linked_to or list(self._scatter_selection_models.keys())[-1]
        sel = self._scatter_selection_models[scatter_letter]

        def update(items, count):
            if not items:
                render_confusion(self._data)
                return
            df_sel = pd.DataFrame(items) if isinstance(items[0], dict) else self._data
            try:
                render_confusion(df_sel)
            except Exception:
                pass

        sel.on_change(update)
        return self

    def add_kde(self, letter, column=None, bandwidth=None, linked_to=None, **kwargs):
        """Agrega KDE (Kernel Density Estimation) chart."""
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None:
            raise ValueError("Debe especificar 'column' para KDE")
        MatrixLayout.map_kde(letter, self._data, column=column, bandwidth=bandwidth, **kwargs)
        if linked_to:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                return self
            def update(items, count):
                df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
                if df is not None:
                    try:
                        MatrixLayout.map_kde(letter, df, column=column, bandwidth=bandwidth, **kwargs)
                    except Exception:
                        pass
            sel.on_change(update)
        return self
    
    def add_distplot(self, letter, column=None, bins=30, kde=True, rug=False, linked_to=None, **kwargs):
        """Agrega distribution plot (histograma + KDE)."""
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None:
            raise ValueError("Debe especificar 'column' para distplot")
        MatrixLayout.map_distplot(letter, self._data, column=column, bins=bins, kde=kde, rug=rug, **kwargs)
        if linked_to:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                return self
            def update(items, count):
                df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
                if df is not None:
                    try:
                        MatrixLayout.map_distplot(letter, df, column=column, bins=bins, kde=kde, rug=rug, **kwargs)
                    except Exception:
                        pass
            sel.on_change(update)
        return self
    
    def add_rug(self, letter, column=None, axis='x', linked_to=None, **kwargs):
        """Agrega rug plot."""
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None:
            raise ValueError("Debe especificar 'column' para rug plot")
        MatrixLayout.map_rug(letter, self._data, column=column, axis=axis, **kwargs)
        if linked_to:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                return self
            def update(items, count):
                df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
                if df is not None:
                    try:
                        MatrixLayout.map_rug(letter, df, column=column, axis=axis, **kwargs)
                    except Exception:
                        pass
            sel.on_change(update)
        return self
    
    def add_qqplot(self, letter, column=None, dist='norm', linked_to=None, **kwargs):
        """Agrega Q-Q plot."""
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None:
            raise ValueError("Debe especificar 'column' para Q-Q plot")
        MatrixLayout.map_qqplot(letter, self._data, column=column, dist=dist, **kwargs)
        if linked_to:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                return self
            def update(items, count):
                df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
                if df is not None:
                    try:
                        MatrixLayout.map_qqplot(letter, df, column=column, dist=dist, **kwargs)
                    except Exception:
                        pass
            sel.on_change(update)
        return self
    
    def add_ecdf(self, letter, column=None, linked_to=None, **kwargs):
        """Agrega ECDF (Empirical Cumulative Distribution Function) chart."""
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None:
            raise ValueError("Debe especificar 'column' para ECDF")
        MatrixLayout.map_ecdf(letter, self._data, column=column, **kwargs)
        if linked_to:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                return self
            def update(items, count):
                df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
                if df is not None:
                    try:
                        MatrixLayout.map_ecdf(letter, df, column=column, **kwargs)
                    except Exception:
                        pass
            sel.on_change(update)
        return self
    
    def add_ridgeline(self, letter, column=None, category_col=None, bandwidth=None, linked_to=None, **kwargs):
        """Agrega ridgeline plot (joy plot)."""
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None or category_col is None:
            raise ValueError("Debe especificar 'column' y 'category_col' para ridgeline")
        MatrixLayout.map_ridgeline(letter, self._data, column=column, category_col=category_col, bandwidth=bandwidth, **kwargs)
        if linked_to:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                return self
            def update(items, count):
                df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
                if df is not None:
                    try:
                        MatrixLayout.map_ridgeline(letter, df, column=column, category_col=category_col, bandwidth=bandwidth, **kwargs)
                    except Exception:
                        pass
            sel.on_change(update)
        return self
    
    def add_ribbon(self, letter, x_col=None, y1_col=None, y2_col=None, linked_to=None, **kwargs):
        """Agrega ribbon plot (área entre líneas con gradiente)."""
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if x_col is None or y1_col is None or y2_col is None:
            raise ValueError("Debe especificar 'x_col', 'y1_col' y 'y2_col' para ribbon")
        MatrixLayout.map_ribbon(letter, self._data, x_col=x_col, y1_col=y1_col, y2_col=y2_col, **kwargs)
        if linked_to:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                return self
            def update(items, count):
                df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
                if df is not None:
                    try:
                        MatrixLayout.map_ribbon(letter, df, x_col=x_col, y1_col=y1_col, y2_col=y2_col, **kwargs)
                    except Exception:
                        pass
            sel.on_change(update)
        return self
    
    def add_hist2d(self, letter, x_col=None, y_col=None, bins=20, linked_to=None, **kwargs):
        """Agrega 2D histogram."""
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if x_col is None or y_col is None:
            raise ValueError("Debe especificar 'x_col' y 'y_col' para hist2d")
        MatrixLayout.map_hist2d(letter, self._data, x_col=x_col, y_col=y_col, bins=bins, **kwargs)
        if linked_to:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                return self
            def update(items, count):
                df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
                if df is not None:
                    try:
                        MatrixLayout.map_hist2d(letter, df, x_col=x_col, y_col=y_col, bins=bins, **kwargs)
                    except Exception:
                        pass
            sel.on_change(update)
        return self
    
    def add_polar(self, letter, angle_col=None, radius_col=None, angle_unit='rad', linked_to=None, **kwargs):
        """Agrega polar plot."""
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if angle_col is None or radius_col is None:
            raise ValueError("Debe especificar 'angle_col' y 'radius_col' para polar plot")
        MatrixLayout.map_polar(letter, self._data, angle_col=angle_col, radius_col=radius_col, angle_unit=angle_unit, **kwargs)
        if linked_to:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                return self
            def update(items, count):
                df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
                if df is not None:
                    try:
                        MatrixLayout.map_polar(letter, df, angle_col=angle_col, radius_col=radius_col, angle_unit=angle_unit, **kwargs)
                    except Exception:
                        pass
            sel.on_change(update)
        return self
    
    def add_funnel(self, letter, stage_col=None, value_col=None, linked_to=None, **kwargs):
        """Agrega funnel plot."""
        MatrixLayout = _get_matrix_layout()
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if stage_col is None or value_col is None:
            raise ValueError("Debe especificar 'stage_col' y 'value_col' para funnel plot")
        MatrixLayout.map_funnel(letter, self._data, stage_col=stage_col, value_col=value_col, **kwargs)
        if linked_to:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                return self
            def update(items, count):
                df = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else None)
                if df is not None:
                    try:
                        MatrixLayout.map_funnel(letter, df, stage_col=stage_col, value_col=value_col, **kwargs)
                    except Exception:
                        pass
            sel.on_change(update)
        return self

    
    def display(self, ascii_layout=None):
        """
        Muestra el layout.
        
        IMPORTANTE: Solo llama este método UNA VEZ después de configurar todos los gráficos.
        Llamar display() múltiples veces causará duplicación de gráficos.
        
        El bar chart se actualiza automáticamente cuando seleccionas en el scatter plot,
        NO necesitas llamar display() nuevamente después de cada selección.
        """
        if ascii_layout:
            self._layout.ascii_layout = ascii_layout
        
        # Solo mostrar una vez - el bar chart se actualiza automáticamente vía JavaScript
        self._layout.display()
        return self

    # ==========================
    # Passthrough de Merge
    # ==========================
    def merge(self, letters=True):
        """Configura merge explícito (delegado a MatrixLayout interno)."""
        self._layout.merge(letters)
        return self

    def merge_all(self):
        """Activa merge para todas las letras."""
        self._layout.merge_all()
        return self

    def merge_off(self):
        """Desactiva merge."""
        self._layout.merge_off()
        return self

    def merge_only(self, letters):
        """Activa merge solo para las letras indicadas."""
        self._layout.merge_only(letters)
        return self
    
    @property
    def selection_widget(self):
        """
        Retorna el widget de selección para mostrar en Jupyter.
        
        Uso:
            display(layout.selection_widget)
        """
        if not HAS_WIDGETS:
            print("⚠️ ipywidgets no está instalado")
            return None
            
        if not hasattr(self.selection_model, '_widget'):
            # Crear widget visual
            import ipywidgets as widgets
            self.selection_model._widget = widgets.VBox([
                widgets.HTML('<h4>📊 Datos Seleccionados</h4>'),
                widgets.Label(value='Esperando selección...'),
                widgets.IntText(value=0, description='Cantidad:', disabled=True)
            ])
            
            # Observar cambios y actualizar widget
            def update_widget(change):
                items = change['new']
                count = len(items)
                
                label = self.selection_model._widget.children[1]
                counter = self.selection_model._widget.children[2]
                
                if count > 0:
                    label.value = f'✅ {count} elementos seleccionados'
                    counter.value = count
                else:
                    label.value = 'Esperando selección...'
                    counter.value = 0
            
            self.selection_model.observe(update_widget, names='items')
        
        return self.selection_model._widget
    
    @property
    def items(self):
        """Retorna los items seleccionados"""
        return self.selection_model.get_items()
    
    @property
    def selected_data(self):
        """
        Retorna los datos seleccionados (alias para items).
        Se actualiza automáticamente cuando se hace brush selection en el scatter plot.
        """
        return self.selection_model.get_items()
    
    @property
    def count(self):
        """Retorna el número de items seleccionados"""
        return self.selection_model.get_count()


# ==========================
# Utilidades compartidas
# ==========================
def _sanitize_for_json(obj):
    """Convierte recursivamente tipos numpy y no serializables a tipos JSON puros.
    (copia local para uso desde reactive.py)
    """
    try:
        import numpy as _np  # opcional
    except Exception:
        _np = None

    if obj is None:
        return None
    if isinstance(obj, (str, bool, int, float)):
        return int(obj) if type(obj).__name__ in ("int64", "int32") else (float(obj) if type(obj).__name__ in ("float32", "float64") else obj)
    if _np is not None:
        if isinstance(obj, _np.integer):
            return int(obj)
        if isinstance(obj, _np.floating):
            return float(obj)
        if isinstance(obj, _np.ndarray):
            return _sanitize_for_json(obj.tolist())
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(v) for v in obj]
    return str(obj)


