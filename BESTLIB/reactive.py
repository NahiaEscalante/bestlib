"""
Sistema de Variables Reactivas para BESTLIB
Permite que los datos se actualicen automáticamente sin re-ejecutar celdas
"""

import ipywidgets as widgets
from traitlets import List, Dict, Int, observe

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


class ReactiveData(widgets.Widget):
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
        self._callbacks.append(callback)
    
    @observe('items')
    def _items_changed(self, change):
        """Se ejecuta automáticamente cuando items cambia"""
        new_items = change['new']
        self.count = len(new_items)
        
        # Ejecutar callbacks registrados
        for callback in self._callbacks:
            try:
                callback(new_items, self.count)
            except Exception as e:
                print(f"Error en callback: {e}")
    
    def update(self, items):
        """Actualiza los items manualmente desde Python"""
        self.items = items
        self.count = len(items)
    
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
    
    def __init__(self, ascii_layout=None, selection_model=None):
        """
        Crea un MatrixLayout con soporte reactivo y LinkedViews integrado.
        
        Args:
            ascii_layout: Layout ASCII (opcional)
            selection_model: Instancia de SelectionModel para reactividad
        """
        from .matrix import MatrixLayout
        
        # Crear instancia base de MatrixLayout
        self._layout = MatrixLayout(ascii_layout)
        
        # Modelo reactivo
        self.selection_model = selection_model or SelectionModel()
        
        # Conectar el modelo reactivo
        self._layout.connect_selection(self.selection_model)
        
        # Sistema de vistas enlazadas
        self._views = {}  # {view_id: view_config}
        self._data = None  # DataFrame o lista de diccionarios
        self._selected_data = []  # Datos seleccionados actualmente
        self._view_letters = {}  # {view_id: letter} - mapeo de vista a letra del layout
        self._barchart_callbacks = {}  # {letter: callback_func} - para evitar duplicados
        self._barchart_cell_ids = {}  # {letter: cell_id} - IDs de celdas de bar charts
        self._scatter_selection_models = {}  # {scatter_letter: SelectionModel} - Modelos por scatter
        self._barchart_to_scatter = {}  # {barchart_letter: scatter_letter} - Enlaces scatter->bar
        self._linked_charts = {}  # {chart_letter: {'type': str, 'linked_to': str, 'callback': func}} - Gráficos enlazados genéricos
    
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
        from .matrix import MatrixLayout
        
        # Crear handler que filtra eventos por letra del scatter
        # Usar closure para capturar la letra
        scatter_letter_capture = letter
        scatter_selection_capture = scatter_selection
        
        def scatter_handler(payload):
            """Handler que actualiza el SelectionModel de este scatter plot Y el modelo principal"""
            # Filtrar eventos: solo procesar si viene de este scatter plot
            event_scatter_letter = payload.get('__scatter_letter__')
            if event_scatter_letter != scatter_letter_capture:
                # Este evento no es para este scatter plot, ignorar
                return
            
            # El payload ya viene con __scatter_letter__ del JavaScript
            items = payload.get('items', [])
            
            # Actualizar el SelectionModel específico de este scatter plot
            scatter_selection_capture.update(items)
            
            # IMPORTANTE: También actualizar el selection_model principal para que selected_data se actualice
            # Esto asegura que los datos seleccionados estén disponibles globalmente
            self.selection_model.update(items)
            
            # Actualizar también _selected_data para compatibilidad
            self._selected_data = items
        
        # Registrar handler en el layout principal
        # Nota: Usamos el mismo layout pero cada scatter tiene su propio SelectionModel
        # El JavaScript enviará __scatter_letter__ en el payload
        self._layout.on('select', scatter_handler)
        
        # Configurar el scatter plot en el mapping
        # Agregar la letra del scatter en el spec para identificar eventos
        scatter_spec = MatrixLayout.map_scatter(
            letter, 
            self._data, 
            x_col=x_col, 
            y_col=y_col, 
            category_col=category_col,
            interactive=interactive,
            **kwargs
        )
        
        # Agregar identificador del scatter plot para enrutamiento de eventos
        if scatter_spec:
            scatter_spec['__scatter_letter__'] = letter
            scatter_spec['__selection_model_id__'] = id(scatter_selection)  # ID único para identificar
            MatrixLayout._map[letter] = scatter_spec
        
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
    
    def add_barchart(self, letter, category_col=None, value_col=None, linked_to=None, **kwargs):
        """
        Agrega un bar chart enlazado que se actualiza automáticamente cuando se selecciona en scatter.
        
        Args:
            letter: Letra del layout ASCII donde irá el bar chart
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional, si no se especifica cuenta)
            linked_to: Letra del scatter plot que debe actualizar este bar chart (opcional)
                      Si no se especifica, se enlaza al último scatter plot agregado
            **kwargs: Argumentos adicionales (color, colorMap, axes, etc.)
        
        Returns:
            self para encadenamiento
        
        Ejemplo:
            layout.add_scatter('S1', df, ...)  # Scatter plot 1
            layout.add_scatter('S2', df, ...)  # Scatter plot 2
            layout.add_barchart('B1', linked_to='S1')  # Bar chart enlazado a S1
            layout.add_barchart('B2', linked_to='S2')  # Bar chart enlazado a S2
        """
        # Importar MatrixLayout al inicio para evitar UnboundLocalError
        from .matrix import MatrixLayout
        
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero para establecer los datos")
        
        # Evitar registrar múltiples callbacks para la misma letra
        if letter in self._barchart_callbacks:
            if MatrixLayout._debug:
                print(f"⚠️ Bar chart para '{letter}' ya está registrado. Ignorando registro duplicado.")
            return self
        
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
            if MatrixLayout._debug:
                print(f"💡 Bar chart '{letter}' enlazado automáticamente a scatter '{scatter_letter}'")
        
        # Guardar el enlace
        self._barchart_to_scatter[letter] = scatter_letter
        
        # Crear bar chart inicial con todos los datos
        MatrixLayout.map_barchart(
            letter,
            self._data,
            category_col=category_col,
            value_col=value_col,
            **kwargs
        )
        
        # Registrar vista para sistema de enlace
        view_id = f"barchart_{letter}"
        self._views[view_id] = {
            'type': 'barchart',
            'letter': letter,
            'category_col': category_col,
            'value_col': value_col,
            'kwargs': kwargs
        }
        self._view_letters[view_id] = letter
        
        # Guardar parámetros para el callback (closure)
        barchart_params = {
            'letter': letter,
            'category_col': category_col,
            'value_col': value_col,
            'kwargs': kwargs.copy(),  # Copia para evitar mutaciones
            'layout_div_id': self._layout.div_id
        }
        
        # Configurar callback para actualizar bar chart cuando cambia selección
        def update_barchart(items, count):
            """Actualiza el bar chart cuando cambia la selección usando JavaScript"""
            try:
                import json
                from IPython.display import Javascript
                
                # Usar datos seleccionados o todos los datos
                data_to_use = self._data
                if items and len(items) > 0:
                    # Convertir lista de dicts a DataFrame si es necesario
                    if HAS_PANDAS and isinstance(items[0], dict):
                        import pandas as pd
                        data_to_use = pd.DataFrame(items)
                    else:
                        data_to_use = items
                
                # Preparar datos del bar chart
                bar_data = self._prepare_barchart_data(
                    data_to_use, 
                    barchart_params['category_col'], 
                    barchart_params['value_col'],
                    barchart_params['kwargs']
                )
                
                if not bar_data:
                    return
                
                # Actualizar también el mapping para consistencia
                MatrixLayout.map_barchart(
                    letter,
                    data_to_use,
                    category_col=barchart_params['category_col'],
                    value_col=barchart_params['value_col'],
                    **barchart_params['kwargs']
                )
                
                # Crear JavaScript para actualizar el gráfico de forma más robusta
                div_id = barchart_params['layout_div_id']
                bar_data_json = json.dumps(bar_data)
                color_map = barchart_params['kwargs'].get('colorMap', {})
                color_map_json = json.dumps(color_map)
                default_color = barchart_params['kwargs'].get('color', '#4a90e2')
                show_axes = barchart_params['kwargs'].get('axes', True)
                
                js_update = f"""
                (function() {{
                    // Esperar a que D3 esté disponible
                    function updateBarchart() {{
                        if (!window.d3) {{
                            setTimeout(updateBarchart, 100);
                            return;
                        }}
                        
                        const container = document.getElementById('{div_id}');
                        if (!container) return;
                        
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
                            console.warn('No se encontró celda para bar chart {letter}');
                            return;
                        }}
                        
                        // Limpiar celda completamente
                        targetCell.innerHTML = '';
                        
                        // Re-renderizar bar chart con nuevos datos
                        const width = Math.max(targetCell.clientWidth || 400, 200);
                        // Calcular altura disponible: considerar padding del contenedor (30px total) y espacio para ejes
                        const availableHeight = Math.max(targetCell.clientHeight - 30, 320);  // Altura mínima de 320px
                        const height = Math.min(availableHeight, 350);  // Altura máxima de 350px para mantener proporción
                        const margin = {{ top: 20, right: 20, bottom: 40, left: 50 }};
                        const chartWidth = width - margin.left - margin.right;
                        const chartHeight = height - margin.top - margin.bottom;
                        
                        const data = {bar_data_json};
                        const colorMap = {color_map_json};
                        
                        if (data.length === 0) {{
                            targetCell.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos</div>';
                            return;
                        }}
                        
                        const svg = window.d3.select(targetCell)
                            .append('svg')
                            .attr('width', width)
                            .attr('height', height);
                        
                        const g = svg.append('g')
                            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
                        
                        const x = window.d3.scaleBand()
                            .domain(data.map(d => d.category))
                            .range([0, chartWidth])
                            .padding(0.2);
                        
                        const y = window.d3.scaleLinear()
                            .domain([0, window.d3.max(data, d => d.value) || 100])
                            .nice()
                            .range([chartHeight, 0]);
                        
                        // Renderizar barras
                        g.selectAll('.bar')
                            .data(data)
                            .enter()
                            .append('rect')
                            .attr('class', 'bar')
                            .attr('x', d => x(d.category))
                            .attr('y', chartHeight)
                            .attr('width', x.bandwidth())
                            .attr('height', 0)
                            .attr('fill', d => colorMap[d.category] || d.color || '{default_color}')
                            .transition()
                            .duration(500)
                            .ease(window.d3.easeCubicOut)
                            .attr('y', d => y(d.value))
                            .attr('height', d => chartHeight - y(d.value));
                        
                        // Renderizar ejes si se requiere
                        if ({str(show_axes).lower()}) {{
                            const xAxis = g.append('g')
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
                    }}
                    
                    updateBarchart();
                }})();
                """
                
                # Ejecutar JavaScript para actualizar solo el bar chart
                # Usar eval_js en lugar de display para evitar duplicación
                try:
                    from IPython.display import Javascript, display
                    display(Javascript(js_update), clear=False)
                except:
                    # Fallback si no está disponible
                    pass
                
            except Exception as e:
                if MatrixLayout._debug:
                    print(f"⚠️ Error actualizando bar chart: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Guardar callback para referencia
        self._barchart_callbacks[letter] = update_barchart
        
        # Registrar callback en el modelo de selección ESPECÍFICO del scatter plot
        # Esto permite que cada scatter plot actualice solo sus bar charts asociados
        scatter_selection = self._scatter_selection_models[scatter_letter]
        scatter_selection.on_change(update_barchart)
        
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
            if MatrixLayout._debug:
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
                if MatrixLayout._debug:
                    print(f"🔄 Actualizando gráfico '{letter}' ({chart_type}) con {count} elementos seleccionados")
            
            update_func = generic_update
        
        # Registrar callback en el modelo de selección del scatter plot
        scatter_selection = self._scatter_selection_models[scatter_letter]
        scatter_selection.on_change(update_func)
        
        return self
    
    def add_histogram(self, letter, column=None, bins=20, linked_to=None, **kwargs):
        """
        Agrega un histograma enlazado que se actualiza automáticamente cuando se selecciona en scatter.
        
        Args:
            letter: Letra del layout ASCII donde irá el histograma
            column: Nombre de columna numérica para el histograma
            bins: Número de bins (default: 20)
            linked_to: Letra del scatter plot que debe actualizar este histograma (opcional)
            **kwargs: Argumentos adicionales (color, axes, etc.)
        
        Returns:
            self para encadenamiento
        """
        from .matrix import MatrixLayout
        
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero para establecer los datos")
        
        if column is None:
            raise ValueError("Debe especificar 'column' para el histograma")
        
        # Determinar a qué scatter plot enlazar
        if linked_to:
            if linked_to not in self._scatter_selection_models:
                raise ValueError(f"Scatter plot '{linked_to}' no existe.")
            scatter_letter = linked_to
        else:
            if not self._scatter_selection_models:
                raise ValueError("No hay scatter plots disponibles.")
            scatter_letter = list(self._scatter_selection_models.keys())[-1]
        
        # Guardar parámetros
        hist_params = {
            'letter': letter,
            'column': column,
            'bins': bins,
            'kwargs': kwargs.copy(),
            'layout_div_id': self._layout.div_id
        }
        
        # Función de actualización del histograma
        def update_histogram(items, count):
            """Actualiza el histograma cuando cambia la selección"""
            try:
                import json
                from IPython.display import Javascript
                
                # Usar datos seleccionados o todos los datos
                data_to_use = self._data
                if items and len(items) > 0:
                    if HAS_PANDAS and isinstance(items[0], dict):
                        import pandas as pd
                        data_to_use = pd.DataFrame(items)
                    else:
                        data_to_use = items
                
                # Preparar datos para histograma
                if HAS_PANDAS and isinstance(data_to_use, pd.DataFrame):
                    values = data_to_use[column].dropna().tolist()
                else:
                    values = [item.get(column, 0) for item in data_to_use if column in item]
                
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
                bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]
                
                hist_data = [{'bin': center, 'count': count} for center, count in zip(bin_centers, hist)]
                
                # Actualizar mapping
                from .matrix import MatrixLayout
                MatrixLayout._map[letter] = {
                    'type': 'histogram',
                    'data': hist_data,
                    'column': column,
                    'bins': bins,
                    **kwargs
                }
                
                # JavaScript para actualizar el gráfico (similar a bar chart)
                div_id = hist_params['layout_div_id']
                hist_data_json = json.dumps(hist_data)
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
                        
                        targetCell.innerHTML = '';
                        
                        const width = Math.max(targetCell.clientWidth || 400, 200);
                        const availableHeight = Math.max(targetCell.clientHeight - 30, 320);
                        const height = Math.min(availableHeight, 350);
                        const margin = {{ top: 20, right: 20, bottom: 40, left: 50 }};
                        const chartWidth = width - margin.left - margin.right;
                        const chartHeight = height - margin.top - margin.bottom;
                        
                        const data = {hist_data_json};
                        
                        if (data.length === 0) {{
                            targetCell.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos</div>';
                            return;
                        }}
                        
                        const svg = window.d3.select(targetCell)
                            .append('svg')
                            .attr('width', width)
                            .attr('height', height);
                        
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
                        
                        g.selectAll('.bar')
                            .data(data)
                            .enter()
                            .append('rect')
                            .attr('class', 'bar')
                            .attr('x', d => x(d.bin))
                            .attr('y', chartHeight)
                            .attr('width', x.bandwidth())
                            .attr('height', 0)
                            .attr('fill', '{default_color}')
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
                
                try:
                    from IPython.display import Javascript, display
                    display(Javascript(js_update), clear=False)
                except:
                    pass
                    
            except Exception as e:
                from .matrix import MatrixLayout
                if MatrixLayout._debug:
                    print(f"⚠️ Error actualizando histograma: {e}")
        
        # Registrar callback
        scatter_selection = self._scatter_selection_models[scatter_letter]
        scatter_selection.on_change(update_histogram)
        
        # Crear histograma inicial con todos los datos
        if HAS_PANDAS and isinstance(self._data, pd.DataFrame):
            values = self._data[column].dropna().tolist()
        else:
            values = [item.get(column, 0) for item in self._data if column in item]
        
        if values:
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
            bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]
            hist_data = [{'bin': center, 'count': count} for center, count in zip(bin_centers, hist)]
            
            MatrixLayout._map[letter] = {
                'type': 'histogram',
                'data': hist_data,
                'column': column,
                'bins': bins,
                **kwargs
            }
        
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
        
        # Determinar a qué scatter plot enlazar
        if linked_to:
            if linked_to not in self._scatter_selection_models:
                raise ValueError(f"Scatter plot '{linked_to}' no existe.")
            scatter_letter = linked_to
        else:
            if not self._scatter_selection_models:
                raise ValueError("No hay scatter plots disponibles.")
            scatter_letter = list(self._scatter_selection_models.keys())[-1]
        
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
            try:
                import json
                from IPython.display import Javascript
                
                # Usar datos seleccionados o todos los datos
                data_to_use = self._data
                if items and len(items) > 0:
                    if HAS_PANDAS and isinstance(items[0], dict):
                        import pandas as pd
                        data_to_use = pd.DataFrame(items)
                    else:
                        data_to_use = items
                
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
                
                # Actualizar mapping
                MatrixLayout._map[letter] = {
                    'type': 'boxplot',
                    'data': box_data,
                    'column': column,
                    'category_col': category_col,
                    **kwargs
                }
                
                # JavaScript para actualizar el gráfico
                div_id = boxplot_params['layout_div_id']
                box_data_json = json.dumps(box_data)
                default_color = kwargs.get('color', '#4a90e2')
                show_axes = kwargs.get('axes', True)
                
                js_update = f"""
                (function() {{
                    function updateBoxplot() {{
                        if (!window.d3) {{
                            setTimeout(updateBoxplot, 100);
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
                        
                        targetCell.innerHTML = '';
                        
                        const width = Math.max(targetCell.clientWidth || 400, 200);
                        const availableHeight = Math.max(targetCell.clientHeight - 30, 320);
                        const height = Math.min(availableHeight, 350);
                        const margin = {{ top: 20, right: 20, bottom: 40, left: 50 }};
                        const chartWidth = width - margin.left - margin.right;
                        const chartHeight = height - margin.top - margin.bottom;
                        
                        const data = {box_data_json};
                        
                        if (data.length === 0) {{
                            targetCell.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">No hay datos</div>';
                            return;
                        }}
                        
                        const svg = window.d3.select(targetCell)
                            .append('svg')
                            .attr('width', width)
                            .attr('height', height);
                        
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
                    }}
                    
                    updateBoxplot();
                }})();
                """
                
                try:
                    from IPython.display import Javascript, display
                    display(Javascript(js_update), clear=False)
                except:
                    pass
                    
            except Exception as e:
                from .matrix import MatrixLayout
                if MatrixLayout._debug:
                    print(f"⚠️ Error actualizando boxplot: {e}")
        
        # Registrar callback
        scatter_selection = self._scatter_selection_models[scatter_letter]
        scatter_selection.on_change(update_boxplot)
        
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
            MatrixLayout._map[letter] = {
                'type': 'boxplot',
                'data': box_data,
                'column': column,
                'category_col': category_col,
                **kwargs
            }
        
        return self
    
    def _prepare_barchart_data(self, data, category_col, value_col, kwargs):
        """Helper para preparar datos del bar chart"""
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
            
            # Obtener colorMap
            color_map = kwargs.get('colorMap', {})
            default_color = kwargs.get('color', '#4a90e2')
            for bar_item in bar_data:
                bar_item['color'] = color_map.get(bar_item['category'], default_color)
            
            return bar_data
        except Exception as e:
            from .matrix import MatrixLayout
            if MatrixLayout._debug:
                print(f"⚠️ Error preparando datos del bar chart: {e}")
            return []
    
    def map(self, mapping):
        """Delega al MatrixLayout interno"""
        self._layout.map(mapping)
        return self
    
    def on(self, event, func):
        """Delega al MatrixLayout interno"""
        self._layout.on(event, func)
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
    
    @property
    def selection_widget(self):
        """
        Retorna el widget de selección para mostrar en Jupyter.
        
        Uso:
            display(layout.selection_widget)
        """
        if not hasattr(self.selection_model, '_widget'):
            # Crear widget visual
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


