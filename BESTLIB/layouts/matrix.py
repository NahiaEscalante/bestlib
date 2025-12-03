"""
MatrixLayout - Refactorizado para usar módulos modulares
"""
import uuid
import copy
import weakref
from ..core.events import EventManager
from ..core.comm import CommManager
from ..core.layout import LayoutEngine
from ..render.html import HTMLGenerator
from ..render.builder import JSBuilder
from ..render.assets import AssetManager
from ..utils.figsize import figsize_to_pixels, process_figsize_in_kwargs
from ..core.exceptions import LayoutError
from ..charts.spec_utils import validate_spec

try:
    import ipywidgets as widgets
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False

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


class MatrixLayout:
    """
    Layout de matriz ASCII refactorizado para usar módulos modulares.
    Mantiene compatibilidad hacia atrás con la API original.
    """
    _debug = False  # Modo debug para ver mensajes detallados
    _safe_html = True
    _instances = weakref.WeakSet()
    _current_theme = 'light'  # Tema actual: 'light', 'dark', o 'christmas'
    
    def __init__(self, ascii_layout=None, figsize=None, row_heights=None, 
                 col_widths=None, gap=None, cell_padding=None, max_width=None):
        """
        Crea una nueva instancia de MatrixLayout.
        
        Args:
            ascii_layout (str, optional): Layout ASCII. Si no se proporciona, se genera uno simple.
            figsize (tuple, optional): Tamaño global de gráficos (width, height) en pulgadas.
            row_heights (list, optional): Lista de alturas por fila (px o fr).
            col_widths (list, optional): Lista de anchos por columna (px, fr, o ratios).
            gap (int, optional): Espaciado entre celdas en píxeles.
            cell_padding (int, optional): Padding de celdas en píxeles.
            max_width (int, optional): Ancho máximo del layout en píxeles.
        """
        # Si no se proporciona layout, crear uno simple
        if ascii_layout is None:
            ascii_layout = "A"
        
        self.ascii_layout = ascii_layout
        self.div_id = "matrix-" + str(uuid.uuid4())
        self._map = {}  # Cada instancia tiene su propio mapeo independiente
        self.__class__._instances.add(self)
        
        # Usar CommManager para registro de instancia
        CommManager.register_instance(self.div_id, self)
        
        # Usar EventManager para gestión de eventos
        self._event_manager = EventManager()
        
        # Flag para rastrear si hay handlers personalizados
        self._has_custom_select_handler = False
        
        # Registrar handler por defecto para eventos 'select' que muestre los datos
        self._register_default_select_handler()
        
        # Configuración del layout
        self._reactive_model = None
        self._merge_opt = None
        self._figsize = figsize
        self._row_heights = row_heights
        self._col_widths = col_widths
        self._gap = gap
        self._cell_padding = cell_padding
        self._max_width = max_width
        self._instance_theme = None  # Tema específico de esta instancia (None = usar tema global)
        
        # Validar y parsear layout usando LayoutEngine
        try:
            self._grid = LayoutEngine.parse_ascii_layout(ascii_layout)
        except LayoutError as e:
            raise LayoutError(f"Layout ASCII inválido: {e}")
        
        # Asegurar que el comm esté registrado usando CommManager
        CommManager.register_comm()
    
    @classmethod
    def set_debug(cls, enabled: bool):
        """
        Activa/desactiva mensajes de debug.
        
        Args:
            enabled (bool): Si True, activa mensajes detallados de debug.
                           Si False, solo muestra errores críticos.
        """
        cls._debug = bool(enabled)
    
    @classmethod
    def set_theme(cls, theme_name: str):
        """
        Establece el tema global para todas las nuevas instancias de MatrixLayout.
        
        Args:
            theme_name (str): Nombre del tema. Valores válidos: 'light', 'dark', 'christmas'
        
        Raises:
            ValueError: Si el nombre del tema no es válido
        
        Ejemplo:
            MatrixLayout.set_theme('dark')  # Cambiar a modo oscuro
            layout = MatrixLayout("ABC")  # Esta instancia usará modo oscuro
        """
        valid_themes = ['light', 'dark', 'christmas']
        if theme_name not in valid_themes:
            raise ValueError(f"Tema inválido: {theme_name}. Temas válidos: {valid_themes}")
        cls._current_theme = theme_name
    
    @classmethod
    def get_theme(cls):
        """
        Obtiene el tema actual.
        
        Returns:
            str: Nombre del tema actual ('light', 'dark', o 'christmas')
        """
        return cls._current_theme
    
    def set_theme(self, theme_name: str):
        """
        Establece el tema para esta instancia específica.
        
        Args:
            theme_name (str): Nombre del tema. Valores válidos: 'light', 'dark', 'christmas'
        
        Returns:
            self: Para permitir encadenamiento de métodos
        
        Raises:
            ValueError: Si el nombre del tema no es válido
        
        Ejemplo:
            layout = MatrixLayout("ABC")
            layout.set_theme('christmas')  # Solo esta instancia usará tema navidad
        """
        valid_themes = ['light', 'dark', 'christmas']
        if theme_name not in valid_themes:
            raise ValueError(f"Tema inválido: {theme_name}. Temas válidos: {valid_themes}")
        self._instance_theme = theme_name
        return self
        EventManager.set_debug(enabled)
        CommManager.set_debug(enabled)
    
    @classmethod
    def on_global(cls, event, func):
        """Registra un callback global para un tipo de evento"""
        EventManager.on_global(event, func)
    
    def on(self, event, func):
        """Registra un callback específico para esta instancia"""
        self._event_manager.on(event, func)
        # Si se registra un handler personalizado para 'select', marcar que hay uno personalizado
        if event == 'select':
            self._has_custom_select_handler = True
        return self
    
    def _register_default_select_handler(self):
        """Registra un handler por defecto para eventos 'select' que muestre los datos seleccionados"""
        def default_select_handler(payload):
            """Handler por defecto que muestra los datos seleccionados (solo si no hay handlers personalizados)"""
            # Solo ejecutar si no hay handlers personalizados
            if self._has_custom_select_handler:
                return
            
            items = payload.get('items', [])
            count = payload.get('count', len(items))
            
            if count == 0:
                print("📊 No hay elementos seleccionados")
                return
            
            print(f"\n📊 Elementos seleccionados: {count}")
            print("=" * 60)
            
            # Mostrar los primeros elementos (máximo 10 para no saturar)
            display_count = min(count, 10)
            for i, item in enumerate(items[:display_count]):
                print(f"\n[{i+1}]")
                for key, value in item.items():
                    if key != 'index' and key != '_original_row':
                        print(f"   {key}: {value}")
            
            if count > display_count:
                print(f"\n... y {count - display_count} elemento(s) más")
            print("=" * 60)
            print(f"\n💡 Tip: Usa layout.on('select', tu_funcion) para personalizar el manejo de selecciones")
        
        self._event_manager.on('select', default_select_handler)
    
    @classmethod
    def register_comm(cls, force=False):
        """Registra manualmente el comm target de Jupyter"""
        return CommManager.register_comm(force=force)
    
    def connect_selection(self, reactive_model, scatter_letter=None):
        """
        Conecta un modelo reactivo para actualizar automáticamente.
        
        Args:
            reactive_model: Instancia de ReactiveData o SelectionModel
            scatter_letter: Letra del scatter plot (opcional)
        """
        if not HAS_WIDGETS:
            print("⚠️ ipywidgets no está instalado. Instala con: pip install ipywidgets")
            return
        
        self._reactive_model = reactive_model
        self._scatter_letter = scatter_letter
        
        def update_model(payload):
            event_scatter_letter = payload.get('__scatter_letter__')
            if scatter_letter and event_scatter_letter and event_scatter_letter != scatter_letter:
                return
            
            items = payload.get('items', [])
            original_rows = []
            for item in items:
                if '_original_row' in item:
                    original_rows.append(item['_original_row'])
                else:
                    original_rows.append(item)
            reactive_model.update(original_rows)
        
        self._event_manager.on('select', update_model)
        # Marcar que hay un handler personalizado (connect_selection también cuenta como personalizado)
        self._has_custom_select_handler = True
        return self
    
    def __del__(self):
        """Limpia la referencia cuando se destruye la instancia"""
        CommManager.unregister_instance(self.div_id)
        try:
            self.__class__._instances.discard(self)
        except Exception:
            pass
    
    @classmethod
    def map(cls, mapping):
        """Mapea gráficos a letras del layout (método legacy de compatibilidad)."""
        # Este método ahora es solo para compatibilidad hacia atrás
        # En la práctica, cada instancia maneja su propio _map
        # Para usar este método, se debe llamar desde una instancia: instance.set_mapping(mapping)
        import warnings
        warnings.warn(
            "MatrixLayout.map() es un método legacy. Use instance.set_mapping() en su lugar.",
            DeprecationWarning,
            stacklevel=2
        )
        return mapping
    
    def _register_spec(self, letter, spec):
        """Registra un spec en el mapeo de esta instancia."""
        validate_spec(spec)
        self._map[letter] = copy.deepcopy(spec)
        return spec
    
    def update_spec_metadata(self, letter, **metadata):
        """Actualiza metadata en un spec de esta instancia."""
        spec = self._map.get(letter)
        if not spec:
            return
        spec.update(metadata)
    
    @classmethod
    def _register_spec_legacy(cls, letter, spec):
        """Helper para métodos map_* de clase (compatibilidad hacia atrás)."""
        instances = list(cls._instances)
        if instances:
            return instances[-1]._register_spec(letter, spec)
        return spec
    
    # Métodos map_* delegados al sistema de gráficos
    @classmethod
    def map_scatter(cls, letter, data, **kwargs):
        """Método helper para crear scatter plot (método de clase legacy)"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('scatter')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_barchart(cls, letter, data, **kwargs):
        """Método helper para crear bar chart"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('bar')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_line_plot(cls, letter, data, **kwargs):
        """Método helper para crear line plot completo"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('line_plot')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_horizontal_bar(cls, letter, data, **kwargs):
        """Método helper para crear horizontal bar chart"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('horizontal_bar')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_hexbin(cls, letter, data, **kwargs):
        """Método helper para crear hexbin chart"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('hexbin')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_errorbars(cls, letter, data, **kwargs):
        """Método helper para crear errorbars chart"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('errorbars')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_fill_between(cls, letter, data, **kwargs):
        """Método helper para crear fill_between chart"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('fill_between')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_step(cls, letter, data, x_col=None, y_col=None, **kwargs):
        """Método helper para crear step plot"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('step_plot')
            spec = chart.get_spec(data, x_col=x_col, y_col=y_col, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_step(letter, data, x_col=x_col, y_col=y_col, **kwargs)
            except Exception:
                spec = {'type': 'step_plot', 'data': [], **kwargs}
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_kde(cls, letter, data, **kwargs):
        """Método helper para crear KDE"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('kde')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_distplot(cls, letter, data, **kwargs):
        """Método helper para crear distplot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('distplot')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_rug(cls, letter, data, **kwargs):
        """Método helper para crear rug plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('rug')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_qqplot(cls, letter, data, **kwargs):
        """Método helper para crear Q-Q plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('qqplot')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_ecdf(cls, letter, data, **kwargs):
        """Método helper para crear ECDF"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('ecdf')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_ridgeline(cls, letter, data, **kwargs):
        """Método helper para crear ridgeline plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('ridgeline')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_ribbon(cls, letter, data, **kwargs):
        """Método helper para crear ribbon plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('ribbon')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_hist2d(cls, letter, data, **kwargs):
        """Método helper para crear 2D histogram"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('hist2d')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_polar(cls, letter, data, **kwargs):
        """Método helper para crear polar plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('polar')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_funnel(cls, letter, data, **kwargs):
        """Método helper para crear funnel plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('funnel')
        spec = chart.get_spec(data, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_histogram(cls, letter, data, value_col=None, bins=10, **kwargs):
        """Método helper para crear histograma"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('histogram')
            spec = chart.get_spec(data, column=value_col, bins=bins, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy si ChartRegistry no tiene histogram
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_histogram(letter, data, value_col=value_col, bins=bins, **kwargs)
            except Exception:
                spec = {'type': 'histogram', 'data': [], **kwargs}
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_pie(cls, letter, data, category_col=None, value_col=None, **kwargs):
        """Método helper para crear pie chart"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('pie')
            spec = chart.get_spec(data, category_col=category_col, value_col=value_col, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_pie(letter, data, category_col=category_col, value_col=value_col, **kwargs)
            except Exception:
                spec = {'type': 'pie', 'data': [], **kwargs}
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_boxplot(cls, letter, data, category_col=None, value_col=None, column=None, **kwargs):
        """Método helper para crear boxplot"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('boxplot')
            # Permitir 'column' como alias de 'value_col'
            if value_col is None and column is not None:
                value_col = column
            spec = chart.get_spec(data, category_col=category_col, value_col=value_col, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_boxplot(letter, data, category_col=category_col, value_col=value_col, column=column, **kwargs)
            except Exception:
                spec = {'type': 'boxplot', 'data': [], **kwargs}
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_line(cls, letter, data, x_col=None, y_col=None, series_col=None, **kwargs):
        """Método helper para crear line chart (multi-series)"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('line')
            spec = chart.get_spec(data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_line(letter, data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
            except Exception:
                spec = {'type': 'line', 'data': [], **kwargs}
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_heatmap(cls, letter, data, x_col=None, y_col=None, value_col=None, **kwargs):
        """Método helper para crear heatmap"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('heatmap')
            spec = chart.get_spec(data, x_col=x_col, y_col=y_col, value_col=value_col, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_heatmap(letter, data, x_col=x_col, y_col=y_col, value_col=value_col, **kwargs)
            except Exception:
                spec = {'type': 'heatmap', 'data': [], **kwargs}
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_violin(cls, letter, data, value_col=None, category_col=None, bins=20, **kwargs):
        """Método helper para crear violin plot"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('violin')
            spec = chart.get_spec(data, value_col=value_col, category_col=category_col, bins=bins, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_violin(letter, data, value_col=value_col, category_col=category_col, bins=bins, **kwargs)
            except Exception:
                spec = {'type': 'violin', 'data': [], **kwargs}
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_radviz(cls, letter, data, features=None, class_col=None, **kwargs):
        """Método helper para crear radviz plot"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('radviz')
            spec = chart.get_spec(data, features=features, class_col=class_col, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_radviz(letter, data, features=features, class_col=class_col, **kwargs)
            except Exception:
                spec = {'type': 'radviz', 'data': [], **kwargs}
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_star_coordinates(cls, letter, data, features=None, class_col=None, **kwargs):
        """Método helper para crear star coordinates plot"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('star_coordinates')
            spec = chart.get_spec(data, features=features, class_col=class_col, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_star_coordinates(letter, data, features=features, class_col=class_col, **kwargs)
            except Exception:
                spec = {'type': 'star_coordinates', 'data': [], **kwargs}
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_parallel_coordinates(cls, letter, data, dimensions=None, category_col=None, **kwargs):
        """Método helper para crear parallel coordinates plot"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('parallel_coordinates')
            spec = chart.get_spec(data, dimensions=dimensions, category_col=category_col, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_parallel_coordinates(letter, data, dimensions=dimensions, category_col=category_col, **kwargs)
            except Exception:
                spec = {'type': 'parallel_coordinates', 'data': [], **kwargs}
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_grouped_barchart(cls, letter, data, main_col=None, sub_col=None, value_col=None, **kwargs):
        """Método helper para crear grouped bar chart"""
        from ..charts import ChartRegistry
        # IMPORTANTE: El chart está registrado como 'grouped_bar', no 'grouped_barchart'
        chart = ChartRegistry.get('grouped_bar')
        spec = chart.get_spec(data, main_col=main_col, sub_col=sub_col, value_col=value_col, **kwargs)
        return cls._register_spec_legacy(letter, spec)
    
    @classmethod
    def map_correlation_heatmap(cls, letter, data, **kwargs):
        """
        Calcula matriz de correlación (pearson) para columnas numéricas del DataFrame.
        Las etiquetas X e Y están ordenadas de la misma manera para mantener consistencia.
        """
        if not (HAS_PANDAS and isinstance(data, pd.DataFrame)):
            raise ValueError("map_correlation_heatmap requiere DataFrame de pandas")
        num_df = data.select_dtypes(include=['number'])
        if num_df.shape[1] == 0:
            raise ValueError("No hay columnas numéricas para correlación")
        corr = num_df.corr().fillna(0.0)
        # Ordenar columnas alfabéticamente para consistencia
        cols = sorted(corr.columns.tolist())
        corr = corr.loc[cols, cols]  # Reordenar matriz de correlación
        cells = []
        # Crear celdas asegurando que x e y estén en el mismo orden
        for i, xi in enumerate(cols):
            for j, yj in enumerate(cols):
                cells.append({'x': str(xi), 'y': str(yj), 'value': float(corr.loc[yj, xi])})
        
        # Procesar figsize si está en kwargs
        from ..utils.figsize import process_figsize_in_kwargs
        process_figsize_in_kwargs(kwargs)
        
        # Opción para mostrar valores numéricos (por defecto False)
        showValues = kwargs.pop('showValues', False)
        
        spec = {
            'type': 'heatmap',
            'data': cells,
            'cells': cells,
            'xLabels': cols,
            'yLabels': cols,
            'x_labels': cols,
            'y_labels': cols,
            'isCorrelation': True,
            'showValues': showValues,
            'colorScale': 'diverging',
            **kwargs
        }
        return cls._register_spec_legacy(letter, spec)
    
    def set_mapping(self, mapping, merge=False):
        """
        Define un mapeo específico para esta instancia (sin afectar el global).
        """
        mapping_copy = copy.deepcopy(mapping)
        if merge and hasattr(self, '_map'):
            self._map.update(mapping_copy)
        else:
            self._map = mapping_copy
        return self
    
    def _layout_letters(self):
        """Retorna las letras únicas definidas en el layout ASCII."""
        if not hasattr(self, '_grid') or not getattr(self._grid, 'cells', None):
            return set()
        letters = set()
        for cell in self._grid.cells.values():
            letter = cell.get('letter')
            if letter and letter.strip():
                letters.add(letter)
        return letters
    
    def _validate_mapping_letters(self, mapping):
        """
        Valida que el mapping cubra solo las letras definidas en el layout.
        Ahora solo valida las letras que están en el layout, ignorando extras.
        """
        valid_letters = self._layout_letters()
        mapped_letters = {k for k in mapping.keys() if not k.startswith('__')}
        
        # Solo validar que las letras del layout tengan specs
        # Ignorar specs extra (pueden ser de otros dashboards)
        missing = valid_letters - mapped_letters
        
        if missing and self._debug:
            print(f"⚠️ [MatrixLayout] Letras sin gráfico asignado: {sorted(missing)}")
    
    def _prepare_repr_data(self, layout_to_use=None):
        """
        Prepara datos comunes para _repr_html_ y _repr_mimebundle_.
        Usa AssetManager y módulos de renderizado.
        """
        # Cargar JS y CSS usando AssetManager
        js_code = AssetManager.load_js()
        css_code = AssetManager.load_css()
        
        # Usar el layout proporcionado o el de la instancia
        layout = layout_to_use if layout_to_use is not None else self.ascii_layout
        
        # Validar layout usando LayoutEngine
        try:
            grid = LayoutEngine.parse_ascii_layout(layout)
        except LayoutError:
            # Si falla, usar validación básica
            rows = [r for r in layout.strip().split("\n") if r]
            if not rows:
                raise LayoutError("ascii_layout no puede estar vacío")
            col_len = len(rows[0])
            if any(len(r) != col_len for r in rows):
                raise LayoutError("Todas las filas del ascii_layout deben tener igual longitud")
            row_count = len(rows)
            col_count = col_len
        else:
            row_count = grid.rows
            col_count = grid.cols
        
        # Escapar layout ASCII
        escaped_layout = layout.replace("`", "\\`")
        
        # Preparar metadata
        meta = {
            "__safe_html__": bool(self._safe_html),
            "__div_id__": self.div_id,
            "__row_count__": row_count,
            "__col_count__": col_count
        }
        
        # Agregar configuración de matriz si existe
        if self._row_heights is not None:
            meta["__row_heights__"] = self._row_heights
        if self._col_widths is not None:
            meta["__col_widths__"] = self._col_widths
        if self._gap is not None:
            meta["__gap__"] = self._gap
        if self._cell_padding is not None:
            meta["__cell_padding__"] = self._cell_padding
        if self._max_width is not None:
            meta["__max_width__"] = self._max_width
        if self._figsize is not None:
            figsize_px = figsize_to_pixels(self._figsize)
            if figsize_px:
                meta["__figsize__"] = figsize_px
        
        # Combinar mapping con metadata
        # Filtrar solo las letras que están en el layout actual
        valid_letters = self._layout_letters()
        active_map = copy.deepcopy(getattr(self, '_map', {}))
        
        # Filtrar mapping para incluir solo letras del layout actual y metadatos
        filtered_map = {
            k: v for k, v in active_map.items()
            if k.startswith('__') or k in valid_letters
        }
        
        # Debug logging para verificar specs - SIEMPRE para gráficos problemáticos
        for letter in valid_letters:
            if letter in filtered_map:
                spec = filtered_map[letter]
                if spec.get('type') in ['funnel', 'polar', 'hist2d', 'ribbon', 'ridgeline']:
                    print(f"🔍 [MatrixLayout] Spec generado para '{letter}': type={spec.get('type')}, keys={list(spec.keys())}")
        
        # Debug logging para verificar specs
        if self._debug:
            print(f"🔍 [MatrixLayout._prepare_repr_data] Debug de specs:")
            print(f"   - Letras válidas en layout: {valid_letters}")
            print(f"   - Letras en _map: {[k for k in active_map.keys() if not k.startswith('__')]}")
            for letter in valid_letters:
                if letter in filtered_map:
                    spec = filtered_map[letter]
                    spec_type = spec.get('type', 'unknown')
                    has_data = 'data' in spec
                    has_series = 'series' in spec
                    data_info = ''
                    if has_data:
                        data = spec.get('data', [])
                        if isinstance(data, list):
                            data_info = f", data_len={len(data)}"
                            if len(data) > 0:
                                sample = data[0] if isinstance(data[0], dict) else data[0]
                                data_info += f", sample_keys={list(sample.keys()) if isinstance(sample, dict) else type(sample)}"
                        else:
                            data_info = f", data_type={type(data).__name__}"
                    if has_series:
                        series = spec.get('series', {})
                        if isinstance(series, dict):
                            data_info += f", series_keys={list(series.keys())[:3]}"
                            if series:
                                first_key = list(series.keys())[0]
                                first_val = series[first_key]
                                if isinstance(first_val, list):
                                    data_info += f", first_series_len={len(first_val)}"
                    print(f"   - '{letter}': type={spec_type}, has_data={has_data}, has_series={has_series}{data_info}")
                else:
                    print(f"   - '{letter}': NO SPEC ENCONTRADO")
        
        self._validate_mapping_letters(filtered_map)
        mapping_merged = {**filtered_map, **meta}
        if self._merge_opt is not None:
            mapping_merged["__merge__"] = self._merge_opt
        
        # Generar estilo inline
        inline_style = ""
        if self._max_width is not None:
            inline_style = f' style="max-width: {self._max_width}px; margin: 0 auto; box-sizing: border-box;"'
        
        return {
            'js_code': js_code,
            'css_code': css_code,
            'escaped_layout': escaped_layout,
            'meta': meta,
            'mapping_merged': mapping_merged,
            'inline_style': inline_style
        }
    
    def _repr_html_(self):
        """Representación HTML del layout (compatible con Jupyter Notebook clásico)"""
        data = self._prepare_repr_data()
        
        # Determinar tema a usar (instancia específica o global)
        theme = getattr(self, '_instance_theme', None) or self._current_theme
        theme_class = f"bestlib-theme-{theme}" if theme != 'light' else ""
        
        # Generar JavaScript usando JSBuilder
        render_js = JSBuilder.build_render_call(
            self.div_id,
            data['escaped_layout'],
            data['mapping_merged']
        ).strip()
        
        # Generar HTML usando HTMLGenerator
        html = HTMLGenerator.generate_full_html(
            self.div_id,
            data['css_code'],
            render_js,
            data['inline_style'],
            theme_class
        )
        
        return html
    
    def _repr_mimebundle_(self, include=None, exclude=None):
        """Representación MIME bundle del layout (compatible con JupyterLab)"""
        import sys
        
        # Determinar tema a usar (instancia específica o global)
        theme = getattr(self, '_instance_theme', None) or self._current_theme
        theme_class = f"bestlib-theme-{theme}" if theme != 'light' else ""
        
        # Detectar si estamos en Colab
        is_colab = "google.colab" in sys.modules
        
        # Cargar assets automáticamente en Colab
        from ..render.assets import AssetManager
        if is_colab:
            AssetManager.ensure_colab_assets_loaded()
        
        # Asegurar que el comm target está registrado
        CommManager.register_comm()
        
        data = self._prepare_repr_data()
        
        # Generar HTML
        html = HTMLGenerator.generate_full_html(
            self.div_id,
            data['css_code'],
            "",  # JS va en bundle separado
            data['inline_style'],
            theme_class
        )
        
        # Generar JavaScript completo usando JSBuilder
        # En Colab, esperar a que D3 esté disponible antes de renderizar
        js = JSBuilder.build_full_js(
            data['js_code'],
            self.div_id,
            data['escaped_layout'],
            data['mapping_merged'],
            wait_for_d3=is_colab  # Esperar D3 solo en Colab
        )
        
        return {
            "text/html": html,
            "application/javascript": js,
        }
    
    def display(self, ascii_layout=None):
        """Muestra el layout usando IPython.display"""
        try:
            from IPython.display import display as ipython_display, HTML, Javascript
            import sys
            
            # Detectar si estamos en Colab
            is_colab = "google.colab" in sys.modules
            
            # Cargar assets automáticamente en Colab
            from ..render.assets import AssetManager
            if is_colab:
                AssetManager.ensure_colab_assets_loaded()
            
            CommManager.register_comm()
            
            data = self._prepare_repr_data(ascii_layout)
            
            # Determinar tema a usar (instancia específica o global)
            theme = getattr(self, '_instance_theme', None) or self._current_theme
            theme_class = f"bestlib-theme-{theme}" if theme != 'light' else ""
            
            # Generar HTML completo (incluye wrapper seguro de D3.js)
            html_content = HTMLGenerator.generate_full_html(
                self.div_id,
                data['css_code'],
                "",  # JS va separado
                data['inline_style'],
                theme_class
            )
            # Generar JavaScript usando JSBuilder
            # En Colab, esperar a que D3 esté disponible antes de renderizar
            js_content = JSBuilder.build_full_js(
                data['js_code'],
                self.div_id,
                data['escaped_layout'],
                data['mapping_merged'],
                wait_for_d3=is_colab  # Esperar D3 solo en Colab
            )
            ipython_display(HTML(html_content))
            ipython_display(Javascript(js_content))
            
            # En Colab, forzar que no se muestre el objeto retornando explícitamente None
            # y suprimiendo cualquier output posterior
            if is_colab:
                from IPython.display import clear_output
                # NO hacer clear_output() porque borraría el gráfico
                # En su lugar, simplemente asegurarse de que None sea lo último
                pass
            
            return None
            
        except Exception as e:
            import traceback
            print(f"❌ Error en display(): {e}")
            traceback.print_exc()
            return None
    
    def merge(self, letters=True):
        """Configura merge explícito para este layout"""
        self._merge_opt = letters
        return self
    
    def merge_all(self):
        """Activa merge para todas las letras"""
        self._merge_opt = True
        return self
    
    def merge_off(self):
        """Desactiva merge"""
        self._merge_opt = False
        return self
    
    def merge_only(self, letters):
        """Activa merge solo para las letras indicadas"""
        self._merge_opt = list(letters) if letters is not None else []
        return self

