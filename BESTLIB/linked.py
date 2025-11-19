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
    from IPython.display import display, HTML, Javascript
    HAS_IPYTHON = True
except ImportError:
    HAS_IPYTHON = False
    Javascript = None

try:
    import ipywidgets as widgets
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False
    widgets = None


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
        self._div_ids = {}  # {view_id: div_id} - Guardar div_id de cada layout
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
        # Guardar div_id para actualizaciones futuras
        self._div_ids[view_id] = layout.div_id
        
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
        # Guardar div_id para actualizaciones futuras
        self._div_ids[view_id] = layout.div_id
        
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
                
                # Re-mapear (actualizar el spec interno)
                self._layouts[view_id].map({'B': bar_spec})
                
                # Actualizar el gráfico directamente con JavaScript sin recrear el contenedor
                div_id = self._div_ids.get(view_id)
                if div_id:
                    self._update_chart_with_js(div_id, bar_spec)
        
        # Actualizar widget de selección si existe
        self._update_selection_widget_display()
    
    def _update_chart_with_js(self, div_id, bar_spec):
        """Actualiza un gráfico existente usando JavaScript sin recrear el contenedor"""
        import json
        
        # Escapar datos para JavaScript
        bar_data_json = json.dumps(bar_spec['data'])
        color_map_json = json.dumps(bar_spec.get('colorMap', {}))
        
        # JavaScript para actualizar el gráfico directamente
        js_update = f"""
        (function() {{
            const divId = '{div_id}';
            const container = document.getElementById(divId);
            if (!container) {{
                console.warn('Contenedor no encontrado:', divId);
                return;
            }}
            
            // Buscar el SVG dentro del contenedor
            const svg = container.querySelector('svg');
            if (!svg) {{
                console.warn('SVG no encontrado en contenedor:', divId);
                return;
            }}
            
            // Obtener datos
            const barData = {bar_data_json};
            const colorMap = {color_map_json};
            
            // Obtener dimensiones del SVG existente
            const width = parseFloat(svg.getAttribute('width')) || 600;
            const height = parseFloat(svg.getAttribute('height')) || 400;
            
            // Calcular márgenes y área del gráfico
            const margin = {{ top: 20, right: 20, bottom: 60, left: 60 }};
            const chartWidth = width - margin.left - margin.right;
            const chartHeight = height - margin.top - margin.bottom;
            
            // Usar D3 si está disponible
            if (typeof d3 !== 'undefined') {{
                const d3Svg = d3.select(svg);
                
                // Buscar el grupo principal del gráfico (el primer 'g' dentro del SVG, que es el grupo de transformación)
                // En matrix.js, se crea como: svg.append('g').attr('transform', `translate(${{margin.left}},${{margin.top}})`);
                let chartG = svg.querySelector('g');
                if (!chartG) {{
                    console.warn('No se encontró el grupo del gráfico');
                    return;
                }}
                
                const d3G = d3.select(chartG);
                
                // Limpiar solo las barras y etiquetas (mantener ejes y otros elementos)
                // En matrix.js, las barras son rect sin clase específica, pero están dentro del grupo principal
                // Los ejes tienen clases específicas (.axis, .domain, .tick)
                // Eliminar todos los rect que no sean parte de los ejes
                d3G.selectAll('rect').each(function() {{
                    const rect = d3.select(this);
                    const classes = this.getAttribute('class') || '';
                    // Solo eliminar si no es parte de los ejes
                    if (!classes.includes('axis') && !classes.includes('domain') && !classes.includes('tick')) {{
                        rect.remove();
                    }}
                }});
                
                // Eliminar etiquetas de barras si existen
                d3G.selectAll('text').each(function() {{
                    const text = d3.select(this);
                    const classes = this.getAttribute('class') || '';
                    // Solo eliminar si es etiqueta de barra, no etiquetas de ejes
                    if (classes.includes('bar-label') || (!classes.includes('axis') && !classes.includes('tick') && !classes.includes('domain'))) {{
                        // Verificar que no sea parte de los ejes por posición
                        const y = parseFloat(this.getAttribute('y')) || 0;
                        if (y < chartHeight + 20) {{ // Etiquetas de barras están arriba
                            text.remove();
                        }}
                    }}
                }});
                
                // Recalcular escalas con nuevos datos
                const xScale = d3.scaleBand()
                    .domain(barData.map(d => d.category))
                    .range([0, chartWidth])
                    .padding(0.2);
                
                const maxValue = d3.max(barData, d => d.value) || 1;
                const yScale = d3.scaleLinear()
                    .domain([0, maxValue * 1.1])
                    .nice()
                    .range([chartHeight, 0]);
                
                // Dibujar nuevas barras usando el patrón enter/update/exit de D3
                // En matrix.js, las barras tienen la clase 'bar'
                const bars = d3G.selectAll('rect.bar')
                    .data(barData, d => d.category);
                
                // Eliminar barras antiguas que ya no están en los datos
                bars.exit().remove();
                
                // Agregar nuevas barras
                const barsEnter = bars.enter()
                    .append('rect')
                    .attr('class', 'bar')
                    .attr('x', d => xScale(d.category))
                    .attr('width', xScale.bandwidth())
                    .attr('y', chartHeight)
                    .attr('height', 0)
                    .attr('fill', d => d.color || colorMap[d.category] || '#9b59b6')
                    .attr('stroke', '#fff')
                    .attr('stroke-width', 1);
                
                // Actualizar barras existentes y animar
                bars.merge(barsEnter)
                    .transition()
                    .duration(300)
                    .attr('x', d => xScale(d.category))
                    .attr('width', xScale.bandwidth())
                    .attr('y', d => yScale(d.value))
                    .attr('height', d => chartHeight - yScale(d.value))
                    .attr('fill', d => d.color || colorMap[d.category] || '#9b59b6');
                
                // Actualizar etiquetas
                const labels = d3G.selectAll('text.bar-label')
                    .data(barData);
                
                labels.exit().remove();
                
                labels.enter()
                    .append('text')
                    .attr('class', 'bar-label')
                    .merge(labels)
                    .attr('x', d => xScale(d.category) + xScale.bandwidth() / 2)
                    .attr('y', d => yScale(d.value) - 5)
                    .attr('text-anchor', 'middle')
                    .attr('font-size', '11px')
                    .attr('fill', '#333')
                    .text(d => d.value);
                
                // Actualizar ejes si existen
                const xAxisG = d3G.select('.x-axis');
                const yAxisG = d3G.select('.y-axis');
                
                if (!xAxisG.empty()) {{
                    const xAxis = d3.axisBottom(xScale);
                    xAxisG.call(xAxis);
                }}
                
                if (!yAxisG.empty()) {{
                    const yAxis = d3.axisLeft(yScale);
                    yAxisG.call(yAxis);
                }}
            }} else {{
                console.warn('D3 no está disponible para actualizar el gráfico');
            }}
        }})();
        """
        
        display(Javascript(js_update))
    
    def display(self):
        """Muestra todas las vistas enlazadas en el notebook"""
        if not HAS_IPYTHON:
            return
        
        # Crear contenedor HTML para todas las vistas con tamaños fijos
        html_parts = [f'<div id="{self._container_id}" style="display: flex; flex-wrap: wrap; gap: 20px; width: 100%;">']
        
        for view_id in self._views.keys():
            container_id = f"{self._container_id}-{view_id}"
            html_parts.append(
                f'<div id="{container_id}" style="flex: 1; min-width: 400px; max-width: 600px; width: 500px; height: 400px; overflow: hidden;"></div>'
            )
        
        html_parts.append('</div>')
        
        display(HTML(''.join(html_parts)))
        
        # Crear y mostrar cada vista
        for view_id, view_config in self._views.items():
            if view_config['type'] == 'scatter':
                layout = self._create_scatter_layout(view_id, view_config)
                self._div_ids[view_id] = layout.div_id
                layout.display()
            elif view_config['type'] == 'barchart':
                layout = self._create_barchart_layout(view_id, view_config)
                self._div_ids[view_id] = layout.div_id
                layout.display()
    
    
    def get_selected_data(self):
        """Retorna los datos seleccionados actualmente"""
        return [item.get('_original', item) for item in self._selected_data]
    
    def get_selected_count(self):
        """Retorna el número de elementos seleccionados"""
        return len(self._selected_data)
    
    @property
    def selection_widget(self):
        """
        Retorna el widget de selección para mostrar en Jupyter.
        Similar a ReactiveMatrixLayout.selection_widget
        
        Uso:
            display(linked.selection_widget)
        """
        if not HAS_WIDGETS:
            print("⚠️ ipywidgets no está instalado. Instala con: pip install ipywidgets")
            return None
        
        if not hasattr(self, '_selection_widget') or self._selection_widget is None:
            # Crear widget visual
            self._selection_widget = widgets.VBox([
                widgets.HTML('<h4>📊 Datos Seleccionados</h4>'),
                widgets.Label(value='Esperando selección...'),
                widgets.IntText(value=0, description='Cantidad:', disabled=True)
            ])
            
            # Función para actualizar el widget
            def update_widget():
                count = len(self._selected_data)
                label = self._selection_widget.children[1]
                counter = self._selection_widget.children[2]
                
                if count > 0:
                    label.value = f'✅ {count} elementos seleccionados'
                    counter.value = count
                else:
                    label.value = 'Esperando selección...'
                    counter.value = 0
            
            # Guardar función de actualización para llamarla desde _update_linked_views
            self._update_selection_widget = update_widget
            
            # Actualizar inicialmente
            update_widget()
        
        return self._selection_widget
    
    def _update_selection_widget_display(self):
        """Actualiza el widget de selección si existe"""
        if hasattr(self, '_update_selection_widget'):
            try:
                self._update_selection_widget()
            except Exception as e:
                # Silenciar errores si el widget no está disponible
                pass
