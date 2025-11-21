"""
MatrixLayout - Refactorizado para usar módulos modulares
"""
import uuid
import weakref
from ..core.events import EventManager
from ..core.comm import CommManager
from ..core.layout import LayoutEngine
from ..render.html import HTMLGenerator
from ..render.builder import JSBuilder
from ..render.assets import AssetManager
from ..utils.figsize import figsize_to_pixels, process_figsize_in_kwargs
from ..core.exceptions import LayoutError

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
    _map = {}
    _safe_html = True
    
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
    
    @classmethod
    def map(cls, mapping):
        """Mapea gráficos a letras del layout"""
        cls._map = mapping
    
    # Métodos map_* delegados al sistema de gráficos
    @classmethod
    def map_scatter(cls, letter, data, **kwargs):
        """Método helper para crear scatter plot"""
        from ..charts import ChartRegistry
        
        chart = ChartRegistry.get('scatter')
        spec = chart.get_spec(data, **kwargs)
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_barchart(cls, letter, data, **kwargs):
        """Método helper para crear bar chart"""
        from ..charts import ChartRegistry
        
        chart = ChartRegistry.get('bar')
        spec = chart.get_spec(data, **kwargs)
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_line_plot(cls, letter, data, **kwargs):
        """Método helper para crear line plot completo"""
        from ..charts import ChartRegistry
        
        chart = ChartRegistry.get('line_plot')
        spec = chart.get_spec(data, **kwargs)
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_horizontal_bar(cls, letter, data, **kwargs):
        """Método helper para crear horizontal bar chart"""
        from ..charts import ChartRegistry
        
        chart = ChartRegistry.get('horizontal_bar')
        spec = chart.get_spec(data, **kwargs)
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_hexbin(cls, letter, data, **kwargs):
        """Método helper para crear hexbin chart"""
        from ..charts import ChartRegistry
        
        chart = ChartRegistry.get('hexbin')
        spec = chart.get_spec(data, **kwargs)
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_errorbars(cls, letter, data, **kwargs):
        """Método helper para crear errorbars chart"""
        from ..charts import ChartRegistry
        
        chart = ChartRegistry.get('errorbars')
        spec = chart.get_spec(data, **kwargs)
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_fill_between(cls, letter, data, **kwargs):
        """Método helper para crear fill_between chart"""
        from ..charts import ChartRegistry
        
        chart = ChartRegistry.get('fill_between')
        spec = chart.get_spec(data, **kwargs)
        
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_kde(cls, letter, data, **kwargs):
        """Método helper para crear KDE"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('kde')
        spec = chart.get_spec(data, **kwargs)
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_distplot(cls, letter, data, **kwargs):
        """Método helper para crear distplot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('distplot')
        spec = chart.get_spec(data, **kwargs)
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_rug(cls, letter, data, **kwargs):
        """Método helper para crear rug plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('rug')
        spec = chart.get_spec(data, **kwargs)
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_qqplot(cls, letter, data, **kwargs):
        """Método helper para crear Q-Q plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('qqplot')
        spec = chart.get_spec(data, **kwargs)
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_ecdf(cls, letter, data, **kwargs):
        """Método helper para crear ECDF"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('ecdf')
        spec = chart.get_spec(data, **kwargs)
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_ridgeline(cls, letter, data, **kwargs):
        """Método helper para crear ridgeline plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('ridgeline')
        spec = chart.get_spec(data, **kwargs)
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_ribbon(cls, letter, data, **kwargs):
        """Método helper para crear ribbon plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('ribbon')
        spec = chart.get_spec(data, **kwargs)
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_hist2d(cls, letter, data, **kwargs):
        """Método helper para crear 2D histogram"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('hist2d')
        spec = chart.get_spec(data, **kwargs)
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_polar(cls, letter, data, **kwargs):
        """Método helper para crear polar plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('polar')
        spec = chart.get_spec(data, **kwargs)
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_funnel(cls, letter, data, **kwargs):
        """Método helper para crear funnel plot"""
        from ..charts import ChartRegistry
        chart = ChartRegistry.get('funnel')
        spec = chart.get_spec(data, **kwargs)
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
    @classmethod
    def map_grouped_barchart(cls, letter, data, main_col=None, sub_col=None, value_col=None, **kwargs):
        """Método helper para crear grouped bar chart"""
        try:
            from ..charts import ChartRegistry
            chart = ChartRegistry.get('grouped_barchart')
            spec = chart.get_spec(data, main_col=main_col, sub_col=sub_col, value_col=value_col, **kwargs)
        except Exception:
            # Fallback: delegar a versión legacy
            try:
                from ...matrix import MatrixLayout as LegacyMatrixLayout
                return LegacyMatrixLayout.map_grouped_barchart(letter, data, main_col=main_col, sub_col=sub_col, value_col=value_col, **kwargs)
            except Exception:
                spec = {'type': 'grouped_barchart', 'data': [], **kwargs}
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    
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
        mapping_merged = {**self._map, **meta}
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
            data['inline_style']
        )
        
        return html
    
    def _repr_mimebundle_(self, include=None, exclude=None):
        """Representación MIME bundle del layout (compatible con JupyterLab)"""
        import sys
        
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
            data['inline_style']
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
            from IPython.display import display, HTML, Javascript
            import sys
            
            # Detectar si estamos en Colab
            is_colab = "google.colab" in sys.modules
            
            # Cargar assets automáticamente en Colab
            from ..render.assets import AssetManager
            if is_colab:
                AssetManager.ensure_colab_assets_loaded()
            
            CommManager.register_comm()
            
            data = self._prepare_repr_data(ascii_layout)
            
            # Generar HTML completo (incluye wrapper seguro de D3.js)
            html_content = HTMLGenerator.generate_full_html(
                self.div_id,
                data['css_code'],
                "",  # JS va separado
                data['inline_style']
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
            
            display(HTML(html_content))
            display(Javascript(js_content))
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
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

