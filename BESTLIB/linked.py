"""
Sistema de Vistas Enlazadas legacy (Linked Views).

⚠️ Deprecated: Usa BESTLIB.layouts.reactive.ReactiveMatrixLayout.
"""
from warnings import warn
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
        warn(
            "LinkedViews está deprecado y será eliminado en versiones futuras. "
            "Migra a ReactiveMatrixLayout.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._views = {}  # {view_id: view_config}
        self._data = []  # Datos originales
        self._selected_data = []  # Datos seleccionados
        self._layouts = {}  # {view_id: MatrixLayout instance}
        self._div_ids = {}  # {view_id: div_id} - Guardar div_id de cada layout
        self._container_id = f"linked-views-{id(self)}"
        self._updating_charts = set()  # {div_id} - Flags para evitar actualizaciones simultáneas
        
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
            # Debug: verificar que el callback se está ejecutando
            if MatrixLayout._debug:
                print(f"🔵 [LinkedViews] Callback select ejecutado")
                print(f"   - Payload keys: {list(payload.keys())}")
                print(f"   - Layout div_id: {layout.div_id}")
            
            # Extraer items del payload
            items = payload.get('items', [])
            
            # CRÍTICO: Verificar que items sea una lista válida
            if not items:
                # Si no hay items, limpiar selección
                self._selected_data = []
                if MatrixLayout._debug:
                    print(f"   ⚠️ No hay items en el payload, limpiando selección")
            else:
                # Asegurar que items sea una lista
                if not isinstance(items, list):
                    items = [items]
                
                # CRÍTICO: Verificar que los items tengan la estructura correcta
                # Los items pueden venir directamente del scatter plot o pueden tener _original_row
                self._selected_data = items
                
                if MatrixLayout._debug:
                    print(f"   ✅ {len(items)} items recibidos")
                    if len(items) > 0:
                        print(f"   - Primer item keys: {list(items[0].keys()) if isinstance(items[0], dict) else 'No es dict'}")
                        print(f"   - Primer item: {items[0]}")
            
            # Actualizar todas las vistas dependientes
            self._update_linked_views()
        
        layout.on('select', on_select)
        
        # CRÍTICO: Asegurar que el comm esté registrado antes de mostrar
        # Esto es necesario para que los eventos funcionen correctamente
        MatrixLayout.register_comm()
        
        # CRÍTICO: Registrar la instancia del layout para que el sistema de comm pueda encontrarla
        # Esto asegura que los eventos lleguen al callback correcto
        if hasattr(layout, 'div_id') and layout.div_id:
            if MatrixLayout._debug:
                print(f"✅ [LinkedViews] Layout registrado con div_id: {layout.div_id}")
        
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
        
        # Obtener la letra de la vista (por defecto 'B' para barchart)
        letter = view_config.get('letter', 'B')
        
        layout = MatrixLayout(letter)
        
        bar_spec = {
            'type': 'bar',
            'data': bar_data,
            'axes': True,
            'interactive': False,
            **view_config['kwargs']
        }
        
        layout.map({letter: bar_spec})
        self._layouts[view_id] = layout
        # Guardar div_id y letra para actualizaciones futuras
        self._div_ids[view_id] = layout.div_id
        # Guardar la letra en view_config para uso en _update_chart_with_js
        view_config['letter'] = letter
        
        return layout
    
    def _update_linked_views(self):
        """Actualiza todas las vistas enlazadas cuando cambia la selección"""
        if not HAS_IPYTHON:
            return
        
        # Debug: verificar que se está actualizando
        if MatrixLayout._debug:
            print(f"🔄 [LinkedViews] Actualizando vistas enlazadas con {len(self._selected_data) if self._selected_data else 0} items seleccionados")
        
        # Actualizar solo los bar charts con datos seleccionados
        for view_id, view_config in self._views.items():
            if view_config['type'] == 'barchart' and view_id in self._layouts:
                # Usar datos seleccionados si existen, sino usar originales
                data = self._selected_data if self._selected_data else self._data
                
                # CRÍTICO: Si no hay datos seleccionados, usar todos los datos originales
                if not data or len(data) == 0:
                    data = self._data
                    if MatrixLayout._debug:
                        print(f"   ⚠️ No hay datos seleccionados, usando todos los datos originales ({len(self._data)} items)")
                else:
                    if MatrixLayout._debug:
                        print(f"   ✅ Usando {len(data)} items seleccionados")
                
                # Extraer los datos originales
                # CRÍTICO: Los items pueden venir con _original_row (usado por matrix.js) o _original (usado por _prepare_scatter_data),
                # o pueden ser los datos originales directamente (con x, y, category)
                original_data = []
                for item in data:
                    if isinstance(item, dict):
                        # Intentar obtener _original_row primero (usado por matrix.js cuando viene del scatter plot)
                        if '_original_row' in item:
                            orig = item['_original_row']
                            original_data.append(orig if orig is not None else item)
                        # Luego intentar _original (usado por _prepare_scatter_data)
                        elif '_original' in item:
                            orig = item['_original']
                            original_data.append(orig if orig is not None else item)
                        # Si no tiene campos especiales, verificar si tiene x, y, category (datos del scatter plot)
                        # Si tiene estos campos, es probable que ya sea el dato original
                        elif 'x' in item and 'y' in item and 'category' in item:
                            # Este es probablemente el dato original del scatter plot
                            original_data.append(item)
                        else:
                            # Usar el item directamente (puede ser que ya sea el dato original)
                            original_data.append(item)
                    else:
                        original_data.append(item)
                
                if MatrixLayout._debug:
                    print(f"   📊 Datos originales extraídos: {len(original_data)} items")
                
                # Preparar nuevos datos del barchart
                bar_data = self._prepare_barchart_data(view_config, original_data)
                
                if MatrixLayout._debug:
                    print(f"   📊 Datos del barchart preparados: {len(bar_data)} categorías")
                    for bar in bar_data:
                        print(f"      - {bar.get('category', 'N/A')}: {bar.get('value', 0)}")
                
                # Actualizar el spec del layout existente
                bar_spec = {
                    'type': 'bar',
                    'data': bar_data,
                    'axes': True,
                    'interactive': False,
                    **view_config['kwargs']
                }
                
                # Actualizar el gráfico directamente con JavaScript sin recrear el contenedor
                # NOTA: NO llamar layout.map() aquí porque puede disparar re-renders automáticos
                # que causan acumulación de barras. Solo actualizamos con JS directamente.
                div_id = self._div_ids.get(view_id)
                if div_id:
                    # Obtener la letra de la vista (por defecto 'B' para barchart)
                    letter = view_config.get('letter', 'B')
                    if MatrixLayout._debug:
                        print(f"   🔄 Actualizando bar chart '{view_id}' (div_id: {div_id}, letter: {letter})")
                    self._update_chart_with_js(div_id, bar_spec, letter=letter)
                else:
                    if MatrixLayout._debug:
                        print(f"   ⚠️ No se encontró div_id para vista '{view_id}'")
        
        # Actualizar widget de selección si existe
        self._update_selection_widget_display()
    
    def _update_chart_with_js(self, div_id, bar_spec, letter='B'):
        """Actualiza un gráfico existente usando JavaScript sin recrear el contenedor"""
        import json
        
        # CRÍTICO: Protección contra race condition - evitar actualizaciones simultáneas
        update_key = f"{div_id}:{letter}"
        if update_key in self._updating_charts:
            # Ya hay una actualización en curso para este div, ignorar esta llamada
            return
        
        # Marcar como actualizando
        self._updating_charts.add(update_key)
        
        # Escapar datos para JavaScript
        bar_data_json = json.dumps(bar_spec['data'])
        color_map_json = json.dumps(bar_spec.get('colorMap', {}))
        
        # JavaScript para actualizar el gráfico directamente
        js_update = f"""
        (function() {{
            const divId = '{div_id}';
            const letter = '{letter}';
            
            // CRÍTICO: Flag de protección a nivel de ventana para evitar ejecuciones simultáneas
            const flagName = '_bestlib_updating_' + divId.replace(/[^a-zA-Z0-9]/g, '_') + '_' + letter;
            if (window[flagName]) {{
                console.warn('Actualización ya en curso para:', divId, letter);
                return;
            }}
            window[flagName] = true;
            
            try {{
                // CRÍTICO: Buscar el contenedor principal del layout
                const mainContainer = document.getElementById(divId);
                if (!mainContainer) {{
                    console.warn('Contenedor principal no encontrado:', divId);
                    window[flagName] = false;
                    return;
                }}
                
                // CRÍTICO: Buscar la celda específica con data-letter dentro del layout
                // El bar chart se renderiza dentro de una celda con clase 'matrix-cell' y data-letter
                const cell = mainContainer.querySelector('.matrix-cell[data-letter="' + letter + '"]');
                if (!cell) {{
                    console.warn('Celda no encontrada para letra:', letter, 'en contenedor:', divId);
                    window[flagName] = false;
                    return;
                }}
                
                // CRÍTICO: Limpiar COMPLETAMENTE la celda antes de actualizar
                // Esto previene la acumulación de SVGs múltiples que causa el crecimiento infinito
                // Eliminar TODOS los SVGs y cualquier otro contenido
                const existingSvgs = cell.querySelectorAll('svg');
                existingSvgs.forEach(svg => svg.remove());
                
                // También limpiar cualquier otro contenido residual
                cell.innerHTML = '';
                
                // Obtener datos
                const barData = {bar_data_json};
                const colorMap = {color_map_json};
                
                // Obtener dimensiones del contenedor (usar dimensiones fijas para evitar expansión)
                // CRÍTICO: Si las dimensiones del contenedor no están disponibles, usar valores por defecto
                let containerWidth = cell.clientWidth || cell.offsetWidth || 500;
                let containerHeight = cell.clientHeight || cell.offsetHeight || 400;
                
                // Si aún no hay dimensiones, esperar un frame y usar valores por defecto seguros
                if (containerWidth === 0 || containerHeight === 0) {{
                    containerWidth = 500;
                    containerHeight = 400;
                }}
                
                const width = Math.min(Math.max(containerWidth, 400), 600);
                const height = Math.min(Math.max(containerHeight, 300), 400);
                
                // Calcular márgenes y área del gráfico (usar los mismos márgenes que matrix.js)
                const margin = {{ top: 20, right: 20, bottom: 60, left: 60 }};
                const chartWidth = width - margin.left - margin.right;
                const chartHeight = height - margin.top - margin.bottom;
                
                // Usar D3 si está disponible para re-renderizar completamente
                if (typeof d3 !== 'undefined') {{
                    // CRÍTICO: Crear SVG completamente nuevo desde cero
                    // Esto evita cualquier problema de acumulación o estado residual
                    const svg = d3.select(cell)
                        .append('svg')
                        .attr('width', width)
                        .attr('height', height)
                        .style('overflow', 'visible');
                    
                    const g = svg.append('g')
                        .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
                    
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
                    
                    // Dibujar barras desde cero
                    // CRÍTICO: Verificar que hay datos antes de dibujar
                    if (barData && barData.length > 0) {{
                        const bars = g.selectAll('.bar')
                            .data(barData)
                            .enter()
                            .append('rect')
                            .attr('class', 'bar')
                            .attr('x', d => xScale(d.category))
                            .attr('width', xScale.bandwidth())
                            .attr('y', chartHeight)
                            .attr('height', 0)
                            .attr('fill', d => d.color || colorMap[d.category] || '#9b59b6')
                            .attr('stroke', '#fff')
                            .attr('stroke-width', 1)
                            .transition()
                            .duration(300)
                            .attr('y', d => yScale(d.value))
                            .attr('height', d => chartHeight - yScale(d.value));
                    }} else {{
                        console.warn('No hay datos para dibujar barras');
                    }}
                    
                    // Dibujar ejes desde cero
                    const xAxis = g.append('g')
                        .attr('transform', `translate(0,${{chartHeight}})`)
                        .call(d3.axisBottom(xScale));
                    
                    xAxis.selectAll('text')
                        .style('font-size', '12px')
                        .style('font-weight', '600')
                        .style('fill', '#000000')
                        .style('font-family', 'Arial, sans-serif');
                    
                    xAxis.selectAll('line, path')
                        .style('stroke', '#000000')
                        .style('stroke-width', '1.5px');
                    
                    const yAxis = g.append('g')
                        .call(d3.axisLeft(yScale).ticks(5));
                    
                    yAxis.selectAll('text')
                        .style('font-size', '12px')
                        .style('font-weight', '600')
                        .style('fill', '#000000')
                        .style('font-family', 'Arial, sans-serif');
                    
                    yAxis.selectAll('line, path')
                        .style('stroke', '#000000')
                        .style('stroke-width', '1.5px');
                    
                    // Asegurar que el SVG mantenga dimensiones fijas
                    svg.attr('width', width);
                    svg.attr('height', height);
                    svg.style('width', width + 'px');
                    svg.style('height', height + 'px');
                    
                }} else {{
                    console.warn('D3 no está disponible para actualizar el gráfico');
                }}
            }} finally {{
                // CRÍTICO: Resetear flag SIEMPRE, incluso si hay error
                window[flagName] = false;
            }}
        }})();
        """
        
        # Ejecutar JavaScript y resetear flag después de un delay para asegurar que se ejecutó
        display(Javascript(js_update))
        
        # Resetear flag después de un breve delay (el JS se ejecuta de forma asíncrona)
        import threading
        def reset_flag():
            import time
            time.sleep(0.5)  # Esperar 500ms para que el JS se ejecute
            if update_key in self._updating_charts:
                self._updating_charts.remove(update_key)
        
        thread = threading.Thread(target=reset_flag, daemon=True)
        thread.start()
    
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
        
        # CRÍTICO: Pequeño delay para asegurar que los contenedores HTML se rendericen
        # antes de mostrar los layouts
        import time
        time.sleep(0.2)  # 200ms debería ser suficiente
        
        # Crear y mostrar cada vista
        # CRÍTICO: Usar display() normal de MatrixLayout y luego mover el contenido al contenedor correcto
        # Esto asegura que todo el JavaScript necesario se cargue correctamente
        for view_id, view_config in self._views.items():
            container_id = f"{self._container_id}-{view_id}"
            
            if view_config['type'] == 'scatter':
                layout = self._create_scatter_layout(view_id, view_config)
                self._div_ids[view_id] = layout.div_id
                # Mostrar layout normalmente primero
                layout.display()
                # Luego mover al contenedor correcto con un delay para asegurar que se renderizó
                # CRÍTICO: Usar un delay más largo para scatter plots para asegurar que el brush se inicialice
                self._move_layout_to_container(layout.div_id, container_id, delay=500)
            elif view_config['type'] == 'barchart':
                layout = self._create_barchart_layout(view_id, view_config)
                self._div_ids[view_id] = layout.div_id
                # Mostrar layout normalmente primero
                layout.display()
                # Luego mover al contenedor correcto con un delay para asegurar que se renderizó
                self._move_layout_to_container(layout.div_id, container_id, delay=300)
    
    def _move_layout_to_container(self, layout_div_id, container_id, delay=300):
        """Mueve el contenido del layout al contenedor específico después de que se renderice"""
        if not HAS_IPYTHON:
            return
        
        from IPython.display import Javascript
        
        # Mover el contenido una sola vez después de un delay
        # CRÍTICO: Usar un delay suficiente para que el layout se renderice completamente
        js_move = f"""
        (function() {{
            let attempts = 0;
            const maxAttempts = 20; // Máximo 2 segundos (20 * 100ms)
            
            function moveLayout() {{
                attempts++;
                const targetContainer = document.getElementById('{container_id}');
                const layoutDiv = document.getElementById('{layout_div_id}');
                
                // Verificar que ambos elementos existan
                if (!targetContainer || !layoutDiv) {{
                    if (attempts < maxAttempts) {{
                        setTimeout(moveLayout, 100);
                        return;
                    }}
                    console.warn('No se encontraron contenedores después de', maxAttempts, 'intentos');
                    return;
                }}
                
                // Verificar que el layout tenga contenido renderizado
                // Buscar SVG o contenido dentro del layout
                const hasContent = layoutDiv.querySelector('svg') || 
                                   layoutDiv.querySelector('.matrix-cell') ||
                                   layoutDiv.innerHTML.trim().length > 0;
                
                if (!hasContent) {{
                    if (attempts < maxAttempts) {{
                        setTimeout(moveLayout, 100);
                        return;
                    }}
                    console.warn('Layout no tiene contenido después de', maxAttempts, 'intentos');
                    return;
                }}
                
                // CRÍTICO: Mover TODO el contenido del layout al contenedor objetivo
                // IMPORTANTE: NO usar innerHTML porque destruye los event listeners de D3.js (brush)
                // En su lugar, mover los nodos directamente usando appendChild
                
                // Mover todos los hijos del layoutDiv al targetContainer
                while (layoutDiv.firstChild) {{
                    targetContainer.appendChild(layoutDiv.firstChild);
                }}
                
                // Actualizar el div_id del contenedor para que coincida (para eventos)
                const newLayoutDiv = targetContainer.querySelector('.matrix-layout');
                if (newLayoutDiv) {{
                    newLayoutDiv.id = '{layout_div_id}';
                    
                    // CRÍTICO: Asegurar que el sistema de comm siga funcionando después de mover
                    // El div_id se mantiene, así que el comm debería seguir funcionando
                    if (typeof window.sendEvent === 'function') {{
                        console.log('✅ Layout movido correctamente (preservando event listeners), div_id:', '{layout_div_id}');
                    }} else {{
                        console.warn('⚠️ window.sendEvent no está disponible después de mover layout');
                    }}
                    
                    // CRÍTICO: Verificar que los event listeners del scatter plot sigan funcionando
                    // Los event listeners deberían estar preservados porque movimos los nodos directamente
                    const scatterPoints = newLayoutDiv.querySelectorAll('.scatter-point, circle[data-point]');
                    const brushOverlay = newLayoutDiv.querySelector('.brush-overlay, .brush');
                    if (scatterPoints.length > 0) {{
                        console.log('✅ Encontrados', scatterPoints.length, 'puntos del scatter plot');
                    }}
                    if (brushOverlay) {{
                        console.log('✅ Brush overlay encontrado');
                    }}
                }}
                
                // CRÍTICO: NO eliminar el div original inmediatamente
                // Esperar un poco para asegurar que todo se haya movido correctamente
                // IMPORTANTE: El layoutDiv original puede estar vacío ahora, pero debemos eliminarlo
                // para evitar duplicados en el DOM
                setTimeout(function() {{
                    // Verificar que el layoutDiv esté vacío antes de eliminarlo
                    if (layoutDiv && layoutDiv.parentNode && layoutDiv.children.length === 0) {{
                        layoutDiv.parentNode.removeChild(layoutDiv);
                    }} else if (layoutDiv && layoutDiv.parentNode) {{
                        // Si aún tiene hijos, moverlos también
                        while (layoutDiv.firstChild) {{
                            targetContainer.appendChild(layoutDiv.firstChild);
                        }}
                        // Luego eliminar el contenedor vacío
                        if (layoutDiv.parentNode && layoutDiv.children.length === 0) {{
                            layoutDiv.parentNode.removeChild(layoutDiv);
                        }}
                    }}
                }}, 200);  // Aumentar delay para asegurar que todo se haya movido
            }}
            
            // Iniciar después de un delay inicial
            setTimeout(moveLayout, {delay});
        }})();
        """
        
        display(Javascript(js_move))
    
    
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
