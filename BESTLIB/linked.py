"""
Sistema de Vistas Enlazadas (Linked Views) para BESTLIB
Permite que múltiples visualizaciones se actualicen automáticamente

NOTA: Este módulo está siendo reemplazado por ReactiveMatrixLayout que integra
LinkedViews dentro de la matriz ASCII. Se mantiene por compatibilidad.
"""

from .matrix import MatrixLayout
from collections import Counter

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

try:
    from IPython.display import display, HTML
    HAS_IPYTHON = True
except ImportError:
    HAS_IPYTHON = False


class LinkedViews:
    """
    Gestor de vistas enlazadas que permite que múltiples gráficos
    se actualicen automáticamente cuando se seleccionan datos.
    
    Ejemplo:
        from BESTLIB.linked import LinkedViews
        
        # Crear gestor de vistas enlazadas
        linked = LinkedViews()
        
        # Agregar scatter plot (vista principal con brush)
        linked.add_scatter('scatter1', data, interactive=True)
        
        # Agregar bar chart (se actualiza automáticamente)
        linked.add_barchart('bar1', category_field='category')
        
        # Mostrar todas las vistas
        linked.display()
        
        # Cuando seleccionas en scatter, el barchart se actualiza solo
    """
    
    def __init__(self):
        self._views = {}  # {view_id: view_config}
        self._data = []  # Datos originales
        self._selected_data = []  # Datos seleccionados
        self._layouts = {}  # {view_id: MatrixLayout instance}
        self._container_id = f"linked-views-{id(self)}"
        
    def set_data(self, data):
        """
        Establece los datos originales para todas las vistas.
        
        Args:
            data: Lista de diccionarios con los datos
        """
        self._data = data
        return self
    
    def add_scatter(self, view_id, data=None, x_field='x', y_field='y', 
                   category_field='category', interactive=True, 
                   x_col=None, y_col=None, category_col=None, **kwargs):
        """
        Agrega un scatter plot a las vistas enlazadas.
        
        Args:
            view_id: Identificador único para esta vista
            data: DataFrame de pandas o lista de diccionarios (opcional si ya se estableció con set_data)
            x_field: Campo para el eje X (deprecated, usar x_col)
            y_field: Campo para el eje Y (deprecated, usar y_col)
            category_field: Campo de categoría (deprecated, usar category_col)
            interactive: Si True, habilita brush selection
            x_col: Nombre de columna para eje X (nuevo, preferido con DataFrames)
            y_col: Nombre de columna para eje Y (nuevo, preferido con DataFrames)
            category_col: Nombre de columna para categorías (nuevo, preferido con DataFrames)
            **kwargs: Argumentos adicionales (colorMap, pointRadius, etc.)
        """
        if data:
            self._data = data
        
        # Usar nuevos parámetros si están disponibles, sino usar los antiguos
        x_field = x_col or x_field
        y_field = y_col or y_field
        category_field = category_col or category_field
        
        self._views[view_id] = {
            'type': 'scatter',
            'x_field': x_field,
            'y_field': y_field,
            'category_field': category_field,
            'interactive': interactive,
            'kwargs': kwargs
        }
        return self
    
    def add_barchart(self, view_id, category_field='category', 
                    value_field=None, aggregation='count',
                    category_col=None, value_col=None, **kwargs):
        """
        Agrega un bar chart que se actualiza automáticamente.
        
        Args:
            view_id: Identificador único para esta vista
            category_field: Campo de categoría (deprecated, usar category_col)
            value_field: Campo numérico (deprecated, usar value_col)
            aggregation: 'count', 'sum', 'mean' (solo si value_field está definido)
            category_col: Nombre de columna para categorías (nuevo, preferido con DataFrames)
            value_col: Nombre de columna para valores (nuevo, preferido con DataFrames)
            **kwargs: Argumentos adicionales
                - colorMap: Diccionario {categoria: color} para colorear barras
                - color: Color único para todas las barras (ignorado si colorMap está presente)
                - axes: Mostrar ejes (default: True)
        """
        # Usar nuevos parámetros si están disponibles
        category_field = category_col or category_field
        value_field = value_col or value_field
        
        self._views[view_id] = {
            'type': 'barchart',
            'category_field': category_field,
            'value_field': value_field,
            'aggregation': aggregation,
            'kwargs': kwargs
        }
        return self
    
    def _prepare_scatter_data(self, view_config, data):
        """Prepara datos para scatter plot, soportando DataFrames"""
        x_field = view_config['x_field']
        y_field = view_config['y_field']
        cat_field = view_config['category_field']
        
        # Si es DataFrame, usar el método helper de MatrixLayout
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            processed_data, original_data = MatrixLayout._prepare_data(
                data, 
                x_col=x_field, 
                y_col=y_field, 
                category_col=cat_field
            )
            return processed_data
        else:
            # Lista de diccionarios (comportamiento original)
            scatter_data = []
            for item in data:
                scatter_data.append({
                    'x': item.get(x_field, 0),
                    'y': item.get(y_field, 0),
                    'category': item.get(cat_field, 'default'),
                    '_original': item  # Guardar datos originales
                })
            return scatter_data
    
    def _prepare_barchart_data(self, view_config, data):
        """Prepara datos para bar chart, soportando DataFrames"""
        cat_field = view_config['category_field']
        value_field = view_config.get('value_field')
        
        # Si es DataFrame, procesar directamente
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if value_field and value_field in data.columns:
                # Agrupar y sumar
                bar_data = data.groupby(cat_field)[value_field].sum().reset_index()
                bar_data = bar_data.rename(columns={cat_field: 'category', value_field: 'value'})
                bar_data = bar_data.to_dict('records')
            elif cat_field and cat_field in data.columns:
                # Contar por categoría
                counts = data[cat_field].value_counts()
                bar_data = [{'category': cat, 'value': count} for cat, count in counts.items()]
            else:
                raise ValueError(f"Debe especificar category_col. Columnas disponibles: {list(data.columns)}")
            
            # Obtener colorMap si existe
            color_map = view_config.get('kwargs', {}).get('colorMap', {})
            for bar_item in bar_data:
                bar_item['color'] = color_map.get(bar_item['category'], '#9b59b6')
            
            return bar_data
        else:
            # Lista de diccionarios (comportamiento original)
            if value_field:
                # Agrupar y sumar
                from collections import defaultdict
                sums = defaultdict(float)
                for item in data:
                    cat = item.get(cat_field, 'unknown')
                    val = item.get(value_field, 0)
                    sums[cat] += val
                categories = dict(sums)
            else:
                # Contar por categoría
                categories = Counter([item.get(cat_field, 'unknown') for item in data])
            
            # Obtener colorMap si existe
            color_map = view_config.get('kwargs', {}).get('colorMap', {})
            
            bar_data = [
                {
                    'category': cat, 
                    'value': count,
                    'color': color_map.get(cat, '#9b59b6')  # Color por defecto si no está en el mapa
                }
                for cat, count in categories.items()
            ]
            
            return bar_data
    
    def _create_scatter_layout(self, view_id, view_config):
        """Crea layout para scatter plot"""
        scatter_data = self._prepare_scatter_data(view_config, self._data)
        
        layout = MatrixLayout("S")
        
        # Callback para actualizar selección
        def on_select(payload):
            self._selected_data = payload.get('items', [])
            # Actualizar todas las vistas dependientes
            self._update_linked_views()
        
        layout.on('select', on_select)
        
        # Configurar scatter
        scatter_spec = {
            'type': 'scatter',
            'data': scatter_data,
            'axes': True,
            'interactive': view_config['interactive'],
            **view_config['kwargs']
        }
        
        layout.map({'S': scatter_spec})
        self._layouts[view_id] = layout
        
        return layout
    
    def _create_barchart_layout(self, view_id, view_config, data_source='original'):
        """Crea layout para bar chart"""
        # Usar datos seleccionados o originales
        data = self._selected_data if data_source == 'selected' and self._selected_data else self._data
        
        bar_data = self._prepare_barchart_data(view_config, data)
        
        layout = MatrixLayout("B")
        
        bar_spec = {
            'type': 'bar',
            'data': bar_data,
            'axes': True,
            'interactive': False,
            **view_config['kwargs']
        }
        
        layout.map({'B': bar_spec})
        self._layouts[view_id] = layout
        
        return layout
    
    def _update_linked_views(self):
        """Actualiza todas las vistas enlazadas cuando cambia la selección"""
        if not HAS_IPYTHON:
            return
        
        # Actualizar solo los bar charts con datos seleccionados
        for view_id, view_config in self._views.items():
            if view_config['type'] == 'barchart' and view_id in self._layouts:
                # Usar datos seleccionados si existen, sino usar originales
                data = self._selected_data if self._selected_data else self._data
                
                # Extraer los datos originales
                original_data = [item.get('_original', item) for item in data]
                
                # Preparar nuevos datos del barchart
                bar_data = self._prepare_barchart_data(view_config, original_data)
                
                # Actualizar el spec del layout existente
                bar_spec = {
                    'type': 'bar',
                    'data': bar_data,
                    'axes': True,
                    'interactive': False,
                    **view_config['kwargs']
                }
                
                # Re-mapear y re-renderizar
                self._layouts[view_id].map({'B': bar_spec})
                
                # Limpiar y re-renderizar el contenedor
                container_id = f"{self._container_id}-{view_id}"
                self._clear_and_redisplay(view_id, container_id)
    
    def _clear_and_redisplay(self, view_id, container_id):
        """Limpia y re-renderiza una vista específica"""
        layout = self._layouts.get(view_id)
        if not layout:
            return
        
        # JavaScript para limpiar el contenedor
        js_clear = f"""
        <script>
        (function() {{
            const container = document.getElementById('{container_id}');
            if (container) {{
                container.innerHTML = '';
            }}
        }})();
        </script>
        """
        
        # Mostrar el script de limpieza y luego el nuevo gráfico
        display(HTML(js_clear))
        layout.display()
    
    def display(self):
        """Muestra todas las vistas enlazadas en el notebook"""
        if not HAS_IPYTHON:
            return
        
        # Crear contenedor HTML para todas las vistas
        html_parts = [f'<div id="{self._container_id}" style="display: flex; flex-wrap: wrap; gap: 20px;">']
        
        for view_id in self._views.keys():
            container_id = f"{self._container_id}-{view_id}"
            html_parts.append(
                f'<div id="{container_id}" style="flex: 1; min-width: 400px; max-width: 600px;"></div>'
            )
        
        html_parts.append('</div>')
        
        display(HTML(''.join(html_parts)))
        
        # Crear y mostrar cada vista
        for view_id, view_config in self._views.items():
            if view_config['type'] == 'scatter':
                self._create_scatter_layout(view_id, view_config).display()
            elif view_config['type'] == 'barchart':
                self._create_barchart_layout(view_id, view_config).display()
    
    
    def get_selected_data(self):
        """Retorna los datos seleccionados actualmente"""
        return [item.get('_original', item) for item in self._selected_data]
    
    def get_selected_count(self):
        """Retorna el número de elementos seleccionados"""
        return len(self._selected_data)
