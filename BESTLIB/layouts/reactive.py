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

# Import de pandas de forma segura usando utils.imports
from ..utils.imports import has_pandas, get_pandas
from ..core.validation import safe_dataframe, safe_get_first_item
from ..core.exceptions import get_logger

# Inicializar logger centralizado
logger = get_logger()

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
        self._selected_data = get_pandas().DataFrame() if has_pandas() else []  # Datos seleccionados actualmente (DataFrame)
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
            # Crear variable en el namespace del usuario (inicializar como DataFrame vacío)
            import __main__
            if has_pandas():
                pd_module = globals().get('pd')
                if pd_module is None:
                    import sys
                    if 'pandas' in sys.modules:
                        pd_module = sys.modules['pandas']
                    else:
                        import pandas as pd_module
                        globals()['pd'] = pd_module
                empty_df = pd_module.DataFrame() if pd_module is not None else []
            else:
                empty_df = []
            setattr(__main__, selection_var, empty_df)
            if self._debug or MatrixLayout._debug:
                df_type = "DataFrame" if has_pandas() else "lista"
                logger = get_logger()
                logger.info(f"Variable '{selection_var}' creada para guardar selecciones de scatter '{letter}' como {df_type}")
        
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
                    logger = get_logger()
                    logger.warning(f"[ReactiveMatrixLayout] items no es lista: {type(items)}")
                items = []
            
            # ✅ CORRECCIÓN: Filtrado más flexible
            # Aceptar tanto __scatter_letter__ como __view_letter__ para compatibilidad
            event_scatter_letter = payload.get('__scatter_letter__') or payload.get('__view_letter__')
            if event_scatter_letter is not None and event_scatter_letter != scatter_letter_capture:
                # Este evento no es para este scatter plot, ignorar
                if self._debug or MatrixLayout._debug:
                    logger = get_logger()
                    logger.debug(f"[ReactiveMatrixLayout] Evento ignorado: esperado '{scatter_letter_capture}', recibido '{event_scatter_letter}'")
                return
            
            if self._debug or MatrixLayout._debug:
                logger = get_logger()
                logger.info(f"[ReactiveMatrixLayout] Evento recibido para scatter '{scatter_letter_capture}': {len(items)} items")
            
            # ✅ CORRECCIÓN: Validar conversión a DataFrame
            items_df = _items_to_dataframe(items)
            if items_df is None or (hasattr(items_df, 'empty') and items_df.empty and len(items) > 0):
                if self._debug or MatrixLayout._debug:
                    logger.warning(f"[ReactiveMatrixLayout] Error al convertir {len(items)} items a DataFrame")
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
        scatter_spec = MatrixLayout.map_scatter(
            letter, 
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
                logger = get_logger()
                logger.debug(f"[ReactiveMatrixLayout] interactive no estaba en spec, agregado manualmente: {interactive}")
        
        # Asegurar que los identificadores estén en el spec guardado
        if scatter_spec:
            scatter_spec['__scatter_letter__'] = letter
            scatter_spec['__selection_model_id__'] = id(scatter_selection)
            MatrixLayout._map[letter] = scatter_spec
            
            # Debug: verificar que el spec tiene los identificadores
            if self._debug or MatrixLayout._debug:
                logger = get_logger()
                logger.debug(f"[ReactiveMatrixLayout] Scatter plot '{letter}' configurado con __scatter_letter__={scatter_spec.get('__scatter_letter__')}")
        
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
                # Asegurar que pd esté disponible (usar el del módulo global)
                if has_pandas():
                    # Usar globals() para evitar UnboundLocalError
                    pd_module = globals().get('pd')
                    if pd_module is None:
                        import sys
                        if 'pandas' in sys.modules:
                            pd_module = sys.modules['pandas']
                        else:
                            import pandas as pd_module
                            globals()['pd'] = pd_module
                    empty_df = pd_module.DataFrame() if pd_module is not None else []
                else:
                    empty_df = []
                setattr(__main__, selection_var, empty_df)
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if has_pandas() else "lista"
                    logger = get_logger()
                    logger.info(f"Variable '{selection_var}' creada para guardar selecciones de bar chart '{letter}' como {df_type}")
            
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
                        logger = get_logger()
                    logger.warning(f"[ReactiveMatrixLayout] items no es lista: {type(items)}")
                    items = []
                
                # ✅ CORRECCIÓN: Filtrado más flexible
                event_letter = payload.get('__view_letter__') or payload.get('__scatter_letter__')
                if event_letter is not None and event_letter != letter:
                    return
                
                # CRÍTICO: Prevenir procesamiento si estamos actualizando el bar chart
                # Verificar flag de actualización del bar chart
                if self._barchart_update_flags.get(barchart_update_flag, False):
                    if self._debug or MatrixLayout._debug:
                        logger = get_logger()
                        logger.debug(f"[ReactiveMatrixLayout] Bar chart '{letter}' está siendo actualizado, ignorando evento")
                    return
                
                if self._debug or MatrixLayout._debug:
                    logger = get_logger()
                    logger.info(f"[ReactiveMatrixLayout] Evento recibido para bar chart '{letter}': {len(items)} items")
                
                # CRÍTICO: Prevenir actualizaciones recursivas
                # Marcar flag ANTES de actualizar el SelectionModel
                self._barchart_update_flags[barchart_update_flag] = True
                
                try:
                    # ✅ CORRECCIÓN: Validar conversión a DataFrame
                    items_df = _items_to_dataframe(items)
                    if items_df is None or (hasattr(items_df, 'empty') and items_df.empty and len(items) > 0):
                        if self._debug or MatrixLayout._debug:
                            logger.warning(f"[ReactiveMatrixLayout] Error al convertir {len(items)} items a DataFrame")
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
                            logger = get_logger()
                            logger.info(f"Selección guardada en variable '{selection_var}' como DataFrame: {count_msg}")
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
                logger = get_logger()
                logger.warning(f"Bar chart para '{letter}' ya está registrado. Ignorando registro duplicado.")
            return self
        
        # Inicializar primary_letter siempre
        primary_letter = None
        
        # Si es vista enlazada, determinar a qué vista principal enlazar
        if not is_primary:
            # CRÍTICO: Si linked_to es None, NO enlazar automáticamente (gráfico estático)
            if linked_to is None:
                # Crear bar chart estático sin enlazar
                MatrixLayout.map_barchart(letter, self._data, category_col=category_col, value_col=value_col, **kwargs)
                return self
            
            # Validar que linked_to no sea el string "None"
            if isinstance(linked_to, str) and linked_to.lower() == 'none':
                linked_to = None
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
                # Si linked_to está especificado pero no existe, lanzar error con información útil
                available_scatters = list(self._scatter_selection_models.keys())
                available_primary = list(self._primary_view_models.keys())
                all_available = available_scatters + available_primary
                
                if self._debug or MatrixLayout._debug:
                    logger = get_logger()
                    logger.error(f"[ReactiveMatrixLayout] Vista principal '{linked_to}' no existe para barchart '{letter}'")
                    logger.debug(f"   - Scatter plots disponibles: {available_scatters}")
                    logger.debug(f"   - Vistas principales disponibles: {available_primary}")
                    logger.debug(f"   - Todas las vistas: {all_available}")
                
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
                logger.debug(f"[ReactiveMatrixLayout] Registrando callback para bar chart '{letter}' enlazado a vista principal '{primary_letter}'")
                logger.debug(f"   - SelectionModel ID: {id(primary_selection)}")
                logger.debug(f"   - Callbacks actuales: {len(primary_selection._callbacks)}")
            
            # Configurar callback para actualizar bar chart cuando cambia selección
            def update_barchart(items, count):
                """Actualiza el bar chart cuando cambia la selección usando JavaScript"""
                try:
                    # Debug: verificar que el callback se está ejecutando
                    if self._debug or MatrixLayout._debug:
                        logger.debug(f"[ReactiveMatrixLayout] Callback ejecutado: Actualizando bar chart '{letter}' con {count} items seleccionados")
                    import json
                    from IPython.display import Javascript
                    import time
                    
                    # Usar datos seleccionados o todos los datos
                    data_to_use = self._data
                    if items and len(items) > 0:
                        # Convertir lista de dicts a DataFrame si es necesario
                        # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
                        if has_pandas() and isinstance(items, list) and len(items) > 0:
                            # ✅ CRIT-002, CRIT-003: Usar helpers centralizados
                            first_item = safe_get_first_item(items)
                            if first_item is not None and isinstance(first_item, dict):
                                df_result = safe_dataframe(items)
                                data_to_use = df_result if df_result is not None else items
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
                        logger.error(f"Error actualizando bar chart: {e}", exc_info=True)
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
                import __main__
                # Asegurar que pd esté disponible (usar el del módulo global)
                if has_pandas():
                    pd_module = globals().get('pd')
                    if pd_module is None:
                        import sys
                        if 'pandas' in sys.modules:
                            pd_module = sys.modules['pandas']
                        else:
                            import pandas as pd_module
                            globals()['pd'] = pd_module
                    empty_df = pd_module.DataFrame() if pd_module is not None else []
                else:
                    empty_df = []
                setattr(__main__, selection_var, empty_df)
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if has_pandas() else "lista"
                    logger.debug(f"Variable '{selection_var}' creada para guardar selecciones de grouped bar chart '{letter}' como {df_type}")
            
            def grouped_handler(payload):
                event_letter = payload.get('__view_letter__')
                if event_letter != letter:
                    return
                
                items = payload.get('items', [])
                
                if self._debug or MatrixLayout._debug:
                    logger.debug(f"[ReactiveMatrixLayout] Evento recibido para grouped bar chart '{letter}': {len(items)} items")
                
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
                        logger.debug(f"Selección guardada en variable '{selection_var}' como DataFrame: {count_msg}")
            
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
                    logger.debug(f"Grouped bar chart '{letter}' enlazado automáticamente a vista principal '{primary_letter}'")
            
            def update(items, count):
                # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
                if not items:
                    data_to_use = self._data
                elif has_pandas() and isinstance(items, list) and len(items) > 0:
                    # ✅ CRIT-002, CRIT-003: Usar helpers centralizados
                    first_item = safe_get_first_item(items)
                    if first_item is not None and isinstance(first_item, dict):
                        df_result = safe_dataframe(items)
                        if df_result is not None:
                            data_to_use = df_result
                        else:
                            data_to_use = items
                    else:
                        data_to_use = items
                else:
                    data_to_use = items
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
                logger.debug(f"Gráfico '{letter}' ({chart_type}) enlazado automáticamente a scatter '{scatter_letter}'")
        
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
                    logger.debug(f"Actualizando gráfico '{letter}' ({chart_type}) con {count} elementos seleccionados")
            
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
                import __main__
                # Asegurar que pd esté disponible (usar el del módulo global)
                if has_pandas():
                    pd_module = globals().get('pd')
                    if pd_module is None:
                        import sys
                        if 'pandas' in sys.modules:
                            pd_module = sys.modules['pandas']
                        else:
                            import pandas as pd_module
                            globals()['pd'] = pd_module
                    empty_df = pd_module.DataFrame() if pd_module is not None else []
                else:
                    empty_df = []
                setattr(__main__, selection_var, empty_df)
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if has_pandas() else "lista"
                    logger.debug(f"Variable '{selection_var}' creada para guardar selecciones de histogram '{letter}' como {df_type}")
            
            # Crear handler para eventos de selección del histogram
            def histogram_handler(payload):
                """Handler que actualiza el SelectionModel de este histogram"""
                event_letter = payload.get('__view_letter__')
                if event_letter != letter:
                    return
                
                items = payload.get('items', [])
                
                if self._debug or MatrixLayout._debug:
                    logger.debug(f"[ReactiveMatrixLayout] Evento recibido para histogram '{letter}': {len(items)} items")
                
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
                        logger.debug(f"Selección guardada en variable '{selection_var}' como DataFrame: {count_msg}")
            
            self._layout.on('select', histogram_handler)
            
            kwargs['__view_letter__'] = letter
            kwargs['__is_primary_view__'] = True
            kwargs['interactive'] = True
        
        # Inicializar primary_letter siempre
        primary_letter = None
        
        # Si es vista enlazada, determinar a qué vista principal enlazar
        if not is_primary:
            # CRÍTICO: Si linked_to es None, NO enlazar automáticamente (gráfico estático)
            if linked_to is None:
                # Crear histograma estático sin enlazar
                MatrixLayout.map_histogram(letter, initial_data, value_col=column, bins=bins, **kwargs)
                return self
            
            # Validar que linked_to no sea el string "None"
            if isinstance(linked_to, str) and linked_to.lower() == 'none':
                linked_to = None
                # Crear histograma estático sin enlazar
                MatrixLayout.map_histogram(letter, initial_data, value_col=column, bins=bins, **kwargs)
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
                    logger.error(f"[ReactiveMatrixLayout] Vista principal '{linked_to}' no existe para histogram '{letter}'")
                    logger.error(f"   - Scatter plots disponibles: {available_scatters}")
                    logger.error(f"   - Vistas principales disponibles: {available_primary}")
                    logger.error(f"   - Todas las vistas: {all_available}")
                
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
                        if has_pandas():
                            pd_module = globals().get('pd')
                            if pd_module is None:
                                import sys
                                if 'pandas' in sys.modules:
                                    pd_module = sys.modules['pandas']
                                else:
                                    import pandas as pd_module
                                    globals()['pd'] = pd_module
                            try:
                                # ✅ CORRECCIÓN: Validar que processed_items tenga elementos antes de acceder a [0]
                                if isinstance(processed_items, list) and len(processed_items) > 0:
                                    if isinstance(processed_items[0], dict):
                                        initial_data = pd_module.DataFrame(processed_items)
                                    else:
                                        initial_data = pd_module.DataFrame(processed_items)
                                else:
                                    initial_data = self._data
                            except Exception:
                                initial_data = self._data
                        else:
                            initial_data = processed_items
                    
                    if self._debug or MatrixLayout._debug:
                        logger.debug(f"Histogram '{letter}' inicializado con {len(processed_items) if processed_items else len(self._data)} items (hay selección activa)")
            
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
                        logger.debug(f"   Histogram '{letter}' callback ya está ejecutándose, ignorando llamada duplicada")
                    return
                update_histogram._executing = True
                
                try:
                    import json
                    from IPython.display import Javascript
                    
                    if self._debug or MatrixLayout._debug:
                        logger.debug(f"   Histogram '{letter}' callback ejecutándose con {count} items")
                    
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
                            if has_pandas():
                                import pandas as pd
                                # Intentar crear DataFrame desde los items procesados
                                try:
                                    # ✅ CORRECCIÓN: Validar que processed_items tenga elementos antes de acceder a [0]
                                    if isinstance(processed_items, list) and len(processed_items) > 0:
                                    # ✅ CRIT-002, CRIT-003: Usar helpers centralizados
                                    first_item = safe_get_first_item(processed_items)
                                    if first_item is not None and isinstance(first_item, dict):
                                        df_result = safe_dataframe(processed_items)
                                        if df_result is not None:
                                            data_to_use = df_result
                                        else:
                                            data_to_use = processed_items
                                    else:
                                        data_to_use = processed_items
                                    else:
                                        # Si no son diccionarios, intentar convertir
                                            # ✅ CRIT-002: Usar helper centralizado
                                            df_result = safe_dataframe(processed_items)
                                            data_to_use = df_result if df_result is not None else processed_items
                                    else:
                                        data_to_use = processed_items
                                except (ValueError, TypeError, KeyError, AttributeError) as e:
                                    logger = get_logger()
                                    logger.warning(f"Error esperado creando DataFrame desde items: {e}")
                                    data_to_use = self._data
                                except Exception as e:
                                    logger = get_logger()
                                    logger.error(f"Error inesperado creando DataFrame desde items: {e}", exc_info=True)
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
                    if has_pandas() and isinstance(data_to_use, get_pandas().DataFrame):
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
                    if has_pandas():
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
                        logger.error(f"Error actualizando histograma: {e}", exc_info=True)
                        import traceback
                        traceback.print_exc()
                finally:
                    # CRÍTICO: Resetear flag después de completar
                    update_histogram._executing = False
                    if self._debug or MatrixLayout._debug:
                        logger.debug(f"   Histogram '{letter}' callback completado")
            
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
                        if has_pandas():
                            import pandas as pd
                            try:
                                # ✅ CRIT-002, CRIT-003: Usar helpers centralizados
                                first_item = safe_get_first_item(processed_items)
                                if first_item is not None:
                                    df_result = safe_dataframe(processed_items)
                                    initial_data = df_result if df_result is not None else processed_items
                                else:
                                    initial_data = processed_items
                            except Exception:
                                initial_data = self._data
                        else:
                            initial_data = processed_items
                    
                    if self._debug or MatrixLayout._debug:
                        logger.debug(f"Histogram '{letter}' inicializado con {len(processed_items) if processed_items else len(self._data)} items (hay selección activa)")
        
        # Crear histograma inicial con datos filtrados si hay selección, o todos los datos si no
        MatrixLayout.map_histogram(letter, initial_data, value_col=column, bins=bins, **kwargs)
        
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
        from .matrix import MatrixLayout
        
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero para establecer los datos")
        
        if column is None:
            raise ValueError("Debe especificar 'column' para el boxplot")
        
        # Verificar si ya existe un callback para este boxplot (evitar duplicados)
        if letter in self._boxplot_callbacks:
            if self._debug or MatrixLayout._debug:
                logger.warning(f"Boxplot para '{letter}' ya está registrado. Ignorando registro duplicado.")
            return self
        
        # Determinar a qué vista principal enlazar
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
                        logger.error(f"[ReactiveMatrixLayout] Vista principal '{linked_to}' no existe para boxplot '{letter}'")
                        logger.error(f"   - Scatter plots disponibles: {available_scatters}")
                        logger.error(f"   - Vistas principales disponibles: {available_primary}")
                        logger.error(f"   - Todas las vistas: {all_available}")
                    
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
                MatrixLayout.map_boxplot(letter, self._data, category_col=category_col, value_col=column, **kwargs)
                return self
            primary_letter = list(all_primary.keys())[-1]
            primary_selection = all_primary[primary_letter]
            if self._debug or MatrixLayout._debug:
                logger.debug(f"Boxplot '{letter}' enlazado automáticamente a vista principal '{primary_letter}'")
        
        # Agregar __linked_to__ al spec para indicadores visuales en JavaScript (solo si hay enlace)
        if primary_letter is not None:
            kwargs['__linked_to__'] = primary_letter
        else:
            kwargs.pop('__linked_to__', None)  # Remover si existe
        
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
            from .matrix import MatrixLayout
            
            # ✅ CORRECCIÓN CRÍTICA: Importar pandas al principio para evitar UnboundLocalError
            pd_module = None
            if has_pandas():
                # Intentar obtener pd de globals primero
                pd_module = globals().get('pd')
                if pd_module is None:
                    import sys
                    if 'pandas' in sys.modules:
                        pd_module = sys.modules['pandas']
                    else:
                        import pandas as pd_module
                        globals()['pd'] = pd_module
            
            # CRÍTICO: Flag para evitar ejecuciones múltiples simultáneas
            if hasattr(update_boxplot, '_executing') and update_boxplot._executing:
                if self._debug or MatrixLayout._debug:
                    logger.debug(f"   Boxplot '{letter}' callback ya está ejecutándose, ignorando llamada duplicada")
                return
            update_boxplot._executing = True
            
            # ✅ CORRECCIÓN: Validar que items tenga el formato correcto antes de procesar
            # Si items está vacío o no tiene la estructura esperada, usar todos los datos
            if not items or (isinstance(items, list) and len(items) == 0):
                if self._debug or MatrixLayout._debug:
                    logger.debug(f"   Boxplot '{letter}': items vacío, usando todos los datos")
                items = None
                count = 0
            
            try:
                import json
                from IPython.display import Javascript
                
                if self._debug or MatrixLayout._debug:
                    logger.debug(f"   Boxplot '{letter}' callback ejecutándose con {count} items")
                
                # ✅ CORRECCIÓN CRÍTICA: Usar datos seleccionados o todos los datos
                # Estrategia mejorada: usar índices originales si están disponibles, o crear DataFrame desde items
                data_to_use = self._data
                if items and len(items) > 0:
                    # ✅ ESTRATEGIA 1: Si tenemos índices originales en el payload, usarlos para filtrar self._data
                    # Esto garantiza que tenemos todas las columnas del DataFrame original
                    if has_pandas() and pd_module is not None and isinstance(self._data, pd_module.DataFrame):
                        # Buscar índices en el payload (pueden venir en diferentes formatos)
                        indices = None
                        if hasattr(items, '__iter__') and not isinstance(items, (str, dict)):
                            # Si items es una lista, buscar en el primer item o en el contexto
                            # Los índices pueden venir en el payload original, no en items
                            pass  # Los índices no están en items, están en el payload original
                        
                        # ✅ ESTRATEGIA 2: Extraer datos originales desde items
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
                                    # Si no tiene _original_row/_original_rows, el item ya es una fila original
                                    # (esto es común cuando viene de scatter plot)
                                    processed_items.append(item)
                            else:
                                processed_items.append(item)
                        
                        if processed_items:
                            try:
                                # Intentar crear DataFrame desde los items procesados
                                if has_pandas() and pd_module is not None:
                                    # ✅ CORRECCIÓN: Validar que processed_items tenga elementos antes de acceder a [0]
                                    if isinstance(processed_items, list) and len(processed_items) > 0:
                                    if isinstance(processed_items[0], dict):
                                        data_from_items = pd_module.DataFrame(processed_items)
                                    else:
                                        data_from_items = pd_module.DataFrame(processed_items)
                                    else:
                                        data_from_items = processed_items
                                    
                                    # ✅ CORRECCIÓN CRÍTICA: Verificar que el DataFrame tenga todas las columnas necesarias
                                    # Si falta la columna del boxplot, usar self._data completo
                                    if column and column not in data_from_items.columns:
                                        if self._debug or MatrixLayout._debug:
                                            logger.warning(f"Error actualizando boxplot: '{column}' no está en datos filtrados, usando todos los datos")
                                        data_to_use = self._data
                                    else:
                                        data_to_use = data_from_items
                                else:
                                    data_to_use = processed_items
                            except Exception as e:
                                if self._debug or MatrixLayout._debug:
                                    logger.warning(f"Error creando DataFrame desde items: {e}", exc_info=True)
                                # Si falla, usar todos los datos
                                data_to_use = self._data
                        else:
                            # Si no hay items procesados, usar todos los datos
                            data_to_use = self._data
                    else:
                        # Si no es DataFrame, usar items directamente
                        data_to_use = items if items else self._data
                else:
                    # Si no hay items, usar todos los datos (selección desactivada)
                    data_to_use = self._data
                
                # Preparar datos para boxplot
                # ✅ CORRECCIÓN: pd_module ya está definido al principio de la función
                if has_pandas() and pd_module is not None and isinstance(data_to_use, pd_module.DataFrame):
                        # ✅ CORRECCIÓN CRÍTICA: Verificar que las columnas necesarias existen
                        if column not in data_to_use.columns:
                            if self._debug or MatrixLayout._debug:
                                logger.warning(f"Error actualizando boxplot: '{column}' no está en datos. Columnas disponibles: {list(data_to_use.columns)[:10]}")
                            # Intentar usar todos los datos
                            data_to_use = self._data
                            if column not in data_to_use.columns:
                                if self._debug or MatrixLayout._debug:
                                    logger.error(f"Error crítico: '{column}' no está en datos originales")
                                update_boxplot._executing = False
                                return
                        
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
                            # ✅ CORRECCIÓN CRÍTICA: Verificar que la columna existe antes de acceder
                            if column not in data_to_use.columns:
                                if self._debug or MatrixLayout._debug:
                                    logger.warning(f"Error actualizando boxplot: '{column}' no está en datos. Columnas disponibles: {list(data_to_use.columns)[:10]}")
                                # Usar todos los datos si la columna no está en los datos filtrados
                                data_to_use = self._data
                                if column not in data_to_use.columns:
                                    if self._debug or MatrixLayout._debug:
                                        logger.error(f"Error crítico: '{column}' no está en datos originales")
                                    update_boxplot._executing = False
                                    return
                            
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
                        
                        // CRÍTICO: Usar getChartDimensions() para calcular dimensiones de manera consistente
                        // Esto asegura que respeta max_width y usa la misma lógica que el render inicial
                        const dims = window.getChartDimensions ? 
                            window.getChartDimensions(targetCell, {{ type: 'boxplot' }}, 400, 350) :
                            {{ width: Math.max(targetCell.clientWidth || 400, 200), height: 350 }};
                        const width = dims.width;
                        const height = dims.height;
                        const margin = {{ top: 20, right: 20, bottom: 40, left: 50 }};
                        const chartWidth = width - margin.left - margin.right;
                        const chartHeight = height - margin.top - margin.bottom;
                        
                        // CRÍTICO: Establecer altura mínima y máxima explícitamente en la celda
                        // para prevenir expansión infinita
                        targetCell.style.minHeight = height + 'px';
                        targetCell.style.maxHeight = height + 'px';
                        targetCell.style.height = height + 'px';
                        targetCell.style.overflow = 'hidden';
                        
                        const data = {box_data_json};
                        
                        if (data.length === 0) {{
                            targetCell.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos</div>';
                            window._bestlib_updating_boxplot_{letter} = false;
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
                            .domain(data.map(d => d.category))
                            .range([0, chartWidth])
                            .padding(0.2);
                        
                        const y = window.d3.scaleLinear()
                            .domain([window.d3.min(data, d => d.lower), window.d3.max(data, d => d.upper)])
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
                            const xAxis = g.append('g')
                                .attr('transform', `translate(0,${{chartHeight}})`)
                                .call(window.d3.axisBottom(x));
                            
                            const yAxis = g.append('g')
                                .call(window.d3.axisLeft(y));
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
                        logger.debug(f"   JavaScript del boxplot '{letter}' ejecutado (display_id: boxplot-update-{letter})")
                except Exception as e:
                    from .matrix import MatrixLayout
                    if self._debug or MatrixLayout._debug:
                        logger.error(f"Error ejecutando JavaScript del boxplot: {e}", exc_info=True)
                        import traceback
                        traceback.print_exc()
                    
            except Exception as e:
                from .matrix import MatrixLayout
                import traceback
                if self._debug or MatrixLayout._debug:
                    logger.error(f"Error actualizando boxplot: {e}", exc_info=True)
                    traceback.print_exc()
            finally:
                # CRÍTICO: Resetear flag después de completar
                update_boxplot._executing = False
                if self._debug or MatrixLayout._debug:
                    logger.debug(f"   Boxplot '{letter}' callback completado")
        
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
                    if has_pandas():
                        import pandas as pd
                        try:
                            # ✅ CORRECCIÓN: Validar que processed_items tenga elementos antes de acceder a [0]
                            if isinstance(processed_items, list) and len(processed_items) > 0:
                            if isinstance(processed_items[0], dict):
                                initial_data = pd.DataFrame(processed_items)
                            else:
                                initial_data = pd.DataFrame(processed_items)
                            else:
                                initial_data = self._data
                        except Exception:
                            initial_data = self._data
                    else:
                        initial_data = processed_items
                
                if self._debug or MatrixLayout._debug:
                        logger.debug(f"Boxplot '{letter}' inicializado con {len(processed_items) if processed_items else len(self._data)} items (hay selección activa)")
        
        # Debug: verificar que el callback se registró
        if self._debug or MatrixLayout._debug:
            logger.debug(f"[ReactiveMatrixLayout] Callback registrado para boxplot '{letter}' enlazado a vista principal '{primary_letter}'")
            logger.debug(f"   - SelectionModel ID: {id(primary_selection)}")
            logger.debug(f"   - Callbacks registrados: {len(primary_selection._callbacks)}")
            logger.debug(f"   - Boxplot callbacks guardados: {list(self._boxplot_callbacks.keys())}")
        
        # Crear boxplot inicial con datos filtrados si hay selección, o todos los datos si no
        data_to_use = initial_data
        # Asegurar que pd esté disponible si has_pandas() es True
        # Usar globals() para acceder al pd del módulo y evitar UnboundLocalError
                if has_pandas():
            # Obtener pd del módulo global
            pd_module = globals().get('pd')
            if pd_module is None:
                import sys
                if 'pandas' in sys.modules:
                    pd_module = sys.modules['pandas']
                else:
                    import pandas as pd_module
                    globals()['pd'] = pd_module
            # Usar pd_module en lugar de pd para evitar UnboundLocalError
            if pd_module is not None and isinstance(data_to_use, pd_module.DataFrame):
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
                # Si no es DataFrame, usar fallback para listas de diccionarios
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
            if has_pandas() and isinstance(data, get_pandas().DataFrame):
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
                logger.error(f"Error preparando datos del bar chart: {e}", exc_info=True)
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
        from .matrix import MatrixLayout
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
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                data_to_use = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                if isinstance(items[0], dict):
                    pd = get_pandas()
                    # ✅ CRIT-002: Usar helper centralizado
                    df_result = safe_dataframe(items)
                    data_to_use = df_result if df_result is not None else items
                else:
                    data_to_use = items
            else:
                data_to_use = items
            try:
                MatrixLayout.map_heatmap(letter, data_to_use, x_col=x_col, y_col=y_col, value_col=value_col, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self

    def add_correlation_heatmap(self, letter, linked_to=None, **kwargs):
        from .matrix import MatrixLayout
        if not (has_pandas() and isinstance(self._data, get_pandas().DataFrame)):
            raise ValueError("add_correlation_heatmap requiere DataFrame")
        MatrixLayout.map_correlation_heatmap(letter, self._data, **kwargs)
        # link
        if not self._scatter_selection_models:
            return self
        scatter_letter = linked_to or list(self._scatter_selection_models.keys())[-1]
        sel = self._scatter_selection_models[scatter_letter]
        def update(items, count):
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                df = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
                if isinstance(items, list) and len(items) > 0:
                    # ✅ CRIT-002, CRIT-003: Validar items antes de acceder
                first_item = safe_get_first_item(items)
                if first_item is not None and isinstance(first_item, dict):
                    df_result = safe_dataframe(items)
                    if df_result is not None:
                        df = df_result
                    else:
                        df = None
                else:
                    df = None
            else:
                df = None
            if df is None:
                return
            try:
                MatrixLayout.map_correlation_heatmap(letter, df, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self

    def add_line(self, letter, x_col=None, y_col=None, series_col=None, linked_to=None, **kwargs):
        from .matrix import MatrixLayout
        if self._data is None:
            raise ValueError("Debe usar set_data() primero")
        MatrixLayout.map_line(letter, self._data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
        if not self._scatter_selection_models:
            return self
        scatter_letter = linked_to or list(self._scatter_selection_models.keys())[-1]
        sel = self._scatter_selection_models[scatter_letter]
        def update(items, count):
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                data_to_use = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                if isinstance(items[0], dict):
                    pd = get_pandas()
                    # ✅ CRIT-002: Usar helper centralizado
                    df_result = safe_dataframe(items)
                    data_to_use = df_result if df_result is not None else items
                else:
                    data_to_use = items
            else:
                data_to_use = items
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
                import __main__
                # Asegurar que pd esté disponible (usar el del módulo global)
                if has_pandas():
                    pd_module = globals().get('pd')
                    if pd_module is None:
                        import sys
                        if 'pandas' in sys.modules:
                            pd_module = sys.modules['pandas']
                        else:
                            import pandas as pd_module
                            globals()['pd'] = pd_module
                    empty_df = pd_module.DataFrame() if pd_module is not None else []
                else:
                    empty_df = []
                setattr(__main__, selection_var, empty_df)
                if self._debug or MatrixLayout._debug:
                    df_type = "DataFrame" if has_pandas() else "lista"
                    logger.debug(f"Variable '{selection_var}' creada para guardar selecciones de pie chart '{letter}' como {df_type}")
            
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
                        logger.debug(f"[ReactiveMatrixLayout] Evento de pie chart ignorado: esperado '{letter}', recibido '{event_letter}'")
                    return
                
                # Si event_letter es None, podría ser un evento antiguo sin __view_letter__
                # En ese caso, procesar solo si no hay otros handlers más específicos
                # Por ahora, procesar si event_letter es None o coincide con letter
                items = payload.get('items', [])
                
                if self._debug or MatrixLayout._debug:
                    logger.debug(f"[ReactiveMatrixLayout] Evento recibido para pie chart '{letter}': {len(items)} items")
                
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
                logger.debug(f"[ReactiveMatrixLayout] Handler registrado para pie chart '{letter}' con selection_var='{selection_var}'")
            
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
                from .matrix import MatrixLayout
                from collections import defaultdict
                import json
                from IPython.display import Javascript
                import traceback
                import hashlib
                
                # Prevenir actualizaciones recursivas
                if self._update_flags.get(pie_update_flag, False):
                    if self._debug or MatrixLayout._debug:
                        logger.debug(f"[ReactiveMatrixLayout] Actualización de pie chart '{letter}' ya en progreso, ignorando...")
                    return
                
                self._update_flags[pie_update_flag] = True
                
                try:
                    if self._debug or MatrixLayout._debug:
                        logger.debug(f"[ReactiveMatrixLayout] Callback ejecutado: Actualizando pie chart '{letter}' con {count} items seleccionados")
                    
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
                            # ✅ CORRECCIÓN: Validar que processed_items tenga elementos antes de acceder a [0]
                            if has_pandas() and isinstance(processed_items, list) and len(processed_items) > 0:
                                if isinstance(processed_items[0], dict):
                                    pd = get_pandas()
                                    if pd is not None:
                                data_to_use = pd.DataFrame(processed_items)
                            else:
                                        data_to_use = processed_items
                                else:
                                    data_to_use = processed_items
                            else:
                                data_to_use = processed_items
                                else:
                                    data_to_use = processed_items
                            else:
                                data_to_use = processed_items
                                data_to_use = processed_items
                        else:
                            # Si no hay items procesados, usar todos los datos
                            data_to_use = self._data
                    else:
                        # Si no hay items, usar todos los datos
                        data_to_use = self._data
                    
                    # Validar que category_col existe en los datos
                    if has_pandas() and isinstance(data_to_use, get_pandas().DataFrame):
                        if category_col and category_col not in data_to_use.columns:
                            if self._debug or MatrixLayout._debug:
                                logger.warning(f"Columna '{category_col}' no encontrada en datos. Columnas disponibles: {list(data_to_use.columns)}")
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
                        if has_pandas() and isinstance(data_to_use, get_pandas().DataFrame):
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
                                    logger.warning(f"No se puede crear pie chart: columna '{category_col}' no encontrada")
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
                                    logger.debug(f"[ReactiveMatrixLayout] Datos del pie chart '{letter}' no han cambiado, ignorando actualización")
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
                                logger.error(f"Error ejecutando JavaScript del pie chart: {e}", exc_info=True)
                                import traceback
                                traceback.print_exc()
                    except Exception as e:
                        if self._debug or MatrixLayout._debug:
                            logger.error(f"Error actualizando pie chart con JavaScript: {e}", exc_info=True)
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
                        logger.error(f"Error actualizando pie chart: {e}", exc_info=True)
                        traceback.print_exc()
                    # Reset flag en caso de error
                    self._update_flags[pie_update_flag] = False
            
            # Registrar callback en el SelectionModel de la vista principal
            primary_selection.on_change(update_pie)
            
            # Debug: verificar que el callback se registró
            if self._debug or MatrixLayout._debug:
                logger.debug(f"[ReactiveMatrixLayout] Callback registrado para pie chart '{letter}' enlazado a vista principal '{primary_letter}'")
                logger.debug(f"   - SelectionModel ID: {id(primary_selection)}")
                logger.debug(f"   - Callbacks registrados: {len(primary_selection._callbacks)}")
        
        return self

    def add_violin(self, letter, value_col=None, category_col=None, bins=20, linked_to=None, **kwargs):
        from .matrix import MatrixLayout
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
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                data_to_use = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                if isinstance(items[0], dict):
                    pd = get_pandas()
                    # ✅ CRIT-002: Usar helper centralizado
                    df_result = safe_dataframe(items)
                    data_to_use = df_result if df_result is not None else items
                else:
                    data_to_use = items
            else:
                data_to_use = items
            try:
                MatrixLayout.map_violin(letter, data_to_use, value_col=value_col, category_col=category_col, bins=bins, **kwargs)
            except Exception:
                pass
        sel.on_change(update)
        return self

    def add_radviz(self, letter, features=None, class_col=None, linked_to=None, **kwargs):
        from .matrix import MatrixLayout
        if not (has_pandas() and isinstance(self._data, get_pandas().DataFrame)):
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
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                df = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
                if isinstance(items, list) and len(items) > 0:
                    # ✅ CRIT-002, CRIT-003: Validar items antes de acceder
                first_item = safe_get_first_item(items)
                if first_item is not None and isinstance(first_item, dict):
                    df_result = safe_dataframe(items)
                    if df_result is not None:
                        df = df_result
                    else:
                        df = None
                else:
                    df = None
            else:
                df = None
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
        from .matrix import MatrixLayout
        if not (has_pandas() and isinstance(self._data, get_pandas().DataFrame)):
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
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                df = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
                if isinstance(items, list) and len(items) > 0:
                    # ✅ CRIT-002, CRIT-003: Validar items antes de acceder
                first_item = safe_get_first_item(items)
                if first_item is not None and isinstance(first_item, dict):
                    df_result = safe_dataframe(items)
                    if df_result is not None:
                        df = df_result
                    else:
                        df = None
                else:
                    df = None
            else:
                df = None
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
        from .matrix import MatrixLayout
        if not (has_pandas() and isinstance(self._data, get_pandas().DataFrame)):
            raise ValueError("add_parallel_coordinates requiere DataFrame")
        MatrixLayout.map_parallel_coordinates(letter, self._data, dimensions=dimensions, category_col=category_col, **kwargs)
        
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
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                df = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
                if isinstance(items, list) and len(items) > 0:
                    # ✅ CRIT-002, CRIT-003: Validar items antes de acceder
                first_item = safe_get_first_item(items)
                if first_item is not None and isinstance(first_item, dict):
                    df_result = safe_dataframe(items)
                    if df_result is not None:
                        df = df_result
                    else:
                        df = None
                else:
                    df = None
            else:
                df = None
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
        from .matrix import MatrixLayout
        if not (has_pandas() and isinstance(self._data, get_pandas().DataFrame)):
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
            # ✅ CRIT-002: Usar get_pandas() en lugar de pd directo
            pd = get_pandas()
            # ✅ CRIT-002: Usar get_pandas() en lugar de pd directo
            pd = get_pandas()
            if pd is not None:
            cm_df = pd.DataFrame(cm, index=labels, columns=labels)
            else:
                raise ImportError("pandas es requerido para confusion matrix")
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
            # ✅ CRIT-002, CRIT-003: Validar items antes de acceder
            first_item = safe_get_first_item(items)
            if first_item is not None and isinstance(first_item, dict):
                df_result = safe_dataframe(items)
                df_sel = df_result if df_result is not None else self._data
                else:
                    df_sel = self._data
            else:
                df_sel = self._data
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
        MatrixLayout.map_line_plot(letter, self._data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                data_to_use = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                if isinstance(items[0], dict):
                    pd = get_pandas()
                    # ✅ CRIT-002: Usar helper centralizado
                    df_result = safe_dataframe(items)
                    data_to_use = df_result if df_result is not None else items
                else:
                    data_to_use = items
            else:
                data_to_use = items
            try:
                MatrixLayout.map_line_plot(letter, data_to_use, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
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
        MatrixLayout.map_horizontal_bar(letter, self._data, category_col=category_col, value_col=value_col, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                data_to_use = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                if isinstance(items[0], dict):
                    pd = get_pandas()
                    # ✅ CRIT-002: Usar helper centralizado
                    df_result = safe_dataframe(items)
                    data_to_use = df_result if df_result is not None else items
                else:
                    data_to_use = items
            else:
                data_to_use = items
            try:
                MatrixLayout.map_horizontal_bar(letter, data_to_use, category_col=category_col, value_col=value_col, **kwargs)
            except Exception:
                pass
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
        MatrixLayout.map_hexbin(letter, self._data, x_col=x_col, y_col=y_col, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                data_to_use = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                if isinstance(items[0], dict):
                    pd = get_pandas()
                    # ✅ CRIT-002: Usar helper centralizado
                    df_result = safe_dataframe(items)
                    data_to_use = df_result if df_result is not None else items
                else:
                    data_to_use = items
            else:
                data_to_use = items
            try:
                MatrixLayout.map_hexbin(letter, data_to_use, x_col=x_col, y_col=y_col, **kwargs)
            except Exception:
                pass
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
        MatrixLayout.map_errorbars(letter, self._data, x_col=x_col, y_col=y_col, yerr=yerr, xerr=xerr, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                data_to_use = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                if isinstance(items[0], dict):
                    pd = get_pandas()
                    # ✅ CRIT-002: Usar helper centralizado
                    df_result = safe_dataframe(items)
                    data_to_use = df_result if df_result is not None else items
                else:
                    data_to_use = items
            else:
                data_to_use = items
            try:
                MatrixLayout.map_errorbars(letter, data_to_use, x_col=x_col, y_col=y_col, yerr=yerr, xerr=xerr, **kwargs)
            except Exception:
                pass
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
        MatrixLayout.map_fill_between(letter, self._data, x_col=x_col, y1=y1, y2=y2, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                data_to_use = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                if isinstance(items[0], dict):
                    pd = get_pandas()
                    # ✅ CRIT-002: Usar helper centralizado
                    df_result = safe_dataframe(items)
                    data_to_use = df_result if df_result is not None else items
                else:
                    data_to_use = items
            else:
                data_to_use = items
            try:
                MatrixLayout.map_fill_between(letter, data_to_use, x_col=x_col, y1=y1, y2=y2, **kwargs)
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
        MatrixLayout.map_step(letter, self._data, x_col=x_col, y_col=y_col, **kwargs)
        if linked_to is None:
            return self
        if linked_to in self._scatter_selection_models:
            sel = self._scatter_selection_models[linked_to]
        elif linked_to in self._primary_view_models:
            sel = self._primary_view_models[linked_to]
        else:
            return self
        def update(items, count):
            # ✅ CORRECCIÓN: Validar items antes de acceder a items[0]
            if not items:
                data_to_use = self._data
            elif has_pandas() and isinstance(items, list) and len(items) > 0:
                if isinstance(items[0], dict):
                    pd = get_pandas()
                    # ✅ CRIT-002: Usar helper centralizado
                    df_result = safe_dataframe(items)
                    data_to_use = df_result if df_result is not None else items
                else:
                    data_to_use = items
            else:
                data_to_use = items
            try:
                MatrixLayout.map_step(letter, data_to_use, x_col=x_col, y_col=y_col, **kwargs)
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
        # Cargar assets automáticamente en Colab
        from ..render.assets import AssetManager
        AssetManager.ensure_colab_assets_loaded()
        
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
            logger.warning("ipywidgets no está instalado")
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
            # Buscar la variable en el namespace del usuario
            import __main__
            if hasattr(__main__, selection_var):
                return getattr(__main__, selection_var)
            else:
                # Si no existe, buscar en _selection_variables para encontrar la letra correspondiente
                for view_letter, var_name in self._selection_variables.items():
                    if var_name == selection_var:
                        # Retornar la selección del modelo de esa vista
                        if view_letter in self._primary_view_models:
                            return self._primary_view_models[view_letter].get_items()
                # Si no se encuentra, retornar DataFrame vacío
                if has_pandas():
                    # ✅ CRIT-002: Usar helper centralizado
                    return safe_dataframe([]) or []
                else:
                    return []
        else:
            # Retornar selección del modelo principal
            return self.selection_model.get_items()
    
    def set_selection(self, selection_var_name, items):
        """
        Guarda la selección en una variable Python por su nombre.
        
        Args:
            selection_var_name (str): Nombre de la variable donde guardar la selección.
            items (list or pd.DataFrame): Los items a guardar.
        """
        import __main__
        setattr(__main__, selection_var_name, items)
        if self._debug or MatrixLayout._debug:
            count_msg = f"{len(items)} filas" if has_pandas() and isinstance(items, pd.DataFrame) else f"{len(items)} items"
            logger.debug(f"Selección guardada en variable '{selection_var_name}': {count_msg}")


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


