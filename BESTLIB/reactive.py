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
        
        # Usar el método helper de MatrixLayout
        from .matrix import MatrixLayout
        MatrixLayout.map_scatter(
            letter, 
            self._data, 
            x_col=x_col, 
            y_col=y_col, 
            category_col=category_col,
            interactive=interactive,
            **kwargs
        )
        
        # Registrar vista para sistema de enlace
        view_id = f"scatter_{letter}"
        self._views[view_id] = {
            'type': 'scatter',
            'letter': letter,
            'x_col': x_col,
            'y_col': y_col,
            'category_col': category_col,
            'interactive': interactive,
            'kwargs': kwargs
        }
        self._view_letters[view_id] = letter
        
        return self
    
    def add_barchart(self, letter, category_col=None, value_col=None, **kwargs):
        """
        Agrega un bar chart enlazado que se actualiza automáticamente cuando se selecciona en scatter.
        
        Args:
            letter: Letra del layout ASCII donde irá el bar chart
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional, si no se especifica cuenta)
            **kwargs: Argumentos adicionales (color, colorMap, axes, etc.)
        
        Returns:
            self para encadenamiento
        """
        if self._data is None:
            raise ValueError("Debe usar set_data() o add_scatter() primero para establecer los datos")
        
        # Evitar registrar múltiples callbacks para la misma letra
        if letter in self._barchart_callbacks:
            if MatrixLayout._debug:
                print(f"⚠️ Bar chart para '{letter}' ya está registrado. Actualizando configuración.")
            # Remover callback anterior
            # (No podemos remover fácilmente, pero podemos evitar duplicados)
        
        # Crear bar chart inicial con todos los datos
        from .matrix import MatrixLayout
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
        
        # Guardar parámetros para el callback
        barchart_params = {
            'letter': letter,
            'category_col': category_col,
            'value_col': value_col,
            'kwargs': kwargs
        }
        
        # Configurar callback para actualizar bar chart cuando cambia selección
        def update_barchart(items, count):
            """Actualiza el bar chart cuando cambia la selección usando JavaScript"""
            try:
                import json
                from IPython.display import display, Javascript
                
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
                if HAS_PANDAS and isinstance(data_to_use, pd.DataFrame):
                    if value_col and value_col in data_to_use.columns:
                        bar_data = data_to_use.groupby(category_col)[value_col].sum().reset_index()
                        bar_data = bar_data.rename(columns={category_col: 'category', value_col: 'value'})
                        bar_data = bar_data.to_dict('records')
                    elif category_col and category_col in data_to_use.columns:
                        counts = data_to_use[category_col].value_counts()
                        bar_data = [{'category': cat, 'value': count} for cat, count in counts.items()]
                    else:
                        return
                else:
                    from collections import Counter
                    if value_col:
                        from collections import defaultdict
                        sums = defaultdict(float)
                        for item in data_to_use:
                            cat = item.get(category_col, 'unknown')
                            val = item.get(value_col, 0)
                            sums[cat] += val
                        bar_data = [{'category': cat, 'value': val} for cat, val in sums.items()]
                    else:
                        categories = Counter([item.get(category_col, 'unknown') for item in data_to_use])
                        bar_data = [{'category': cat, 'value': count} for cat, count in categories.items()]
                
                # Obtener colorMap
                color_map = kwargs.get('colorMap', {})
                for bar_item in bar_data:
                    bar_item['color'] = color_map.get(bar_item['category'], kwargs.get('color', '#4a90e2'))
                
                # Actualizar también el mapping para consistencia
                MatrixLayout.map_barchart(
                    letter,
                    data_to_use,
                    category_col=category_col,
                    value_col=value_col,
                    **kwargs
                )
                
                # Actualizar el gráfico usando JavaScript (sin re-renderizar todo)
                div_id = self._layout.div_id
                bar_data_json = json.dumps(bar_data)
                color_map_json = json.dumps(color_map) if color_map else '{}'
                
                js_update = f"""
                (function() {{
                    const container = document.getElementById('{div_id}');
                    if (!container) return;
                    
                    // Buscar todas las celdas
                    const cells = container.querySelectorAll('.matrix-cell');
                    
                    // Encontrar la celda que tiene el bar chart (buscar por SVG con barras)
                    let targetCell = null;
                    let targetIndex = -1;
                    
                    cells.forEach((cell, idx) => {{
                        const svg = cell.querySelector('svg');
                        if (svg) {{
                            const bars = svg.querySelectorAll('.bar');
                            if (bars && bars.length > 0) {{
                                targetCell = cell;
                                targetIndex = idx;
                            }}
                        }}
                    }});
                    
                    if (targetCell && window.d3) {{
                        // Limpiar celda
                        targetCell.innerHTML = '';
                        
                        // Re-renderizar bar chart con nuevos datos
                        const width = targetCell.clientWidth || 400;
                        const height = 250;
                        const margin = {{ top: 20, right: 20, bottom: 40, left: 50 }};
                        const chartWidth = width - margin.left - margin.right;
                        const chartHeight = height - margin.top - margin.bottom;
                        
                        const data = {bar_data_json};
                        const colorMap = {color_map_json};
                        
                        const svg = d3.select(targetCell)
                            .append('svg')
                            .attr('width', width)
                            .attr('height', height);
                        
                        const g = svg.append('g')
                            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
                        
                        const x = d3.scaleBand()
                            .domain(data.map(d => d.category))
                            .range([0, chartWidth])
                            .padding(0.2);
                        
                        const y = d3.scaleLinear()
                            .domain([0, d3.max(data, d => d.value) || 100])
                            .nice()
                            .range([chartHeight, 0]);
                        
                        g.selectAll('.bar')
                            .data(data)
                            .enter()
                            .append('rect')
                            .attr('class', 'bar')
                            .attr('x', d => x(d.category))
                            .attr('y', chartHeight)
                            .attr('width', x.bandwidth())
                            .attr('height', 0)
                            .attr('fill', d => colorMap[d.category] || d.color || '{kwargs.get("color", "#4a90e2")}')
                            .transition()
                            .duration(500)
                            .attr('y', d => y(d.value))
                            .attr('height', d => chartHeight - y(d.value));
                        
                        if ({kwargs.get('axes', True)}) {{
                            const xAxis = g.append('g')
                                .attr('transform', `translate(0,${{chartHeight}})`)
                                .call(d3.axisBottom(x));
                            
                            xAxis.selectAll('text')
                                .style('font-size', '12px')
                                .style('font-weight', '600')
                                .style('fill', '#000000')
                                .style('font-family', 'Arial, sans-serif');
                            
                            xAxis.selectAll('line, path')
                                .style('stroke', '#000000')
                                .style('stroke-width', '1.5px');
                            
                            const yAxis = g.append('g')
                                .call(d3.axisLeft(y).ticks(5));
                            
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
                }})();
                """
                
                # Ejecutar JavaScript para actualizar solo el bar chart
                display(Javascript(js_update))
                
            except Exception as e:
                if MatrixLayout._debug:
                    print(f"⚠️ Error actualizando bar chart: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Guardar callback para referencia
        self._barchart_callbacks[letter] = update_barchart
        
        # Registrar callback en el modelo de selección (solo una vez)
        self.selection_model.on_change(update_barchart)
        
        return self
    
    def map(self, mapping):
        """Delega al MatrixLayout interno"""
        self._layout.map(mapping)
        return self
    
    def on(self, event, func):
        """Delega al MatrixLayout interno"""
        self._layout.on(event, func)
        return self
    
    def display(self, ascii_layout=None):
        """Muestra el layout"""
        if ascii_layout:
            self._layout.ascii_layout = ascii_layout
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
    def count(self):
        """Retorna el número de items seleccionados"""
        return self.selection_model.get_count()

