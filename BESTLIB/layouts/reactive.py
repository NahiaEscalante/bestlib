"""
ReactiveMatrixLayout - Layout reactivo para BESTLIB
Migrado desde reactive.py legacy a layouts/reactive.py según estructura modular
"""
try:
    import ipywidgets as widgets
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False
    widgets = None

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

# Importar desde módulos modulares
from .matrix import MatrixLayout
from ..reactive.selection import SelectionModel
from ..reactive.selection import _items_to_dataframe

class ReactiveMatrixLayout:
    """
    Versión reactiva de MatrixLayout que actualiza automáticamente los datos
    e integra LinkedViews dentro de la matriz ASCII.
    
    Uso:
        from BESTLIB.layouts import ReactiveMatrixLayout
        from BESTLIB.reactive import SelectionModel
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
            selection_model: Instancia de SelectionModel para reactividad (opcional, se crea uno nuevo si es None)
            figsize: Tamaño global de gráficos (width, height) en pulgadas o píxeles
            row_heights: Lista de alturas por fila (px o fr)
            col_widths: Lista de anchos por columna (px, fr, o ratios)
            gap: Espaciado entre celdas en píxeles (default: 12px)
            cell_padding: Padding de celdas en píxeles (default: 15px)
            max_width: Ancho máximo del layout en píxeles (default: 1200px)
        """
        # MatrixLayout ya está importado al nivel del módulo (línea 46)
        # No re-importar aquí para evitar problemas de caché
        
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
        
        # Modelo reactivo - importar SelectionModel de forma robusta
        # Estrategia: intentar múltiples formas de importar
        LocalSelectionModel = None
        
        # Estrategia 1: Import directo desde reactive.selection (más confiable)
        try:
            from ..reactive.selection import SelectionModel as SM_direct
            if SM_direct is not None:
                LocalSelectionModel = SM_direct
        except (ImportError, AttributeError, ModuleNotFoundError):
            pass
        
        # Estrategia 2: Si falla, intentar desde reactive.__init__
        if LocalSelectionModel is None:
            try:
                from ..reactive import SelectionModel as SM_reactive
                if SM_reactive is not None:
                    LocalSelectionModel = SM_reactive
            except (ImportError, AttributeError, ModuleNotFoundError):
                pass
        
        # Estrategia 3: Intentar desde BESTLIB.__init__ (puede tener caché)
        if LocalSelectionModel is None:
            try:
                from .. import SelectionModel as SM_init
                if SM_init is not None:
                    LocalSelectionModel = SM_init
            except (ImportError, AttributeError, ModuleNotFoundError):
                pass
        
        # Si todas las estrategias fallaron
        if LocalSelectionModel is None:
            raise ImportError(
                "SelectionModel no está disponible.\n"
                "Posibles soluciones:\n"
                "1. Reinicia el kernel de Jupyter (Kernel → Restart Kernel)\n"
                "2. Importa directamente: from BESTLIB.reactive.selection import SelectionModel\n"
                "3. O usa: from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel"
            )
        
        # Si selection_model es None, crear una nueva instancia
        if selection_model is None:
            self.selection_model = LocalSelectionModel()
        else:
            self.selection_model = selection_model
        
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
        self._selection_store = {}
    
    def set_data(self, data):
        """
        Establece los datos originales para todas las vistas enlazadas.
        
        Args:
            data: DataFrame de pandas o lista de diccionarios
        """
        self._data = data
        return self
    
    def _empty_selection(self):
        if HAS_PANDAS and pd is not None:
            return pd.DataFrame()
        return []
    
    def _extract_filtered_data(self, items):
        """
        Extrae datos filtrados desde items de selección.
        Maneja _original_rows, _original_row, y items directos.
        
        Args:
            items: Lista de items de selección
        
        Returns:
            DataFrame de pandas o lista de diccionarios con los datos filtrados
        """
        if not items:
            return self._data
        
        processed_items = []
        for item in items:
            if isinstance(item, dict):
                if '_original_rows' in item:
                    processed_items.extend(item['_original_rows'])
                elif '_original_row' in item:
                    processed_items.append(item['_original_row'])
                else:
                    processed_items.append(item)
            else:
                processed_items.append(item)
        
        if HAS_PANDAS and processed_items:
            import pandas as pd
            try:
                return pd.DataFrame(processed_items)
            except Exception:
                return processed_items
        
        return processed_items if processed_items else self._data
    
    def _register_chart(self, letter, chart_type, data, **kwargs):
        """
        Helper para registrar un chart en el layout interno usando el método de instancia.
        
        Args:
            letter: Letra del layout
            chart_type: Tipo de chart ('scatter', 'bar', 'histogram', etc.)
            data: Datos del chart
            **kwargs: Argumentos adicionales para el chart
        
        Returns:
            El spec generado
        """
        from ..charts import ChartRegistry
        chart = ChartRegistry.get(chart_type)
        spec = chart.get_spec(data, **kwargs)
        return self._layout._register_spec(letter, spec)
    
    def add_scatter(self, letter, data=None, x_col=None, y_col=None, category_col=None, interactive=True, selection_var=None, **kwargs):
        """
        Agrega un scatter plot a la matriz con soporte para DataFrames.
        
        Args:
            letter: Letra del layout ASCII donde irá el scatter plot
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            category_col: Nombre de columna para categorías (opcional)
            interactive: Si True, habilita brush selection
            selection_var: Nombre de variable Python donde guardar selecciones (ej: 'selected_data')
            **kwargs: Argumentos adicionales (colorMap, pointRadius, axes, etc.)
        
        Returns:
            self para encadenamiento
        """
        if data is not None:
            self._data = data
        elif self._data is None:
            raise ValueError("Debe proporcionar datos con data= o usar set_data() primero")
        
        # ✅ CORRECCIÓN CRÍTICA: Guardar selection_var si se especifica
        if selection_var:
            if not hasattr(self, '_selection_variables'):
                self._selection_variables = {}
            self._selection_variables[letter] = selection_var
            empty_value = self._empty_selection()
            self._selection_store[selection_var] = empty_value
            if self._debug or MatrixLayout._debug:
                df_type = "DataFrame" if HAS_PANDAS else "lista"
                print(f"📦 Variable '{selection_var}' creada para guardar selecciones de scatter '{letter}' como {df_type}")
        
        # Crear un SelectionModel específico para este scatter plot
        # Esto permite que cada scatter plot actualice solo sus bar charts asociados
        scatter_selection = SelectionModel()
        self._scatter_selection_models[letter] = scatter_selection
        
        # Crear un handler personalizado para este scatter plot específico
        # El handler se conecta directamente al layout principal pero filtra por letra
        from .matrix import MatrixLayout
        
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
                if self._debug or MatrixLayout._debug:
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
            
            # ✅ CORRECCIÓN: Guardar DataFrame en SelectionModel también
            data_to_update = items_df if items_df is not None and not (hasattr(items_df, 'empty') and items_df.empty) else items
            
            # Actualizar el SelectionModel específico de este scatter plot
            # Esto disparará los callbacks registrados (como update_histogram, update_boxplot)
            scatter_selection_capture.update(data_to_update)
            
            # IMPORTANTE: También actualizar el selection_model principal para que selected_data se actualice
            # Esto asegura que los datos seleccionados estén disponibles globalmente
            self.selection_model.update(data_to_update)
            
            # Actualizar también _selected_data con DataFrame para que el usuario pueda acceder fácilmente
            self._selected_data = items_df if items_df is not None else items
            
            # Guardar en variable Python si se especificó selection_var para este scatter
            if hasattr(self, '_selection_variables') and scatter_letter_capture in self._selection_variables:
                selection_var_name = self._selection_variables[scatter_letter_capture]
                self.set_selection(selection_var_name, items_df if items_df is not None else items)
        
        # Registrar handler en el layout principal
        # Nota: Usamos el mismo layout pero cada scatter tiene su propio SelectionModel
        # El JavaScript enviará __scatter_letter__ en el payload
        self._layout.on('select', scatter_handler)
        
        # Configurar el scatter plot en el mapping
        # IMPORTANTE: Agregar __scatter_letter__ ANTES de crear el spec para asegurar que esté disponible
        kwargs_with_identifier = kwargs.copy()
        kwargs_with_identifier['__scatter_letter__'] = letter
        kwargs_with_identifier['__selection_model_id__'] = id(scatter_selection)
        
        # ✅ CORRECCIÓN CRÍTICA: Asegurar que interactive esté explícitamente en kwargs
        # Esto garantiza que se propague al spec correctamente
        # IMPORTANTE: Remover interactive de kwargs si existe para evitar duplicados
        kwargs_with_identifier.pop('interactive', None)  # Remover si existe
        kwargs_with_identifier['interactive'] = interactive  # Agregar el valor correcto
        
        # Crear scatter plot spec con identificadores incluidos
        scatter_spec = self._register_chart(
            letter,
            'scatter',
            self._data,
            x_col=x_col,
            y_col=y_col,
            category_col=category_col,
            **kwargs_with_identifier  # ✅ interactive ya está aquí
        )
        
        # ✅ CORRECCIÓN CRÍTICA: Verificar que interactive esté en el spec final
        if 'interactive' not in scatter_spec or scatter_spec.get('interactive') is None:
            scatter_spec['interactive'] = interactive
            if self._debug or MatrixLayout._debug:
                print(f"⚠️ [ReactiveMatrixLayout] interactive no estaba en spec, agregado manualmente: {interactive}")
        
        # Asegurar que los identificadores estén en el spec guardado
        if scatter_spec:
            metadata = {
                '__scatter_letter__': letter,
                '__selection_model_id__': id(scatter_selection)
            }
            scatter_spec.update(metadata)
            self._layout.update_spec_metadata(letter, **metadata)
            
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
        from .matrix import MatrixLayout
        
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero para establecer los datos")
        
        # Determinar si será vista principal o enlazada
        if linked_to is None:
            # Verificar si hay vistas principales para auto-enlazar
            all_primary = {**self._scatter_selection_models, **self._primary_view_models}
            if interactive is None:
                if all_primary:
                    # Auto-enlazar a la última vista principal
                    linked_to = list(all_primary.keys())[-1]
                    interactive = False
                    is_primary = False
                    if self._debug or MatrixLayout._debug:
                        print(f"💡 Bar chart '{letter}' enlazado automáticamente a '{linked_to}'")
                else:
                    # No hay vistas principales, crear gráfico estático
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
                self._selection_store[selection_var] = self._empty_selection()
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
                
                # ✅ CORRECCIÓN CRÍTICA: Filtrado más flexible y robusto
                # Aceptar tanto __view_letter__ como __scatter_letter__ para compatibilidad
                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                
                # Si el evento tiene una letra específica, verificar que coincida
                if event_letter is not None:
                    if event_letter != letter:
                        if self._debug or MatrixLayout._debug:
                            print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: esperado '{letter}', recibido '{event_letter}'")
                        return
                else:
                    # Si no hay letra en el payload, podría ser un evento genérico
                    # En este caso, solo procesar si el payload tiene items y parece ser para este bar chart
                    # Verificar por tipo de gráfico
                    graph_type = payload.get('__graph_type__', '')
                    if graph_type != 'bar' and graph_type != '':
                        if self._debug or MatrixLayout._debug:
                            print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: tipo de gráfico '{graph_type}' no es 'bar'")
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
                        self.set_selection(selection_var, items_df if items_df is not None else items)
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
        
        # Inicializar primary_letter siempre
        primary_letter = None
        
        # Si es vista enlazada, determinar a qué vista principal enlazar
        if not is_primary:
            # CRÍTICO: Si linked_to es None, NO enlazar automáticamente (gráfico estático)
            if linked_to is None:
                # Crear bar chart estático sin enlazar
                self._register_chart(letter, 'bar', self._data, category_col=category_col, value_col=value_col, **kwargs)
                return self
            
            # Validar que linked_to no sea el string "None"
            if isinstance(linked_to, str) and linked_to.lower() == 'none':
                linked_to = None
                # Crear bar chart estático sin enlazar
                self._register_chart(letter, 'bar', self._data, category_col=category_col, value_col=value_col, **kwargs)
                return self
            
            # Buscar en scatter plots primero (compatibilidad hacia atrás)
            if linked_to in self._scatter_selection_models:
                primary_letter = linked_to
                primary_selection = self._scatter_selection_models[primary_letter]
            elif linked_to in self._primary_view_models:
                primary_letter = linked_to
                primary_selection = self._primary_view_models[primary_letter]
            else:
                # Si linked_to está especificado pero no existe, lanzar error con información útil
                available_scatters = list(self._scatter_selection_models.keys())
                available_primary = list(self._primary_view_models.keys())
                all_available = available_scatters + available_primary
                
                if self._debug or MatrixLayout._debug:
                    print(f"❌ [ReactiveMatrixLayout] Vista principal '{linked_to}' no existe para barchart '{letter}'")
                    print(f"   - Scatter plots disponibles: {available_scatters}")
                    print(f"   - Vistas principales disponibles: {available_primary}")
                    print(f"   - Todas las vistas: {all_available}")
                
                error_msg = f"Vista principal '{linked_to}' no existe. "
                if all_available:
                    error_msg += f"Vistas disponibles: {all_available}. "
                error_msg += "Agrega la vista principal primero (ej: add_scatter('A', ...) o add_barchart('B', interactive=True, ...))."
                raise ValueError(error_msg)
        
        # Guardar el enlace (solo si es vista enlazada y primary_letter está definido)
        if not is_primary and primary_letter is not None:
            self._barchart_to_scatter[letter] = primary_letter
            # Agregar __linked_to__ al spec para indicadores visuales en JavaScript
            kwargs['__linked_to__'] = primary_letter
        else:
            # Si es vista principal o no hay enlace, remover __linked_to__
            kwargs.pop('__linked_to__', None)  # Remover si existe
        
        # Crear bar chart inicial con todos los datos
        self._register_chart(
            letter,
            'bar',
            self._data,
            category_col=category_col,
            value_col=value_col,
            **kwargs
        )
        
        # ✅ CORRECCIÓN CRÍTICA: Asegurar que __view_letter__ esté en el spec guardado
        # Esto es necesario para que JavaScript pueda identificar el gráfico correctamente
        if letter in self._layout._map:
            if is_primary:
                self._layout.update_spec_metadata(
                    letter,
                    __view_letter__=letter,
                    __is_primary_view__=True,
                    interactive=True
                )
                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Bar chart '{letter}' configurado como vista principal con __view_letter__={letter}")
            elif linked_to:
                self._layout.update_spec_metadata(letter, __linked_to__=linked_to)
        
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
        
        # Inicializar update_barchart para evitar UnboundLocalError
        update_barchart = None
        
        # Si es vista enlazada, configurar callback de actualización
        if not is_primary:
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
                        
                        // CRÍTICO: Usar dimensiones fijas para evitar crecimiento acumulativo
                        // Guardar dimensiones originales en la primera ejecución
                        if (!targetCell.dataset.originalWidth) {{
                            const svg = targetCell.querySelector('svg');
                            if (svg) {{
                                targetCell.dataset.originalWidth = svg.getAttribute('width') || '400';
                                targetCell.dataset.originalHeight = svg.getAttribute('height') || '350';
                            }} else {{
                                targetCell.dataset.originalWidth = '400';
                                targetCell.dataset.originalHeight = '350';
                            }}
                        }}
                        const width = parseInt(targetCell.dataset.originalWidth);
                        const height = parseInt(targetCell.dataset.originalHeight);
                        
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
            # Solo si update_barchart fue definido (es decir, si es vista enlazada)
            if update_barchart is not None:
                primary_selection.on_change(update_barchart)
                
                # Marcar como callback registrado
                self._barchart_callbacks[letter] = update_barchart
        
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
        from .matrix import MatrixLayout
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
                self._selection_store[selection_var] = self._empty_selection()
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de grouped bar chart '{letter}' como {df_type}")
            
            def grouped_handler(payload):
                # ✅ CORRECCIÓN CRÍTICA: Filtrado más flexible y robusto
                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                
                # Si el evento tiene una letra específica, verificar que coincida
                if event_letter is not None:
                    if event_letter != letter:
                        if self._debug or MatrixLayout._debug:
                            print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: esperado '{letter}', recibido '{event_letter}'")
                        return
                else:
                    # Si no hay letra en el payload, verificar por tipo de gráfico
                    graph_type = payload.get('__graph_type__', '')
                    if graph_type != 'grouped_bar' and graph_type != '':
                        if self._debug or MatrixLayout._debug:
                            print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: tipo de gráfico '{graph_type}' no es 'grouped_bar'")
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
                    self.set_selection(selection_var, items_df if items_df is not None else items)
                    if self._debug or MatrixLayout._debug:
                        count_msg = f"{len(items_df)} filas" if items_df is not None and hasattr(items_df, '__len__') else f"{len(items)} items"
                        print(f"💾 Selección guardada en variable '{selection_var}' como DataFrame: {count_msg}")
            
            self._layout.on('select', grouped_handler)
            
            kwargs['__view_letter__'] = letter
            kwargs['__is_primary_view__'] = True
            kwargs['interactive'] = True
        
        # Crear gráfico inicial - usar registro directo para evitar problemas de instancia
        self._register_chart(letter, 'grouped_bar', self._data, main_col=main_col, sub_col=sub_col, value_col=value_col, **kwargs)
        
        # ✅ CORRECCIÓN CRÍTICA: Asegurar que __view_letter__ esté en el spec guardado
        if letter in self._layout._map:
            if is_primary:
                self._layout.update_spec_metadata(
                    letter,
                    __view_letter__=letter,
                    __is_primary_view__=True,
                    interactive=True
                )
                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Grouped bar chart '{letter}' configurado como vista principal con __view_letter__={letter}")
            elif linked_to:
                self._layout.update_spec_metadata(letter, __linked_to__=linked_to)
        
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
                    self._register_chart(letter, 'grouped_bar', data_to_use, main_col=main_col, sub_col=sub_col, value_col=value_col, **kwargs)
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
        from .matrix import MatrixLayout
        
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
        from .matrix import MatrixLayout
        
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
        
        # CRÍTICO: Inicializar initial_data SIEMPRE al principio para evitar UnboundLocalError
        initial_data = self._data
        
        # Si es vista principal, crear su propio SelectionModel
        if is_primary:
            histogram_selection = SelectionModel()
            self._primary_view_models[letter] = histogram_selection
            self._primary_view_types[letter] = 'histogram'
            
            # Guardar variable de selección si se especifica
            if selection_var:
                self._selection_variables[letter] = selection_var
                self._selection_store[selection_var] = self._empty_selection()
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de histogram '{letter}' como {df_type}")
            
            # Crear handler para eventos de selección del histogram
            def histogram_handler(payload):
                """Handler que actualiza el SelectionModel de este histogram"""
                # ✅ CORRECCIÓN CRÍTICA: Filtrado más flexible y robusto
                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                
                # Si el evento tiene una letra específica, verificar que coincida
                if event_letter is not None:
                    if event_letter != letter:
                        if self._debug or MatrixLayout._debug:
                            print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: esperado '{letter}', recibido '{event_letter}'")
                        return
                else:
                    # Si no hay letra en el payload, verificar por tipo de gráfico
                    graph_type = payload.get('__graph_type__', '')
                    if graph_type != 'histogram' and graph_type != '':
                        if self._debug or MatrixLayout._debug:
                            print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: tipo de gráfico '{graph_type}' no es 'histogram'")
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
                    self.set_selection(selection_var, items_df if items_df is not None else items)
                    if self._debug or MatrixLayout._debug:
                        count_msg = f"{len(items_df)} filas" if items_df is not None and hasattr(items_df, '__len__') else f"{len(items)} items"
                        print(f"💾 Selección guardada en variable '{selection_var}' como DataFrame: {count_msg}")
            
            self._layout.on('select', histogram_handler)
            
            kwargs['__view_letter__'] = letter
            kwargs['__is_primary_view__'] = True
            kwargs['interactive'] = True
        
        # Si es vista principal, crear histograma y retornar
        # ✅ DEBUG SIEMPRE: Verificar si es vista principal
        print(f"🔍 [add_histogram] Verificando si es vista principal para '{letter}'")
        print(f"   - is_primary: {is_primary}")
        print(f"   - interactive: {interactive}")
        print(f"   - linked_to: {linked_to}")
        
        if is_primary:
            # ✅ DEBUG: Verificar datos antes de crear histograma
            print(f"🔍 [ReactiveMatrixLayout] Creando histogram '{letter}' como vista principal")
            print(f"   - initial_data type: {type(initial_data)}")
            if HAS_PANDAS and hasattr(initial_data, 'shape'):
                print(f"   - initial_data shape: {initial_data.shape}")
                print(f"   - column '{column}' exists: {column in initial_data.columns if hasattr(initial_data, 'columns') else 'N/A'}")
            elif isinstance(initial_data, list):
                print(f"   - initial_data length: {len(initial_data)}")
            
            # ✅ CORRECCIÓN CRÍTICA: Asegurar que xLabel y yLabel se pasen correctamente
            # map_histogram usa value_col, no column, así que asegurar que esté en kwargs si se especificó
            histogram_kwargs = kwargs.copy()
            if 'xLabel' in histogram_kwargs:
                histogram_kwargs['xLabel'] = histogram_kwargs['xLabel']
            if 'yLabel' in histogram_kwargs:
                histogram_kwargs['yLabel'] = histogram_kwargs['yLabel']
            
            # ✅ DEBUG: Verificar antes de llamar a map_histogram
            print(f"🔍 [add_histogram] ANTES de llamar map_histogram:")
            print(f"   - letter: {letter}")
            print(f"   - initial_data type: {type(initial_data)}")
            print(f"   - initial_data is None: {initial_data is None}")
            if hasattr(initial_data, 'shape'):
                print(f"   - initial_data shape: {initial_data.shape}")
            print(f"   - column: {column}")
            print(f"   - bins: {bins}")
            print(f"   - histogram_kwargs keys: {list(histogram_kwargs.keys())}")
            
            # ✅ CORRECCIÓN CRÍTICA: Crear histogram usando el método de instancia
            try:
                spec = self._register_chart(
                    letter,
                    'histogram',
                    initial_data,
                    value_col=column,
                    bins=bins,
                    **histogram_kwargs
                )
                print(f"🔍 [add_histogram] DESPUÉS de crear histogram:")
                print(f"   - spec type: {type(spec)}")
                print(f"   - spec keys: {list(spec.keys()) if isinstance(spec, dict) else 'N/A'}")
                if isinstance(spec, dict):
                    print(f"   - spec['data'] length: {len(spec.get('data', []))}")
            except Exception as e:
                print(f"❌ [add_histogram] ERROR al crear histogram: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # ✅ CORRECCIÓN CRÍTICA: Asegurar que __view_letter__ esté en el spec guardado
            # Usar el spec retornado en lugar de acceder directamente a _map para evitar problemas de sincronización
            if spec and letter in self._layout._map:
                self._layout.update_spec_metadata(
                    letter,
                    __view_letter__=letter,
                    __is_primary_view__=True,
                    interactive=True
                )
                # ✅ DEBUG: Verificar que el spec tiene datos
                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Histogram '{letter}' configurado como vista principal con __view_letter__={letter}")
                    print(f"   - Spec type: {self._layout._map[letter].get('type')}")
                    print(f"   - Data length: {len(self._layout._map[letter].get('data', []))}")
                    data = self._layout._map[letter].get('data', [])
                    if data:
                        print(f"   - First bin: bin={data[0].get('bin')}, count={data[0].get('count')}")
                    else:
                        print(f"   - ⚠️ WARNING: Histogram data está vacío!")
            else:
                if self._debug or MatrixLayout._debug:
                    print(f"❌ [ReactiveMatrixLayout] ERROR: Histogram '{letter}' no se guardó en _map después de map_histogram")
                    print(f"   - spec is None: {spec is None}")
                    print(f"   - letter in _map: {letter in self._layout._map}")
            
            return self
        
        # Inicializar primary_letter siempre
        primary_letter = None
        
        # Si es vista enlazada, determinar a qué vista principal enlazar
        if not is_primary:
            # CRÍTICO: Si linked_to es None, NO enlazar automáticamente (gráfico estático)
            if linked_to is None:
                # Crear histograma estático sin enlazar
                self._register_chart(
                    letter,
                    'histogram',
                    initial_data,
                    value_col=column,
                    bins=bins,
                    **kwargs
                )
                return self
            
            # Validar que linked_to no sea el string "None"
            if isinstance(linked_to, str) and linked_to.lower() == 'none':
                linked_to = None
                # Crear histograma estático sin enlazar
                self._register_chart(
                    letter,
                    'histogram',
                    initial_data,
                    value_col=column,
                    bins=bins,
                    **kwargs
                )
                return self
            
            # Buscar en scatter plots primero (compatibilidad hacia atrás)
            if linked_to in self._scatter_selection_models:
                primary_letter = linked_to
                primary_selection = self._scatter_selection_models[primary_letter]
            elif linked_to in self._primary_view_models:
                primary_letter = linked_to
                primary_selection = self._primary_view_models[primary_letter]
            else:
                # Si linked_to está especificado pero no existe, lanzar error con información útil
                available_scatters = list(self._scatter_selection_models.keys())
                available_primary = list(self._primary_view_models.keys())
                all_available = available_scatters + available_primary
                
                if self._debug or MatrixLayout._debug:
                    print(f"❌ [ReactiveMatrixLayout] Vista principal '{linked_to}' no existe para histogram '{letter}'")
                    print(f"   - Scatter plots disponibles: {available_scatters}")
                    print(f"   - Vistas principales disponibles: {available_primary}")
                    print(f"   - Todas las vistas: {all_available}")
                
                error_msg = f"Vista principal '{linked_to}' no existe. "
                if all_available:
                    error_msg += f"Vistas disponibles: {all_available}. "
                error_msg += "Agrega la vista principal primero (ej: add_scatter('A', ...) o add_barchart('B', interactive=True, ...))."
                raise ValueError(error_msg)
            
            # Agregar __linked_to__ al spec para indicadores visuales en JavaScript (solo si hay enlace)
            if primary_letter is not None:
                kwargs['__linked_to__'] = primary_letter
            else:
                kwargs.pop('__linked_to__', None)  # Remover si existe
            
            # CRÍTICO: Si ya hay una selección activa en la vista principal, usar esos datos desde el inicio
            if primary_letter is not None:
                # Verificar si hay una selección activa
                current_items = primary_selection.get_items()
                if current_items and len(current_items) > 0:
                    # Procesar items para obtener DataFrame filtrado
                    processed_items = []
                    for item in current_items:
                        if isinstance(item, dict):
                            if '_original_rows' in item and isinstance(item['_original_rows'], list):
                                processed_items.extend(item['_original_rows'])
                            elif '_original_row' in item:
                                processed_items.append(item['_original_row'])
                            else:
                                processed_items.append(item)
                        else:
                            processed_items.append(item)
                    
                    if processed_items:
                        if HAS_PANDAS:
                            pd_module = globals().get('pd')
                            if pd_module is None:
                                import sys
                                if 'pandas' in sys.modules:
                                    pd_module = sys.modules['pandas']
                                else:
                                    import pandas as pd_module
                                    globals()['pd'] = pd_module
                            try:
                                if isinstance(processed_items[0], dict):
                                    initial_data = pd_module.DataFrame(processed_items)
                                else:
                                    initial_data = pd_module.DataFrame(processed_items)
                            except Exception:
                                initial_data = self._data
                        else:
                            initial_data = processed_items
                    
                    if self._debug or MatrixLayout._debug:
                        print(f"📊 Histogram '{letter}' inicializado con {len(processed_items) if processed_items else len(self._data)} items (hay selección activa)")
            
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
                from .matrix import MatrixLayout
                
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
                                # (esto es común cuando viene de scatter plot)
                                else:
                                    processed_items.append(item)
                            else:
                                processed_items.append(item)
                        
                        if processed_items:
                            if HAS_PANDAS:
                                import pandas as pd
                                # Intentar crear DataFrame desde los items procesados
                                try:
                                    if isinstance(processed_items[0], dict):
                                        data_to_use = pd.DataFrame(processed_items)
                                    else:
                                        # Si no son diccionarios, intentar convertir
                                        data_to_use = pd.DataFrame(processed_items)
                                except Exception as e:
                                    if self._debug or MatrixLayout._debug:
                                        print(f"⚠️ Error creando DataFrame desde items: {e}")
                                    data_to_use = self._data
                            else:
                                data_to_use = processed_items
                        else:
                            data_to_use = self._data
                    else:
                        # Si no hay items, usar todos los datos (selección desactivada)
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
                    
                    # Asegurar que pd esté disponible (usar globals para evitar UnboundLocalError)
                    if HAS_PANDAS:
                        pd_module = globals().get('pd')
                        if pd_module is None:
                            import sys
                            if 'pandas' in sys.modules:
                                pd_module = sys.modules['pandas']
                            else:
                                import pandas as pd_module
                                globals()['pd'] = pd_module
                        if pd_module is not None and isinstance(data_to_use, pd_module.DataFrame):
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
                        
                        // CRÍTICO: Calcular dimensiones ANTES de limpiar el innerHTML
                        // para evitar que la celda pierda sus dimensiones
                        const dims = window.getChartDimensions ? 
                            window.getChartDimensions(targetCell, {{ type: 'histogram' }}, 400, 350) :
                            {{ width: Math.max(targetCell.clientWidth || 400, 200), height: 350 }};
                        const width = dims.width;
                        const height = dims.height;
                        const margin = {{ top: 20, right: 20, bottom: 40, left: 50 }};
                        const chartWidth = width - margin.left - margin.right;
                        const chartHeight = height - margin.top - margin.bottom;
                        
                        // CRÍTICO: Establecer altura mínima y máxima explícitamente en la celda
                        // ANTES de limpiar el innerHTML para prevenir expansión infinita
                        targetCell.style.minHeight = height + 'px';
                        targetCell.style.maxHeight = height + 'px';
                        targetCell.style.height = height + 'px';
                        targetCell.style.overflow = 'hidden';
                        
                        // CRÍTICO: Limpiar solo después de establecer dimensiones
                        targetCell.innerHTML = '';
                        
                        const data = {hist_data_json};
                        
                        if (data.length === 0) {{
                            targetCell.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos</div>';
                            return;
                        }}
                        
                        // CRÍTICO: Establecer dimensiones fijas en el SVG para prevenir expansión infinita
                        const svg = window.d3.select(targetCell)
                            .append('svg')
                            .attr('width', width)
                            .attr('height', height)
                            .style('max-height', height + 'px')
                            .style('overflow', 'hidden')
                            .style('display', 'block');
                        
                        const g = svg.append('g')
                            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
                        
                        const x = window.d3.scaleBand()
                            .domain(data.map(d => d.bin))
                            .range([0, chartWidth])
                            .padding(0.1);
                        
                        const y = window.d3.scaleLinear()
                            .domain([0, window.d3.max(data, d => d.count) || 100])
                            .nice()
                            .range([chartHeight, 0]);
                        
                        // IMPORTANTE: Agregar event listeners a las barras para interactividad
                        const bars = g.selectAll('.bar')
                            .data(data)
                            .enter()
                            .append('rect')
                            .attr('class', 'bar')
                            .attr('x', d => x(d.bin))
                            .attr('y', chartHeight)
                            .attr('width', x.bandwidth())
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
                            const xAxis = g.append('g')
                                .attr('transform', `translate(0,${{chartHeight}})`)
                                .call(window.d3.axisBottom(x));
                            
                            const yAxis = g.append('g')
                                .call(window.d3.axisLeft(y));
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
            
            # CRÍTICO: Si ya hay una selección activa en la vista principal, usar esos datos desde el inicio
            initial_data = self._data
            if not is_primary and primary_letter is not None:
                # Verificar si hay una selección activa
                current_items = primary_selection.get_items()
                if current_items and len(current_items) > 0:
                    # Procesar items para obtener DataFrame filtrado
                    processed_items = []
                    for item in current_items:
                        if isinstance(item, dict):
                            if '_original_rows' in item and isinstance(item['_original_rows'], list):
                                processed_items.extend(item['_original_rows'])
                            elif '_original_row' in item:
                                processed_items.append(item['_original_row'])
                            else:
                                processed_items.append(item)
                        else:
                            processed_items.append(item)
                    
                    if processed_items:
                        if HAS_PANDAS:
                            import pandas as pd
                            try:
                                if isinstance(processed_items[0], dict):
                                    initial_data = pd.DataFrame(processed_items)
                                else:
                                    initial_data = pd.DataFrame(processed_items)
                            except Exception:
                                initial_data = self._data
                        else:
                            initial_data = processed_items
                    
                    if self._debug or MatrixLayout._debug:
                        print(f"📊 Histogram '{letter}' inicializado con {len(processed_items) if processed_items else len(self._data)} items (hay selección activa)")
        
        # Crear histograma inicial con datos filtrados si hay selección, o todos los datos si no
        # (Solo para vistas enlazadas, las vistas principales ya se crearon arriba)
        kwargs_with_linked = kwargs.copy()
        if linked_to:
            kwargs_with_linked['__linked_to__'] = linked_to
        
        self._register_chart(
            letter,
            'histogram',
            initial_data,
            value_col=column,
            bins=bins,
            **kwargs_with_linked
        )
        
        return self
    
    def add_boxplot(self, letter, column=None, category_col=None, linked_to=None, interactive=None, selection_var=None, **kwargs):
        """
        Agrega un boxplot que puede ser vista principal o enlazada.
        
        Args:
            letter: Letra del layout ASCII donde irá el boxplot
            column: Nombre de columna numérica para el boxplot
            category_col: Nombre de columna de categorías (opcional, para boxplot por categoría)
            linked_to: Letra de la vista principal que debe actualizar este boxplot (opcional)
                      Si no se especifica y interactive=True, este boxplot será vista principal
            interactive: Si True, permite seleccionar cajas. Si es None, se infiere de linked_to
            selection_var: Nombre de variable Python donde guardar selecciones (ej: 'selected_box')
            **kwargs: Argumentos adicionales (color, axes, etc.)
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero para establecer los datos")
        
        if column is None:
            raise ValueError("Debe especificar 'column' para el boxplot")
        
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
            boxplot_selection = SelectionModel()
            self._primary_view_models[letter] = boxplot_selection
            self._primary_view_types[letter] = 'boxplot'
            
            # Guardar variable de selección si se especifica
            if selection_var:
                self._selection_variables[letter] = selection_var
                self._selection_store[selection_var] = self._empty_selection()
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de boxplot '{letter}' como {df_type}")
            
            # Crear handler para eventos de selección del boxplot
            def boxplot_handler(payload):
                """Handler que actualiza el SelectionModel de este boxplot"""
                # ✅ CORRECCIÓN CRÍTICA: Filtrado más flexible y robusto
                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                
                # Si el evento tiene una letra específica, verificar que coincida
                if event_letter is not None:
                    if event_letter != letter:
                        if self._debug or MatrixLayout._debug:
                            print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: esperado '{letter}', recibido '{event_letter}'")
                        return
                else:
                    # Si no hay letra en el payload, verificar por tipo de gráfico
                    graph_type = payload.get('__graph_type__', '')
                    if graph_type != 'boxplot' and graph_type != '':
                        if self._debug or MatrixLayout._debug:
                            print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: tipo de gráfico '{graph_type}' no es 'boxplot'")
                        return
                
                items = payload.get('items', [])
                
                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Evento recibido para boxplot '{letter}': {len(items)} items")
                
                # Convertir items a DataFrame antes de guardar
                items_df = _items_to_dataframe(items)
                
                boxplot_selection.update(items)
                self.selection_model.update(items)
                self._selected_data = items_df if items_df is not None else items
                
                # Guardar en variable Python si se especificó (como DataFrame)
                if selection_var:
                    self.set_selection(selection_var, items_df if items_df is not None else items)
                    if self._debug or MatrixLayout._debug:
                        count_msg = f"{len(items_df)} filas" if items_df is not None and hasattr(items_df, '__len__') else f"{len(items)} items"
                        print(f"💾 Selección guardada en variable '{selection_var}' como DataFrame: {count_msg}")
            
            self._layout.on('select', boxplot_handler)
            
            kwargs['__view_letter__'] = letter
            kwargs['__is_primary_view__'] = True
            kwargs['interactive'] = True
        
        # Verificar si ya existe un callback para este boxplot (evitar duplicados)
        if letter in self._boxplot_callbacks:
            if self._debug or MatrixLayout._debug:
                print(f"⚠️ Boxplot para '{letter}' ya está registrado. Ignorando registro duplicado.")
            return self
        
        # Si es vista principal, crear boxplot y retornar
        if is_primary:
            self._register_chart(
                letter,
                'boxplot',
                self._data,
                category_col=category_col,
                value_col=column,
                **kwargs
            )
            
            # ✅ CORRECCIÓN CRÍTICA: Asegurar que __view_letter__ esté en el spec guardado
            if letter in self._layout._map:
                self._layout.update_spec_metadata(
                    letter,
                    __view_letter__=letter,
                    __is_primary_view__=True,
                    interactive=True
                )
                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Boxplot '{letter}' configurado como vista principal con __view_letter__={letter}")
            
            return self
        
        # Determinar a qué vista principal enlazar (solo si es vista enlazada)
        primary_letter = None  # Inicializar siempre
        
        if linked_to is not None:
            # Validar que linked_to no sea el string "None"
            if isinstance(linked_to, str) and linked_to.lower() == 'none':
                linked_to = None
            else:
                # Buscar en scatter plots primero (compatibilidad hacia atrás)
                if linked_to in self._scatter_selection_models:
                    primary_letter = linked_to
                    primary_selection = self._scatter_selection_models[primary_letter]
                elif linked_to in self._primary_view_models:
                    primary_letter = linked_to
                    primary_selection = self._primary_view_models[primary_letter]
                else:
                    # Error con información detallada
                    available_scatters = list(self._scatter_selection_models.keys())
                    available_primary = list(self._primary_view_models.keys())
                    all_available = available_scatters + available_primary
                    
                    if self._debug or MatrixLayout._debug:
                        print(f"❌ [ReactiveMatrixLayout] Vista principal '{linked_to}' no existe para boxplot '{letter}'")
                        print(f"   - Scatter plots disponibles: {available_scatters}")
                        print(f"   - Vistas principales disponibles: {available_primary}")
                        print(f"   - Todas las vistas: {all_available}")
                    
                    error_msg = f"Vista principal '{linked_to}' no existe. "
                    if all_available:
                        error_msg += f"Vistas disponibles: {all_available}. "
                    error_msg += "Agrega la vista principal primero (ej: add_scatter('A', ...) o add_barchart('B', interactive=True, ...))."
                    raise ValueError(error_msg)
        
        if linked_to is None:
            # Si no se especifica, usar la última vista principal disponible
            all_primary = {**self._scatter_selection_models, **self._primary_view_models}
            if not all_primary:
                # Si no hay vistas principales, crear boxplot estático
                self._register_chart(
                    letter,
                    'boxplot',
                    self._data,
                    category_col=category_col,
                    value_col=column,
                    **kwargs
                )
                return self
            primary_letter = list(all_primary.keys())[-1]
            primary_selection = all_primary[primary_letter]
            if self._debug or MatrixLayout._debug:
                print(f"💡 Boxplot '{letter}' enlazado automáticamente a vista principal '{primary_letter}'")
        
        # Agregar __linked_to__ al spec para indicadores visuales en JavaScript (solo si hay enlace)
        if primary_letter is not None:
            kwargs['__linked_to__'] = primary_letter
        else:
            kwargs.pop('__linked_to__', None)  # Remover si existe
        
        # Crear boxplot inicial usando el método de instancia
        self._register_chart(
            letter,
            'boxplot',
            self._data,
            category_col=category_col,
            value_col=column,
            **kwargs
        )
        
        # ✅ CORRECCIÓN CRÍTICA: Asegurar que __linked_to__ esté en el spec guardado
        if letter in self._layout._map and primary_letter is not None:
            self._layout.update_spec_metadata(letter, __linked_to__=primary_letter)
        
        # Guardar parámetros
        boxplot_params = {
            'letter': letter,
            'column': column,
            'category_col': category_col,
            'kwargs': kwargs.copy(),
            'layout_div_id': self._layout.div_id
            }
        
        # Función de actualización del boxplot (con actualización del DOM)
        def update_boxplot(items, count):
            """Actualiza el boxplot cuando cambia la selección"""
            if self._debug or MatrixLayout._debug:
                print(f"   🔄 Boxplot '{letter}' callback ejecutándose con {count} items")
            
            try:
                # Usar el helper para extraer datos filtrados
                data_to_use = self._extract_filtered_data(items)
                
                # Regenerar spec con datos filtrados
                kwargs_update = boxplot_params['kwargs'].copy()
                if primary_letter is not None:
                    kwargs_update['__linked_to__'] = primary_letter
                
                # Usar el método de instancia para registrar el spec actualizado
                self._register_chart(
                    letter,
                    'boxplot',
                    data_to_use,
                    category_col=category_col,
                    value_col=column,
                    **kwargs_update
                )
                
                # CRÍTICO: Actualizar el DOM con JavaScript
                spec = self._layout._map.get(letter)
                if spec and spec.get('data'):
                    import json
                    from IPython.display import Javascript, display
                    
                    # Preparar datos para JavaScript
                    box_data_json = json.dumps(spec['data'])
                    title = spec.get('title', '')
                    x_label = spec.get('xLabel', '')
                    y_label = spec.get('yLabel', '')
                    
                    # JavaScript para actualizar el boxplot
                    div_id = boxplot_params.get('layout_div_id', '')
                    js_update = f"""
                    (function() {{
                        setTimeout(function() {{
                            // Buscar celda por data-letter
                            let container = document.getElementById('{div_id}');
                            if (!container) container = document;
                            let targetCell = container.querySelector('.matrix-cell[data-letter="{letter}"]');
                            if (!targetCell) targetCell = document.querySelector('.matrix-cell[data-letter="{letter}"]');
                            if (!targetCell || !window.d3) return;
                            
                            // Obtener dimensiones originales
                            const svg = d3.select(targetCell).select('svg');
                            if (svg.empty()) return;
                        
                        const originalWidth = parseInt(svg.attr('width')) || 400;
                        const originalHeight = parseInt(svg.attr('height')) || 300;
                        
                        // Limpiar contenido anterior
                        svg.selectAll('*').remove();
                        
                        // Datos del boxplot - normalizar lower/upper a min/max
                        const rawData = {box_data_json};
                        if (!rawData || rawData.length === 0) return;
                        const boxData = rawData.map(d => ({{
                            category: d.category,
                            min: d.min !== undefined ? d.min : d.lower,
                            max: d.max !== undefined ? d.max : d.upper,
                            q1: d.q1, q3: d.q3, median: d.median
                        }})).filter(d => !isNaN(d.min) && !isNaN(d.max));
                        if (boxData.length === 0) return;
                        
                        // Configuración
                        const margin = {{top: 50, right: 30, bottom: 70, left: 60}};
                        const width = originalWidth - margin.left - margin.right;
                        const height = originalHeight - margin.top - margin.bottom;
                        
                        // Crear grupo principal
                        const g = svg.append('g')
                            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
                        
                        // Escalas
                        const categories = boxData.map(d => d.category);
                        const xScale = d3.scaleBand()
                            .domain(categories)
                            .range([0, width])
                            .padding(0.3);
                        
                        const allValues = boxData.flatMap(d => [d.min, d.max]);
                        const yScale = d3.scaleLinear()
                            .domain([d3.min(allValues), d3.max(allValues)])
                            .nice()
                            .range([height, 0]);
                        
                        // Dibujar boxplots
                        boxData.forEach(d => {{
                            const x = xScale(d.category);
                            const boxWidth = xScale.bandwidth();
                            
                            // Línea vertical (min-max)
                            g.append('line')
                                .attr('x1', x + boxWidth/2)
                                .attr('x2', x + boxWidth/2)
                                .attr('y1', yScale(d.min))
                                .attr('y2', yScale(d.max))
                                .attr('stroke', '#333')
                                .attr('stroke-width', 1);
                            
                            // Caja (Q1-Q3)
                            g.append('rect')
                                .attr('x', x)
                                .attr('y', yScale(d.q3))
                                .attr('width', boxWidth)
                                .attr('height', yScale(d.q1) - yScale(d.q3))
                                .attr('fill', '#4a90e2')
                                .attr('stroke', '#333')
                                .attr('stroke-width', 1);
                            
                            // Mediana
                            g.append('line')
                                .attr('x1', x)
                                .attr('x2', x + boxWidth)
                                .attr('y1', yScale(d.median))
                                .attr('y2', yScale(d.median))
                                .attr('stroke', '#fff')
                                .attr('stroke-width', 2);
                            
                            // Whiskers
                            [d.min, d.max].forEach(val => {{
                                g.append('line')
                                    .attr('x1', x + boxWidth * 0.25)
                                    .attr('x2', x + boxWidth * 0.75)
                                    .attr('y1', yScale(val))
                                    .attr('y2', yScale(val))
                                    .attr('stroke', '#333')
                                    .attr('stroke-width', 1);
                            }});
                        }});
                        
                        // Ejes
                        g.append('g')
                            .attr('transform', `translate(0,${{height}})`)
                            .call(d3.axisBottom(xScale))
                            .selectAll('text')
                            .attr('transform', 'rotate(-45)')
                            .style('text-anchor', 'end');
                        
                        g.append('g')
                            .call(d3.axisLeft(yScale));
                        
                        // Título
                        if ('{title}') {{
                            svg.append('text')
                                .attr('x', originalWidth / 2)
                                .attr('y', 20)
                                .attr('text-anchor', 'middle')
                                .style('font-size', '14px')
                                .style('font-weight', 'bold')
                                .text('{title}');
                        }}
                        
                        // Etiquetas de ejes
                        if ('{x_label}') {{
                            svg.append('text')
                                .attr('x', originalWidth / 2)
                                .attr('y', originalHeight - 10)
                                .attr('text-anchor', 'middle')
                                .style('font-size', '12px')
                                .text('{x_label}');
                        }}
                        
                        if ('{y_label}') {{
                            svg.append('text')
                                .attr('transform', 'rotate(-90)')
                                .attr('x', -originalHeight / 2)
                                .attr('y', 15)
                                .attr('text-anchor', 'middle')
                                .style('font-size', '12px')
                                .text('{y_label}');
                        }}
                        }}, 100); // setTimeout
                    }})();
                    """
                    
                    # Ejecutar JavaScript
                    display(Javascript(js_update), display_id=f'boxplot-update-{letter}', update=True)
                
                if self._debug or MatrixLayout._debug:
                    print(f"   ✅ Boxplot '{letter}' actualizado en DOM")
                    
            except Exception as e:
                if self._debug or MatrixLayout._debug:
                    print(f"⚠️ Error actualizando boxplot: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Registrar callback en el SelectionModel de la vista principal
        primary_selection.on_change(update_boxplot)
        
        # Guardar referencia al callback para evitar duplicados
        self._boxplot_callbacks[letter] = update_boxplot
        
        # CRÍTICO: Si ya hay una selección activa en la vista principal, usar esos datos desde el inicio
        initial_data = self._data
        if primary_letter is not None:
            # Verificar si hay una selección activa
            current_items = primary_selection.get_items()
            if current_items and len(current_items) > 0:
                # Procesar items para obtener DataFrame filtrado
                processed_items = []
                for item in current_items:
                    if isinstance(item, dict):
                        if '_original_rows' in item and isinstance(item['_original_rows'], list):
                            processed_items.extend(item['_original_rows'])
                        elif '_original_row' in item:
                            processed_items.append(item['_original_row'])
                        else:
                            processed_items.append(item)
                    else:
                        processed_items.append(item)
                
                if processed_items:
                    if HAS_PANDAS:
                        import pandas as pd
                        try:
                            if isinstance(processed_items[0], dict):
                                initial_data = pd.DataFrame(processed_items)
                            else:
                                initial_data = pd.DataFrame(processed_items)
                        except Exception:
                            initial_data = self._data
                    else:
                        initial_data = processed_items
                
                if self._debug or MatrixLayout._debug:
                    print(f"📊 Boxplot '{letter}' inicializado con {len(processed_items) if processed_items else len(self._data)} items (hay selección activa)")
        
        # Debug: verificar que el callback se registró
        if self._debug or MatrixLayout._debug:
            print(f"🔗 [ReactiveMatrixLayout] Callback registrado para boxplot '{letter}' enlazado a vista principal '{primary_letter}'")
            print(f"   - SelectionModel ID: {id(primary_selection)}")
            print(f"   - Callbacks registrados: {len(primary_selection._callbacks)}")
            print(f"   - Boxplot callbacks guardados: {list(self._boxplot_callbacks.keys())}")
        
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
            from .matrix import MatrixLayout
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
    def add_heatmap(self, letter, x_col=None, y_col=None, value_col=None, linked_to=None, interactive=None, selection_var=None, **kwargs):
        """
        Agrega un heatmap que puede ser vista principal (con selección) o enlazada.

        - Como vista principal (interactive=True, sin linked_to):
          el usuario puede hacer click en una celda y recibir un DataFrame con las filas asociadas.
        - Como vista enlazada (linked_to=...):
          el heatmap se actualiza a partir de la selección de otra vista (scatter, bar, etc.).
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")

        # Determinar si será vista principal o enlazada
        if linked_to is None:
            # Solo es vista principal si interactive=True se especifica explícitamente
            if interactive is None:
                interactive = False
                is_primary = False
            else:
                is_primary = bool(interactive)
        else:
            is_primary = False
            if interactive is None:
                interactive = False

        # Vista principal con selección
        if is_primary:
            # Crear SelectionModel específico y registrar como vista principal
            heatmap_selection = SelectionModel()
            self._primary_view_models[letter] = heatmap_selection
            self._primary_view_types[letter] = 'heatmap'

            # Configurar variable de selección si se especifica
            if selection_var:
                self._selection_variables[letter] = selection_var
                self._selection_store[selection_var] = self._empty_selection()
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de heatmap '{letter}' como {df_type}")

            # Handler para eventos de selección provenientes del heatmap
            def heatmap_handler(payload):
                """Actualiza el SelectionModel de este heatmap a partir de eventos de JS."""
                items = payload.get('items', [])
                if not isinstance(items, list):
                    if self._debug or MatrixLayout._debug:
                        print(f"⚠️ [ReactiveMatrixLayout] items no es lista en heatmap '{letter}': {type(items)}")
                    items = []

                # Filtrado por letra o tipo de gráfico
                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                if event_letter is not None and event_letter != letter:
                    # Evento para otra vista
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento de heatmap ignorado: esperado '{letter}', recibido '{event_letter}'")
                    return

                graph_type = payload.get('__graph_type__', '')
                if event_letter is None and graph_type not in ('heatmap', ''):
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: tipo de gráfico '{graph_type}' no es 'heatmap'")
                    return

                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Evento recibido para heatmap '{letter}': {len(items)} items")

                # Convertir a DataFrame cuando sea posible
                items_df = _items_to_dataframe(items)
                data_to_update = items_df if (items_df is not None and not getattr(items_df, 'empty', False)) else items

                # Actualizar modelo específico y modelo global
                heatmap_selection.update(data_to_update)
                self.selection_model.update(data_to_update)
                self._selected_data = items_df if items_df is not None else items

                # Actualizar variable de selección del usuario
                if selection_var:
                    self.set_selection(selection_var, items_df if items_df is not None else items)

            # Registrar handler y marcar spec como vista principal interactiva
            self._layout.on('select', heatmap_handler)
            kwargs['__view_letter__'] = letter
            kwargs['__is_primary_view__'] = True
            kwargs['interactive'] = True

            # Render inicial con todos los datos
            self._register_chart(letter, 'heatmap', self._data, x_col=x_col, y_col=y_col, value_col=value_col, **kwargs)

            # Asegurar que el spec almacenado tenga los metadatos correctos
            if letter in self._layout._map:
                self._layout.update_spec_metadata(
                    letter,
                    __view_letter__=letter,
                    __is_primary_view__=True,
                    interactive=True
                )

            return self

        # Vista enlazada (como hasta ahora): se actualiza según selección de otra vista
        # Render inicial
        self._register_chart(letter, 'heatmap', self._data, x_col=x_col, y_col=y_col, value_col=value_col, **kwargs)

        # Enlazar solo si hay al menos una vista principal existente
        if not self._scatter_selection_models and not self._primary_view_models:
            return self

        # Determinar vista principal a la que se enlaza
        if linked_to is not None:
            if linked_to in self._scatter_selection_models:
                sel = self._scatter_selection_models[linked_to]
            elif linked_to in self._primary_view_models:
                sel = self._primary_view_models[linked_to]
            else:
                raise ValueError(f"Vista principal '{linked_to}' no existe. Agrega la vista principal primero.")
        else:
            # Si no se especifica, usar la última vista principal disponible
            all_primary = {**self._scatter_selection_models, **self._primary_view_models}
            primary_letter = list(all_primary.keys())[-1]
            sel = all_primary[primary_letter]

        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'heatmap', data_to_use, x_col=x_col, y_col=y_col, value_col=value_col, **kwargs)
            except Exception:
                if self._debug or MatrixLayout._debug:
                    import traceback
                    print(f"⚠️ [ReactiveMatrixLayout] Error actualizando heatmap enlazado '{letter}'")
                    traceback.print_exc()

        sel.on_change(update)
        return self

    def add_correlation_heatmap(self, letter, linked_to=None, **kwargs):
        from .matrix import MatrixLayout
        if not (HAS_PANDAS and isinstance(self._data, pd.DataFrame)):
            raise ValueError("add_correlation_heatmap requiere DataFrame")
        # Usar método de clase pero registrar directamente en la instancia correcta
        spec = MatrixLayout.map_correlation_heatmap.__func__(MatrixLayout, letter, self._data, **kwargs)
        if spec:
            self._layout._map[letter] = spec
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
                spec = MatrixLayout.map_correlation_heatmap.__func__(MatrixLayout, letter, df, **kwargs)
                if spec:
                    self._layout._map[letter] = spec
            except Exception:
                pass
        sel.on_change(update)
        return self

    def add_line(self, letter, x_col=None, y_col=None, series_col=None, linked_to=None, **kwargs):
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        self._register_chart(letter, 'line', self._data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
        if not self._scatter_selection_models:
            return self
        scatter_letter = linked_to or list(self._scatter_selection_models.keys())[-1]
        sel = self._scatter_selection_models[scatter_letter]
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'line', data_to_use, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
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
        from .matrix import MatrixLayout
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
                self._selection_store[selection_var] = self._empty_selection()
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de pie chart '{letter}' como {df_type}")
            
            # Crear handler para eventos de selección del pie chart
            def pie_handler(payload):
                """Handler que actualiza el SelectionModel de este pie chart"""
                # CRÍTICO: Verificar que el evento sea para este pie chart
                event_letter = payload.get('__view_letter__')
                
                # Si el evento tiene __view_letter__, debe coincidir con la letra de este pie chart
                # Si no tiene __view_letter__, procesar solo si no hay otros handlers más específicos
                # (esto permite compatibilidad con eventos antiguos)
                if event_letter is not None and event_letter != letter:
                    # El evento es para otra vista, ignorar
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento de pie chart ignorado: esperado '{letter}', recibido '{event_letter}'")
                    return
                
                # Si event_letter es None, podría ser un evento antiguo sin __view_letter__
                # En ese caso, procesar solo si no hay otros handlers más específicos
                # Por ahora, procesar si event_letter es None o coincide con letter
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
                    # Usar el método set_selection para mantener consistencia
                    self.set_selection(selection_var, items_df if items_df is not None else items)
            
            # CRÍTICO: Registrar handler ANTES de crear el gráfico para asegurar que esté disponible cuando llegue el evento
            self._layout.on('select', pie_handler)
            
            if self._debug or MatrixLayout._debug:
                print(f"📝 [ReactiveMatrixLayout] Handler registrado para pie chart '{letter}' con selection_var='{selection_var}'")
            
            kwargs['__view_letter__'] = letter
            kwargs['__is_primary_view__'] = True
            kwargs['interactive'] = True
        
        # Crear pie chart inicial con todos los datos - usar registro directo
        self._register_chart(letter, 'pie', self._data, category_col=category_col, value_col=value_col, **kwargs)
        
        # Asegurar que __linked_to__ esté en el spec guardado (por si map_pie no lo copió)
        if not is_primary and linked_to:
            if letter in self._layout._map:
                self._layout.update_spec_metadata(letter, __linked_to__=linked_to)
        
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
                from .matrix import MatrixLayout
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

    def add_violin(self, letter, value_col=None, category_col=None, bins=50, linked_to=None, interactive=None, selection_var=None, **kwargs):
        """
        Agrega un violin plot que muestra la distribución de densidad de los datos.
        
        Args:
            letter: Letra del layout ASCII
            value_col: Columna con valores numéricos
            category_col: Columna de categorías (opcional)
            bins: Número de puntos para el perfil de densidad (default: 50)
            linked_to: Letra de la vista principal que debe actualizar este violin (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        
        # Determinar si será vista principal o enlazada
        if linked_to is None:
            if interactive is None:
                interactive = False
                is_primary = False
            else:
                is_primary = bool(interactive)
        else:
            is_primary = False
            if interactive is None:
                interactive = False

        # Vista principal con selección (click en violines)
        if is_primary:
            violin_selection = SelectionModel()
            self._primary_view_models[letter] = violin_selection
            self._primary_view_types[letter] = 'violin'

            if selection_var:
                self._selection_variables[letter] = selection_var
                self._selection_store[selection_var] = self._empty_selection()
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de violin '{letter}' como {df_type}")

            def violin_handler(payload):
                """Handler que actualiza el SelectionModel de este violin plot."""
                items = payload.get('items', [])
                if not isinstance(items, list):
                    if self._debug or MatrixLayout._debug:
                        print(f"⚠️ [ReactiveMatrixLayout] items no es lista en violin '{letter}': {type(items)}")
                    items = []

                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                if event_letter is not None and event_letter != letter:
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: esperado '{letter}', recibido '{event_letter}'")
                    return

                graph_type = payload.get('__graph_type__', '')
                if event_letter is None and graph_type not in ('violin', ''):
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: tipo de gráfico '{graph_type}' no es 'violin'")
                    return

                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Evento recibido para violin '{letter}': {len(items)} items")

                items_df = _items_to_dataframe(items)
                data_to_update = items_df if (items_df is not None and not getattr(items_df, 'empty', False)) else items

                violin_selection.update(data_to_update)
                self.selection_model.update(data_to_update)
                self._selected_data = items_df if items_df is not None else items

                if selection_var:
                    self.set_selection(selection_var, items_df if items_df is not None else items)

            self._layout.on('select', violin_handler)

            # Crear violin plot inicial marcándolo como vista principal interactiva
            self._register_chart(
                letter,
                'violin',
                self._data,
                value_col=value_col,
                category_col=category_col,
                bins=bins,
                __view_letter__=letter,
                __is_primary_view__=True,
                interactive=True,
                **kwargs
            )
            return self

        # Vista enlazada (como antes): se actualiza desde otra vista
        self._register_chart(
            letter,
            'violin',
            self._data,
            value_col=value_col,
            category_col=category_col,
            bins=bins,
            **kwargs
        )
        
        # Solo registrar callback si linked_to está especificado explícitamente
        if linked_to is None:
            return self
        
        # Buscar vista principal especificada
        if linked_to in self._scatter_selection_models:
            primary_selection = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            primary_selection = self._primary_view_models[linked_to]
        else:
            raise ValueError(f"Vista principal '{linked_to}' no existe. Agrega la vista principal primero.")
        
        # Guardar parámetros para el callback
        violin_params = {
            'value_col': value_col,
            'category_col': category_col,
            'bins': bins,
            'kwargs': kwargs.copy()
        }
        
        def update_violin(items, count):
            """Actualiza el violin plot cuando cambia la selección"""
            if self._debug or MatrixLayout._debug:
                print(f"   🔄 Violin '{letter}' callback ejecutándose con {count} items")
            
            try:
                # Determinar datos a usar
                data_to_use = self._data
                if items and len(items) > 0:
                    # Extraer datos originales desde items
                    processed_items = []
                    for item in items:
                        if isinstance(item, dict):
                            if '_original_row' in item:
                                processed_items.append(item['_original_row'])
                            elif '_original_rows' in item:
                                processed_items.extend(item['_original_rows'])
                            else:
                                processed_items.append(item)
                        else:
                            processed_items.append(item)
                    
                    if processed_items and HAS_PANDAS and pd is not None:
                        try:
                            data_to_use = pd.DataFrame(processed_items)
                            # Verificar que la columna necesaria existe
                            if value_col not in data_to_use.columns:
                                if self._debug or MatrixLayout._debug:
                                    print(f"⚠️ Columna '{value_col}' no encontrada, usando todos los datos")
                                data_to_use = self._data
                        except Exception as e:
                            if self._debug or MatrixLayout._debug:
                                print(f"⚠️ Error creando DataFrame: {e}")
                            data_to_use = self._data
                
                # Regenerar spec con datos filtrados
                kwargs_update = violin_params['kwargs'].copy()
                if linked_to is not None:
                    kwargs_update['__linked_to__'] = linked_to
                
                # Usar el método de instancia para registrar el spec actualizado
                self._register_chart(
                    letter,
                    'violin',
                    data_to_use,
                    value_col=value_col,
                    category_col=category_col,
                    bins=bins,
                    **kwargs_update
                )
                
                if self._debug or MatrixLayout._debug:
                    print(f"   ✅ Violin '{letter}' spec actualizado")
                    
            except Exception as e:
                if self._debug or MatrixLayout._debug:
                    print(f"⚠️ Error actualizando violin: {e}")
                    import traceback
                    traceback.print_exc()
        
        primary_selection.on_change(update_violin)
        return self

    def add_radviz(self, letter, features=None, class_col=None, linked_to=None, **kwargs):
        from .matrix import MatrixLayout
        if not (HAS_PANDAS and isinstance(self._data, pd.DataFrame)):
            raise ValueError("add_radviz requiere DataFrame")
        self._register_chart(letter, 'radviz', self._data, features=features, class_col=class_col, **kwargs)
        
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
                self._register_chart(letter, 'radviz', df, features=features, class_col=class_col, **kwargs)
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
        from .matrix import MatrixLayout
        if not (HAS_PANDAS and isinstance(self._data, pd.DataFrame)):
            raise ValueError("add_star_coordinates requiere DataFrame")
        self._register_chart(letter, 'star_coordinates', self._data, features=features, class_col=class_col, **kwargs)
        
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
                self._register_chart(letter, 'star_coordinates', df, features=features, class_col=class_col, **kwargs)
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
        from .matrix import MatrixLayout
        if not (HAS_PANDAS and isinstance(self._data, pd.DataFrame)):
            raise ValueError("add_parallel_coordinates requiere DataFrame")
        self._register_chart(letter, 'parallel_coordinates', self._data, dimensions=dimensions, category_col=category_col, **kwargs)
        
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
                self._register_chart(letter, 'parallel_coordinates', df, dimensions=dimensions, category_col=category_col, **kwargs)
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
        from .matrix import MatrixLayout
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
            melted_data = cm_df.reset_index().melt(id_vars='index', var_name='Pred', value_name='Value')
            self._register_chart(
                letter, 'heatmap', melted_data,
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

    def add_line_plot(self, letter, x_col=None, y_col=None, series_col=None, linked_to=None, **kwargs):
        """
        Agrega line plot completo (versión mejorada del line chart).
        
        Args:
            letter: Letra del layout ASCII
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            series_col: Nombre de columna para series (opcional)
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        self._register_chart(letter, 'line_plot', self._data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'line_plot', data_to_use, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self
    
    def add_horizontal_bar(self, letter, category_col=None, value_col=None, linked_to=None, **kwargs):
        """
        Agrega horizontal bar chart.
        
        Args:
            letter: Letra del layout ASCII
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional)
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")

        # Determinar si será vista principal o enlazada
        interactive = kwargs.pop('interactive', None) if 'interactive' in kwargs else interactive
        selection_var = kwargs.pop('selection_var', None) if 'selection_var' in kwargs else None

        if linked_to is None:
            if interactive is None:
                interactive = False
                is_primary = False
            else:
                is_primary = bool(interactive)
        else:
            is_primary = False
            if interactive is None:
                interactive = False

        # Vista principal con selección (similar a barchart)
        if is_primary:
            hb_selection = SelectionModel()
            self._primary_view_models[letter] = hb_selection
            self._primary_view_types[letter] = 'horizontal_bar'

            if selection_var:
                self._selection_variables[letter] = selection_var
                self._selection_store[selection_var] = self._empty_selection()
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de horizontal_bar '{letter}' como {df_type}")

            def hb_handler(payload):
                """Handler que actualiza el SelectionModel de este horizontal bar chart"""
                items = payload.get('items', [])
                if not isinstance(items, list):
                    if self._debug or MatrixLayout._debug:
                        print(f"⚠️ [ReactiveMatrixLayout] items no es lista en horizontal_bar '{letter}': {type(items)}")
                    items = []

                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                if event_letter is not None and event_letter != letter:
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: esperado '{letter}', recibido '{event_letter}'")
                    return

                graph_type = payload.get('__graph_type__', '')
                if event_letter is None and graph_type not in ('horizontal_bar', ''):
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: tipo de gráfico '{graph_type}' no es 'horizontal_bar'")
                    return

                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Evento recibido para horizontal_bar '{letter}': {len(items)} items")

                items_df = _items_to_dataframe(items)
                data_to_update = items_df if (items_df is not None and not getattr(items_df, 'empty', False)) else items

                hb_selection.update(data_to_update)
                self.selection_model.update(data_to_update)
                self._selected_data = items_df if items_df is not None else items

                if selection_var:
                    self.set_selection(selection_var, items_df if items_df is not None else items)

            self._layout.on('select', hb_handler)

            # Crear gráfico inicial como vista principal interactiva
            self._register_chart(
                letter,
                'horizontal_bar',
                self._data,
                category_col=category_col,
                value_col=value_col,
                __view_letter__=letter,
                __is_primary_view__=True,
                interactive=True,
                **kwargs
            )
            return self

        # Vista enlazada (como antes)
        self._register_chart(letter, 'horizontal_bar', self._data, category_col=category_col, value_col=value_col, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self

        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'horizontal_bar', data_to_use, category_col=category_col, value_col=value_col, **kwargs)
            except Exception:
                if self._debug or MatrixLayout._debug:
                    import traceback
                    print(f"⚠️ [ReactiveMatrixLayout] Error actualizando horizontal_bar enlazado '{letter}'")
                    traceback.print_exc()

        sel.on_change(update)
        return self
    
    def add_hexbin(self, letter, x_col=None, y_col=None, linked_to=None, **kwargs):
        """
        Agrega hexbin chart (visualización de densidad).
        
        Args:
            letter: Letra del layout ASCII
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales (bins, colorScale, etc.)
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")

        interactive = kwargs.pop('interactive', None) if 'interactive' in kwargs else interactive
        selection_var = kwargs.pop('selection_var', None) if 'selection_var' in kwargs else None

        if linked_to is None:
            if interactive is None:
                interactive = False
                is_primary = False
            else:
                is_primary = bool(interactive)
        else:
            is_primary = False
            if interactive is None:
                interactive = False

        # Vista principal con selección por hexágono
        if is_primary:
            hex_selection = SelectionModel()
            self._primary_view_models[letter] = hex_selection
            self._primary_view_types[letter] = 'hexbin'

            if selection_var:
                self._selection_variables[letter] = selection_var
                self._selection_store[selection_var] = self._empty_selection()
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de hexbin '{letter}' como {df_type}")

            def hex_handler(payload):
                """Handler que actualiza el SelectionModel de este hexbin chart"""
                items = payload.get('items', [])
                if not isinstance(items, list):
                    if self._debug or MatrixLayout._debug:
                        print(f"⚠️ [ReactiveMatrixLayout] items no es lista en hexbin '{letter}': {type(items)}")
                    items = []

                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                if event_letter is not None and event_letter != letter:
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: esperado '{letter}', recibido '{event_letter}'")
                    return

                graph_type = payload.get('__graph_type__', '')
                if event_letter is None and graph_type not in ('hexbin', ''):
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: tipo de gráfico '{graph_type}' no es 'hexbin'")
                    return

                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Evento recibido para hexbin '{letter}': {len(items)} items")

                items_df = _items_to_dataframe(items)
                data_to_update = items_df if (items_df is not None and not getattr(items_df, 'empty', False)) else items

                hex_selection.update(data_to_update)
                self.selection_model.update(data_to_update)
                self._selected_data = items_df if items_df is not None else items

                if selection_var:
                    self.set_selection(selection_var, items_df if items_df is not None else items)

            self._layout.on('select', hex_handler)

            self._register_chart(
                letter,
                'hexbin',
                self._data,
                x_col=x_col,
                y_col=y_col,
                __view_letter__=letter,
                __is_primary_view__=True,
                interactive=True,
                **kwargs
            )
            return self

        # Vista enlazada (como antes)
        self._register_chart(letter, 'hexbin', self._data, x_col=x_col, y_col=y_col, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'hexbin', data_to_use, x_col=x_col, y_col=y_col, **kwargs)
            except Exception:
                if self._debug or MatrixLayout._debug:
                    import traceback
                    print(f"⚠️ [ReactiveMatrixLayout] Error actualizando hexbin enlazado '{letter}'")
                    traceback.print_exc()
        sel.on_change(update)
        return self
    
    def add_errorbars(self, letter, x_col=None, y_col=None, yerr=None, xerr=None, linked_to=None, **kwargs):
        """
        Agrega errorbars chart.
        
        Args:
            letter: Letra del layout ASCII
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            yerr: Nombre de columna para error en Y (opcional)
            xerr: Nombre de columna para error en X (opcional)
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")

        interactive = kwargs.pop('interactive', None) if 'interactive' in kwargs else interactive
        selection_var = kwargs.pop('selection_var', None) if 'selection_var' in kwargs else None

        if linked_to is None:
            if interactive is None:
                interactive = False
                is_primary = False
            else:
                is_primary = bool(interactive)
        else:
            is_primary = False
            if interactive is None:
                interactive = False

        # Vista principal con selección por punto de errorbars
        if is_primary:
            eb_selection = SelectionModel()
            self._primary_view_models[letter] = eb_selection
            self._primary_view_types[letter] = 'errorbars'

            if selection_var:
                self._selection_variables[letter] = selection_var
                self._selection_store[selection_var] = self._empty_selection()
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if HAS_PANDAS else "lista"
                    print(f"📦 Variable '{selection_var}' creada para guardar selecciones de errorbars '{letter}' como {df_type}")

            def eb_handler(payload):
                """Handler que actualiza el SelectionModel de este errorbars chart"""
                items = payload.get('items', [])
                if not isinstance(items, list):
                    if self._debug or MatrixLayout._debug:
                        print(f"⚠️ [ReactiveMatrixLayout] items no es lista en errorbars '{letter}': {type(items)}")
                    items = []

                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                if event_letter is not None and event_letter != letter:
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: esperado '{letter}', recibido '{event_letter}'")
                    return

                graph_type = payload.get('__graph_type__', '')
                if event_letter is None and graph_type not in ('errorbars', ''):
                    if self._debug or MatrixLayout._debug:
                        print(f"⏭️ [ReactiveMatrixLayout] Evento ignorado: tipo de gráfico '{graph_type}' no es 'errorbars'")
                    return

                if self._debug or MatrixLayout._debug:
                    print(f"✅ [ReactiveMatrixLayout] Evento recibido para errorbars '{letter}': {len(items)} items")

                items_df = _items_to_dataframe(items)
                data_to_update = items_df if (items_df is not None and not getattr(items_df, 'empty', False)) else items

                eb_selection.update(data_to_update)
                self.selection_model.update(data_to_update)
                self._selected_data = items_df if items_df is not None else items

                if selection_var:
                    self.set_selection(selection_var, items_df if items_df is not None else items)

            self._layout.on('select', eb_handler)

            self._register_chart(
                letter,
                'errorbars',
                self._data,
                x_col=x_col,
                y_col=y_col,
                yerr=yerr,
                xerr=xerr,
                __view_letter__=letter,
                __is_primary_view__=True,
                interactive=True,
                **kwargs
            )
            return self

        # Vista enlazada (como antes)
        self._register_chart(letter, 'errorbars', self._data, x_col=x_col, y_col=y_col, yerr=yerr, xerr=xerr, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self

        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'errorbars', data_to_use, x_col=x_col, y_col=y_col, yerr=yerr, xerr=xerr, **kwargs)
            except Exception:
                if self._debug or MatrixLayout._debug:
                    import traceback
                    print(f"⚠️ [ReactiveMatrixLayout] Error actualizando errorbars enlazado '{letter}'")
                    traceback.print_exc()

        sel.on_change(update)
        return self
    
    def add_fill_between(self, letter, x_col=None, y1=None, y2=None, linked_to=None, **kwargs):
        """
        Agrega fill_between chart (área entre dos líneas).
        
        Args:
            letter: Letra del layout ASCII
            x_col: Nombre de columna para eje X
            y1: Nombre de columna para primera línea Y
            y2: Nombre de columna para segunda línea Y
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        self._register_chart(letter, 'fill_between', self._data, x_col=x_col, y1=y1, y2=y2, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'fill_between', data_to_use, x_col=x_col, y1=y1, y2=y2, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self
    
    def add_step(self, letter, x_col=None, y_col=None, linked_to=None, **kwargs):
        """
        Agrega step plot (líneas escalonadas).
        
        Args:
            letter: Letra del layout ASCII
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales (stepType, etc.)
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        self._register_chart(letter, 'step_plot', self._data, x_col=x_col, y_col=y_col, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'step_plot', data_to_use, x_col=x_col, y_col=y_col, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self

    def add_kde(self, letter, column=None, bandwidth=None, linked_to=None, **kwargs):
        """
        Agrega KDE (Kernel Density Estimation) chart.
        
        Args:
            letter: Letra del layout ASCII
            column: Nombre de columna para el KDE
            bandwidth: Ancho de banda del kernel (opcional)
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None:
            raise ValueError("Debe especificar 'column' para KDE")
        self._register_chart(letter, 'kde', self._data, column=column, bandwidth=bandwidth, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'kde', data_to_use, column=column, bandwidth=bandwidth, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self
    
    def add_distplot(self, letter, column=None, bins=30, kde=True, rug=False, linked_to=None, **kwargs):
        """
        Agrega distribution plot (histograma + KDE).
        
        Args:
            letter: Letra del layout ASCII
            column: Nombre de columna para el distplot
            bins: Número de bins para el histograma
            kde: Si incluir KDE superpuesto
            rug: Si incluir rug plot
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None:
            raise ValueError("Debe especificar 'column' para distplot")
        self._register_chart(letter, 'distplot', self._data, column=column, bins=bins, kde=kde, rug=rug, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'distplot', data_to_use, column=column, bins=bins, kde=kde, rug=rug, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self
    
    def add_rug(self, letter, column=None, axis='x', linked_to=None, **kwargs):
        """
        Agrega rug plot.
        
        Args:
            letter: Letra del layout ASCII
            column: Nombre de columna para el rug plot
            axis: Eje donde dibujar ('x' o 'y')
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None:
            raise ValueError("Debe especificar 'column' para rug plot")
        self._register_chart(letter, 'rug', self._data, column=column, axis=axis, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'rug', data_to_use, column=column, axis=axis, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self
    
    def add_qqplot(self, letter, column=None, dist='norm', linked_to=None, **kwargs):
        """
        Agrega Q-Q plot.
        
        Args:
            letter: Letra del layout ASCII
            column: Nombre de columna para el Q-Q plot
            dist: Distribución teórica ('norm', 'expon', etc.)
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None:
            raise ValueError("Debe especificar 'column' para Q-Q plot")
        self._register_chart(letter, 'qqplot', self._data, column=column, dist=dist, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'qqplot', data_to_use, column=column, dist=dist, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self
    
    def add_ecdf(self, letter, column=None, linked_to=None, **kwargs):
        """
        Agrega ECDF (Empirical Cumulative Distribution Function) chart.
        
        Args:
            letter: Letra del layout ASCII
            column: Nombre de columna para el ECDF
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        if column is None:
            raise ValueError("Debe especificar 'column' para ECDF")
        self._register_chart(letter, 'ecdf', self._data, column=column, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            data_to_use = self._data if not items else (pd.DataFrame(items) if HAS_PANDAS and isinstance(items[0], dict) else items)
            try:
                self._register_chart(letter, 'ecdf', data_to_use, column=column, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self

    def add_ridgeline(self, letter, column=None, category_col=None, bandwidth=None, linked_to=None, **kwargs):
        """
        Agrega ridgeline plot (joy plot).
        
        Args:
            letter: Letra del layout ASCII
            column: Nombre de columna numérica para las distribuciones
            category_col: Nombre de columna categórica para separar las crestas
            bandwidth: Ancho de banda para KDE (opcional)
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
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
        """
        Agrega ribbon plot (área entre líneas con gradiente).
        
        Args:
            letter: Letra del layout ASCII
            x_col: Nombre de columna para eje X
            y1_col: Nombre de columna para límite inferior
            y2_col: Nombre de columna para límite superior
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
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
        """
        Agrega 2D histogram.
        
        Args:
            letter: Letra del layout ASCII
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            bins: Número de bins (por defecto 20)
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
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
        """
        Agrega polar plot.
        
        Args:
            letter: Letra del layout ASCII
            angle_col: Nombre de columna para el ángulo
            radius_col: Nombre de columna para el radio
            angle_unit: Unidad del ángulo ('rad' o 'deg', por defecto 'rad')
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
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
        """
        Agrega funnel plot.
        
        Args:
            letter: Letra del layout ASCII
            stage_col: Nombre de columna para las etapas del embudo
            value_col: Nombre de columna para los valores
            linked_to: Letra de la vista principal que debe actualizar este gráfico (opcional)
            **kwargs: Argumentos adicionales
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
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

    
    def _repr_html_(self):
        """Representación HTML para Jupyter (delega al layout interno)"""
        return self._layout._repr_html_()
    
    def _repr_mimebundle_(self, include=None, exclude=None):
        """Representación MIME bundle para JupyterLab (delega al layout interno)"""
        return self._layout._repr_mimebundle_(include=include, exclude=exclude)
    
    def display(self, ascii_layout=None):
        """
        Muestra el layout.
        
        IMPORTANTE: Solo llama este método UNA VEZ después de configurar todos los gráficos.
        Llamar display() múltiples veces causará duplicación de gráficos.
        
        El bar chart se actualiza automáticamente cuando seleccionas en el scatter plot,
        NO necesitas llamar display() nuevamente después de cada selección.
        """
        # Cargar assets automáticamente en Colab
        from ..render.assets import AssetManager
        AssetManager.ensure_colab_assets_loaded()
        
        if ascii_layout:
            self._layout.ascii_layout = ascii_layout
        
        # Solo mostrar una vez - el bar chart se actualiza automáticamente vía JavaScript
        self._layout.display()
        
        # Retornar None explícitamente para evitar que Jupyter muestre el objeto
        return None

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
    
    def get_selection(self, selection_var=None):
        """
        Obtiene la selección guardada en una variable Python.
        
        Args:
            selection_var (str, optional): Nombre de la variable de selección.
                                          Si no se especifica, retorna la selección del modelo principal.
        
        Returns:
            DataFrame o lista: Datos seleccionados guardados en la variable especificada,
                              o la selección del modelo principal si no se especifica variable.
        
        Ejemplo:
            layout = ReactiveMatrixLayout("P", selection_model=SelectionModel())
            layout.set_data(df)
            layout.add_pie('P', category_col='species', interactive=True, selection_var='selected_pie_category')
            layout.display()
            
            # Más tarde, obtener la selección:
            selected = layout.get_selection('selected_pie_category')
            # O simplemente:
            selected = layout.get_selection()  # Retorna selection_model.get_items()
        """
        if selection_var:
            if selection_var in self._selection_store:
                return self._selection_store[selection_var]
            for view_letter, var_name in self._selection_variables.items():
                if var_name == selection_var and view_letter in self._primary_view_models:
                    return self._primary_view_models[view_letter].get_items()
            return self._empty_selection()
        return self.selection_model.get_items()
    
    def set_selection(self, selection_var_name, items):
        """
        Guarda la selección en una variable Python por su nombre.
        
        Args:
            selection_var_name (str): Nombre de la variable donde guardar la selección.
            items (list or pd.DataFrame): Los items a guardar.
        """
        self._selection_store[selection_var_name] = items
        if self._debug or MatrixLayout._debug:
            if HAS_PANDAS and isinstance(items, pd.DataFrame):
                count_msg = f"{len(items)} filas"
            elif hasattr(items, '__len__'):
                count_msg = f"{len(items)} items"
            else:
                count_msg = "0 items"
            print(f"💾 Selección guardada para '{selection_var_name}': {count_msg}")


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


