import uuid
import json
import os
import weakref

try:
    import ipywidgets as widgets
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

class MatrixLayout:
    _map = {}
    _safe_html = True
    
    # Sistema de comunicación bidireccional (JS → Python)
    _instances = {}  # dict[str, weakref.ReferenceType[MatrixLayout]]
    _global_handlers = {}  # dict[str, callable]
    _comm_registered = False
    _debug = False  # Modo debug para ver mensajes detallados
    
    @staticmethod
    def _prepare_data(data, x_col=None, y_col=None, category_col=None, value_col=None):
        """
        Prepara datos para visualización, aceptando DataFrames de pandas o listas de diccionarios.
        
        Args:
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X (scatter plots)
            y_col: Nombre de columna para eje Y (scatter plots)
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (bar charts)
        
        Returns:
            tuple: (datos_procesados, datos_originales)
            - datos_procesados: Lista de diccionarios con formato estándar
            - datos_originales: Lista de diccionarios con todas las columnas originales
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            # Convertir DataFrame a lista de diccionarios
            original_data = data.to_dict('records')
            
            processed_data = []
            for idx, row in data.iterrows():
                item = {}
                
                # Mapear columnas según especificación
                if x_col and x_col in data.columns:
                    item['x'] = row[x_col]
                elif 'x' in row:
                    item['x'] = row['x']
                
                if y_col and y_col in data.columns:
                    item['y'] = row[y_col]
                elif 'y' in row:
                    item['y'] = row['y']
                
                if category_col and category_col in data.columns:
                    item['category'] = row[category_col]
                elif 'category' in row:
                    item['category'] = row['category']
                
                if value_col and value_col in data.columns:
                    item['value'] = row[value_col]
                elif 'value' in row:
                    item['value'] = row['value']
                
                # Guardar referencia a la fila original completa
                item['_original_row'] = original_data[idx]
                item['_original_index'] = int(idx)
                
                processed_data.append(item)
            
            return processed_data, original_data
        else:
            # Si ya es lista de diccionarios, solo agregar referencias
            if isinstance(data, list):
                processed_data = []
                for idx, item in enumerate(data):
                    processed_item = item.copy()
                    # Asegurar que existe _original_row
                    if '_original_row' not in processed_item:
                        processed_item['_original_row'] = item
                    if '_original_index' not in processed_item:
                        processed_item['_original_index'] = idx
                    processed_data.append(processed_item)
                return processed_data, data
            else:
                raise ValueError("Los datos deben ser un DataFrame de pandas o una lista de diccionarios")
    
    @classmethod
    def set_debug(cls, enabled: bool):
        """Activa/desactiva mensajes de debug."""
        cls._debug = enabled
    
    @classmethod
    def on_global(cls, event, func):
        """Registra un callback global para un tipo de evento."""
        cls._global_handlers[event] = func
    
    @classmethod
    def register_comm(cls, force=False):
        """
        Registra manualmente el comm target de Jupyter.
        Útil para forzar el registro o verificar que funciona.
        
        Args:
            force (bool): Si True, fuerza el re-registro incluso si ya está registrado
        
        Returns:
            bool: True si el registro fue exitoso, False si falló
        """
        if cls._comm_registered and not force:
            if cls._debug:
                print("ℹ️ [MatrixLayout] Comm ya estaba registrado")
            return True
        
        if force:
            cls._comm_registered = False
        
        return cls._ensure_comm_target()
    
    @classmethod
    def _ensure_comm_target(cls):
        """
        Registra el comm target de Jupyter para recibir eventos desde JS.
        Solo se ejecuta una vez por sesión.
        
        Returns:
            bool: True si el registro fue exitoso, False si falló
        """
        if cls._comm_registered:
            return True
        
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if not ip or not hasattr(ip, "kernel"):
                if cls._debug:
                    print("⚠️ [MatrixLayout] No hay kernel de IPython disponible")
                return False
            
            km = ip.kernel.comm_manager
            
            def _target(comm, open_msg):
                """Handler del comm target que procesa mensajes desde JS"""
                div_id = open_msg['content']['data'].get('div_id', 'unknown')
                
                if cls._debug:
                    print(f"🔗 [MatrixLayout] Comm abierto para div_id: {div_id}")
                
                @comm.on_msg
                def _recv(msg):
                    try:
                        data = msg["content"]["data"]
                        div_id = data.get("div_id")
                        event_type = data.get("type")
                        payload = data.get("payload")
                        
                        if cls._debug:
                            print(f"📩 [MatrixLayout] Evento recibido:")
                            print(f"   - Tipo: {event_type}")
                            print(f"   - Div ID: {div_id}")
                            print(f"   - Payload: {payload}")
                        
                        # Buscar instancia por div_id
                        inst_ref = cls._instances.get(div_id)
                        inst = inst_ref() if inst_ref else None
                        
                        # Buscar handlers: primero en instancia (puede haber múltiples), luego global
                        handlers = []
                        
                        # Obtener todos los handlers de la instancia (puede haber múltiples para LinkedViews)
                        if inst and hasattr(inst, "_handlers"):
                            handler = inst._handlers.get(event_type)
                            if handler:
                                # Handler puede ser una función o lista de funciones
                                if isinstance(handler, list):
                                    handlers.extend(handler)
                                else:
                                    handlers.append(handler)
                                if cls._debug:
                                    print(f"   ✓ {len(handlers)} handler(s) de instancia encontrado(s)")
                        
                        # Agregar handler global si existe
                        global_handler = cls._global_handlers.get(event_type)
                        if global_handler:
                            handlers.append(global_handler)
                            if cls._debug:
                                print(f"   ✓ Handler global encontrado")
                        
                        # Ejecutar todos los callbacks (múltiples para soportar múltiples scatter plots)
                        if handlers:
                            for handler in handlers:
                                try:
                                    handler(payload)
                                except Exception as e:
                                    if cls._debug:
                                        print(f"   ❌ Error en handler: {e}")
                                        import traceback
                                        traceback.print_exc()
                        else:
                            if cls._debug:
                                print(f"   ⚠️ No hay handler registrado para '{event_type}'")
                    
                    except Exception as e:
                        print(f"❌ [MatrixLayout] Error en handler: {e}")
                        if cls._debug:
                            import traceback
                            traceback.print_exc()
            
            km.register_target("bestlib_matrix", _target)
            cls._comm_registered = True
            
            if cls._debug:
                print("✅ [MatrixLayout] Comm target 'bestlib_matrix' registrado exitosamente")
            
            return True
            
        except Exception as e:
            print(f"❌ [MatrixLayout] No se pudo registrar comm: {e}")
            if cls._debug:
                import traceback
                traceback.print_exc()
            return False
    
    def on(self, event, func):
        """
        Registra un callback específico para esta instancia.
        
        Nota: Si se registran múltiples handlers para el mismo evento,
        todos se ejecutarán (útil para LinkedViews con múltiples scatter plots).
        """
        if not hasattr(self, "_handlers"):
            self._handlers = {}
        
        # Permitir múltiples handlers para el mismo evento
        if event not in self._handlers:
            self._handlers[event] = []
        elif not isinstance(self._handlers[event], list):
            # Convertir handler único a lista
            self._handlers[event] = [self._handlers[event]]
        
        self._handlers[event].append(func)
        return self

    @classmethod
    def map(cls, mapping):
        cls._map = mapping
    
    @classmethod
    def map_scatter(cls, letter, data, x_col=None, y_col=None, category_col=None, size_col=None, color_col=None, **kwargs):
        """
        Método helper para crear scatter plot desde DataFrame de pandas.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            x_col: Nombre de columna para eje X
            y_col: Nombre de columna para eje Y
            category_col: Nombre de columna para categorías (opcional)
            **kwargs: Argumentos adicionales (colorMap, pointRadius, interactive, axes, etc.)
        
        Returns:
            dict: Especificación del scatter plot para usar en map()
        
        Ejemplo:
            import pandas as pd
            df = pd.DataFrame({'edad': [20, 30, 40], 'salario': [5000, 8000, 12000], 'dept': ['A', 'B', 'A']})
            
            MatrixLayout.map_scatter('S', df, x_col='edad', y_col='salario', category_col='dept', interactive=True)
            layout = MatrixLayout("S")
        """
        processed_data, original_data = cls._prepare_data(data, x_col=x_col, y_col=y_col, category_col=category_col, value_col=size_col)

        # Enriquecer con tamaño y color por punto si se especifican columnas
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if size_col and size_col in data.columns:
                for idx, row in data.iterrows():
                    if idx < len(processed_data):
                        try:
                            processed_data[idx]['size'] = float(row[size_col])
                        except Exception:
                            pass
            if color_col and color_col in data.columns:
                for idx, row in data.iterrows():
                    if idx < len(processed_data):
                        processed_data[idx]['color'] = row[color_col]
        else:
            # Lista de dicts
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    if idx < len(processed_data):
                        if size_col and size_col in item:
                            try:
                                processed_data[idx]['size'] = float(item.get(size_col))
                            except Exception:
                                pass
                        if color_col and color_col in item:
                            processed_data[idx]['color'] = item.get(color_col)
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs and y_col:
            kwargs['yLabel'] = y_col
        
        spec = {
            'type': 'scatter',
            'data': processed_data,
            **kwargs
        }
        
        # Actualizar el mapping
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        
        return spec
    
    @classmethod
    def map_barchart(cls, letter, data, category_col=None, value_col=None, **kwargs):
        """
        Método helper para crear bar chart desde DataFrame de pandas.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            category_col: Nombre de columna para categorías
            value_col: Nombre de columna para valores (opcional, si no se especifica cuenta)
            **kwargs: Argumentos adicionales (color, colorMap, interactive, axes, etc.)
        
        Returns:
            dict: Especificación del bar chart para usar en map()
        
        Ejemplo:
            import pandas as pd
            df = pd.DataFrame({'dept': ['A', 'B', 'C'], 'ventas': [100, 200, 150]})
            
            MatrixLayout.map_barchart('B', df, category_col='dept', value_col='ventas', interactive=True)
            layout = MatrixLayout("B")
        """
        from collections import Counter
        
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            # Si hay value_col, agrupar y sumar
            if value_col and value_col in data.columns:
                bar_data = data.groupby(category_col)[value_col].sum().reset_index()
                bar_data = bar_data.rename(columns={category_col: 'category', value_col: 'value'})
                bar_data = bar_data.to_dict('records')
            elif category_col and category_col in data.columns:
                # Contar por categoría
                counts = data[category_col].value_counts()
                bar_data = [{'category': cat, 'value': count} for cat, count in counts.items()]
            else:
                raise ValueError("Debe especificar category_col")
            
            # Agregar datos originales para referencia
            original_data = data.to_dict('records')
            for i, bar_item in enumerate(bar_data):
                # Encontrar todas las filas con esta categoría
                matching_rows = [row for row in original_data if row.get(category_col) == bar_item['category']]
                bar_item['_original_rows'] = matching_rows
        else:
            # Lista de diccionarios
            if category_col:
                categories = Counter([item.get(category_col, 'unknown') for item in data])
                bar_data = [{'category': cat, 'value': count} for cat, count in categories.items()]
            else:
                categories = Counter([item.get('category', 'unknown') for item in data])
                bar_data = [{'category': cat, 'value': count} for cat, count in categories.items()]
            
            # Agregar datos originales
            original_data = data if isinstance(data, list) else []
            for bar_item in bar_data:
                matching_rows = [row for row in original_data if row.get(category_col or 'category') == bar_item['category']]
                bar_item['_original_rows'] = matching_rows
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and category_col:
            kwargs['xLabel'] = category_col
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = value_col if value_col else 'Count'
        
        spec = {
            'type': 'bar',
            'data': bar_data,
            **kwargs
        }
        
        # Actualizar el mapping
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        
        return spec

    @classmethod
    def map_grouped_barchart(cls, letter, data, main_col=None, sub_col=None, value_col=None, **kwargs):
        """
        Crea barplot anidado: categorías principales (main_col) con subcategorías (sub_col).
        Estructura: {
          type: 'bar', grouped: True,
          groups: [mainCat1, mainCat2, ...],
          series: [sub1, sub2, ...],
          data: [{ group: mainCat, series: sub, value: v }, ...]
        }
        """
        if main_col is None or sub_col is None:
            raise ValueError("Se requieren main_col y sub_col para grouped barplot")
        rows = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if value_col and value_col in data.columns:
                agg = data.groupby([main_col, sub_col])[value_col].sum().reset_index()
                for _, r in agg.iterrows():
                    rows.append({'group': r[main_col], 'series': r[sub_col], 'value': float(r[value_col])})
            else:
                # contar ocurrencias por combinación
                counts = data.groupby([main_col, sub_col]).size().reset_index(name='value')
                for _, r in counts.iterrows():
                    rows.append({'group': r[main_col], 'series': r[sub_col], 'value': float(r['value'])})
            groups = agg[main_col].unique().tolist() if 'agg' in locals() else counts[main_col].unique().tolist()
            series = agg[sub_col].unique().tolist() if 'agg' in locals() else counts[sub_col].unique().tolist()
        else:
            # lista de dicts
            from collections import defaultdict
            if not isinstance(data, list):
                raise ValueError("Datos inválidos para grouped barplot")
            if value_col:
                sums = defaultdict(lambda: defaultdict(float))
                for it in data:
                    g = it.get(main_col, 'unknown')
                    s = it.get(sub_col, 'unknown')
                    sums[g][s] += float(it.get(value_col, 0))
                for g, submap in sums.items():
                    for s, v in submap.items():
                        rows.append({'group': g, 'series': s, 'value': float(v)})
            else:
                counts = defaultdict(lambda: defaultdict(int))
                for it in data:
                    g = it.get(main_col, 'unknown')
                    s = it.get(sub_col, 'unknown')
                    counts[g][s] += 1
                for g, submap in counts.items():
                    for s, v in submap.items():
                        rows.append({'group': g, 'series': s, 'value': int(v)})
            groups = sorted(list({r['group'] for r in rows}))
            series = sorted(list({r['series'] for r in rows}))
        spec = {
            'type': 'bar',
            'grouped': True,
            'groups': groups,
            'series': series,
            'data': rows,
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_histogram(cls, letter, data, value_col=None, bins=10, **kwargs):
        """
        Método helper para crear histograma desde DataFrame o lista de dicts.
        
        Args:
            letter: Letra del layout ASCII donde irá el gráfico
            data: DataFrame de pandas o lista de diccionarios
            value_col: Columna numérica a binnear (requerida si data es DataFrame)
            bins: Número de bins (int) o secuencia de bordes
            **kwargs: color, axes, etc.
        """
        import math
        import itertools
        values = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if not value_col or value_col not in data.columns:
                raise ValueError("Debe especificar value_col para histograma con DataFrame")
            # Extraer valores numéricos limpiando NaN
            series = data[value_col].dropna()
            try:
                values = series.astype(float).tolist()
            except Exception:
                values = [float(v) for v in series.tolist()]
        else:
            # Lista de diccionarios
            if not isinstance(data, list):
                raise ValueError("Datos inválidos para histograma: se requiere DataFrame o lista de dicts")
            col = value_col or 'value'
            for item in data:
                v = item.get(col)
                if v is not None:
                    try:
                        values.append(float(v))
                    except Exception:
                        continue
        if not values:
            hist_data = []
        else:
            vmin = min(values)
            vmax = max(values)
            if isinstance(bins, int):
                if bins <= 0:
                    bins = 10
                step = (vmax - vmin) / bins if vmax > vmin else 1.0
                edges = [vmin + i * step for i in range(bins + 1)]
            else:
                edges = list(bins)
                edges.sort()
            counts = [0] * (len(edges) - 1)
            for v in values:
                # Asignar bin; incluir borde derecho en el último bin
                idx = None
                for i in range(len(edges) - 1):
                    left, right = edges[i], edges[i + 1]
                    if (v >= left and v < right) or (i == len(edges) - 2 and v == right):
                        idx = i
                        break
                if idx is not None:
                    counts[idx] += 1
            # Centro del bin para etiqueta; D3 usa 'bin' y 'count'
            hist_data = [
                {
                    'bin': float((edges[i] + edges[i + 1]) / 2.0),
                    'count': int(counts[i])
                }
                for i in range(len(counts))
            ]
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and value_col:
            kwargs['xLabel'] = value_col
        if 'yLabel' not in kwargs:
            kwargs['yLabel'] = 'Frequency'
        
        spec = {
            'type': 'histogram',
            'data': hist_data,
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_boxplot(cls, letter, data, category_col=None, value_col=None, **kwargs):
        """
        Método helper para crear boxplot por categoría.
        
        Args:
            letter: Letra del layout ASCII
            data: DataFrame o lista de diccionarios
            category_col: Columna categórica (opcional; si None, usa una sola categoría)
            value_col: Columna numérica para calcular cuantiles (requerida con DataFrame)
            **kwargs: color, axes, etc.
        """
        import statistics
        def five_num_summary(values_list):
            vals = sorted([float(v) for v in values_list if v is not None])
            if not vals:
                return None
            n = len(vals)
            median = statistics.median(vals)
            # Cuartiles usando método mediana-excluida
            if n < 4:
                q1 = vals[max(0, (n//4) - 1)] if n > 1 else vals[0]
                q3 = vals[min(n-1, (3*n)//4)] if n > 1 else vals[-1]
            else:
                mid = n // 2
                lower = vals[:mid]
                upper = vals[mid+1:] if n % 2 == 1 else vals[mid:]
                q1 = statistics.median(lower) if lower else vals[0]
                q3 = statistics.median(upper) if upper else vals[-1]
            iqr = q3 - q1
            lower_whisker = max(min(vals), q1 - 1.5 * iqr)
            upper_whisker = min(max(vals), q3 + 1.5 * iqr)
            return {
                'lower': float(lower_whisker),
                'q1': float(q1),
                'median': float(median),
                'q3': float(q3),
                'upper': float(upper_whisker)
            }
        box_data = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if value_col is None or value_col not in data.columns:
                raise ValueError("Debe especificar value_col para boxplot con DataFrame")
            if category_col and category_col in data.columns:
                grouped = data.groupby(category_col)
                for cat, subdf in grouped:
                    summary = five_num_summary(subdf[value_col].dropna().tolist())
                    if summary:
                        box_data.append({'category': cat, **summary})
            else:
                summary = five_num_summary(data[value_col].dropna().tolist())
                if summary:
                    box_data.append({'category': 'All', **summary})
        else:
            # Lista de diccionarios
            if not isinstance(data, list):
                raise ValueError("Datos inválidos para boxplot: se requiere DataFrame o lista de dicts")
            val_key = value_col or 'value'
            if category_col:
                from collections import defaultdict
                groups = defaultdict(list)
                for item in data:
                    groups[item.get(category_col, 'unknown')].append(item.get(val_key))
                for cat, vals in groups.items():
                    summary = five_num_summary(vals)
                    if summary:
                        box_data.append({'category': cat, **summary})
            else:
                summary = five_num_summary([item.get(val_key) for item in data])
                if summary:
                    box_data.append({'category': 'All', **summary})
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and category_col:
            kwargs['xLabel'] = category_col
        if 'yLabel' not in kwargs and value_col:
            kwargs['yLabel'] = value_col
        
        spec = {
            'type': 'boxplot',
            'data': box_data,
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_heatmap(cls, letter, data, x_col=None, y_col=None, value_col=None, **kwargs):
        """
        Crea heatmap a partir de DataFrame/lista: devuelve celdas {x,y,value}.
        """
        cells = []
        x_labels, y_labels = [], []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if value_col and x_col and y_col:
                # Tabla larga → celdas directas
                df = data[[x_col, y_col, value_col]].dropna()
                x_labels = df[x_col].astype(str).unique().tolist()
                y_labels = df[y_col].astype(str).unique().tolist()
                cells = [
                    {'x': str(r[x_col]), 'y': str(r[y_col]), 'value': float(r[value_col])}
                    for _, r in df.iterrows()
                ]
            else:
                raise ValueError("Especifique x_col, y_col y value_col para heatmap")
        else:
            # Lista de dicts
            if not isinstance(data, list):
                raise ValueError("Datos inválidos para heatmap")
            for item in data:
                if x_col in item and y_col in item and value_col in item:
                    cells.append({'x': str(item[x_col]), 'y': str(item[y_col]), 'value': float(item[value_col])})
                    x_labels.append(str(item[x_col]))
                    y_labels.append(str(item[y_col]))
            x_labels = sorted(list(set(x_labels)))
            y_labels = sorted(list(set(y_labels)))
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs and y_col:
            kwargs['yLabel'] = y_col
        
        spec = {
            'type': 'heatmap',
            'data': cells,
            'xLabels': x_labels,
            'yLabels': y_labels,
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_correlation_heatmap(cls, letter, data, **kwargs):
        """
        Calcula matriz de correlación (pearson) para columnas numéricas del DataFrame.
        """
        if not (HAS_PANDAS and isinstance(data, pd.DataFrame)):
            raise ValueError("map_correlation_heatmap requiere DataFrame de pandas")
        num_df = data.select_dtypes(include=['number'])
        if num_df.shape[1] == 0:
            raise ValueError("No hay columnas numéricas para correlación")
        corr = num_df.corr().fillna(0.0)
        cols = corr.columns.tolist()
        cells = []
        for i, xi in enumerate(cols):
            for j, yj in enumerate(cols):
                cells.append({'x': xi, 'y': yj, 'value': float(corr.iloc[j, i])})
        spec = {
            'type': 'heatmap',
            'data': cells,
            'xLabels': cols,
            'yLabels': cols,
            'isCorrelation': True,
            **kwargs
        }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_line(cls, letter, data, x_col=None, y_col=None, series_col=None, **kwargs):
        """
        Crea line chart. Si series_col está definido, múltiples series.
        """
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if x_col is None or y_col is None:
                raise ValueError("x_col e y_col son requeridos para line plot")
            df = data[[x_col, y_col] + ([series_col] if series_col else [])].dropna()
            if series_col:
                series_names = df[series_col].unique().tolist()
                series = {}
                for name in series_names:
                    sdf = df[df[series_col] == name].sort_values(by=x_col)
                    series[name] = [{ 'x': float(x), 'y': float(y), 'series': str(name) } for x, y in zip(sdf[x_col], sdf[y_col])]
                payload = {'series': series}
            else:
                sdf = df.sort_values(by=x_col)
                payload = {'series': { 'default': [{ 'x': float(x), 'y': float(y) } for x, y in zip(sdf[x_col], sdf[y_col])] }}
        else:
            # Lista de dicts
            items = [d for d in (data or []) if x_col in d and y_col in d]
            if series_col:
                series = {}
                for item in items:
                    key = str(item.get(series_col))
                    series.setdefault(key, []).append({'x': float(item[x_col]), 'y': float(item[y_col]), 'series': key})
                # ordenar por x
                for k in series:
                    series[k] = sorted(series[k], key=lambda p: p['x'])
                payload = {'series': series}
            else:
                pts = sorted([{'x': float(i[x_col]), 'y': float(i[y_col])} for i in items], key=lambda p: p['x'])
                payload = {'series': { 'default': pts }}
        
        # Agregar etiquetas de ejes automáticamente si no están en kwargs
        if 'xLabel' not in kwargs and x_col:
            kwargs['xLabel'] = x_col
        if 'yLabel' not in kwargs and y_col:
            kwargs['yLabel'] = y_col
        
        spec = { 'type': 'line', **payload, **kwargs }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_pie(cls, letter, data, category_col=None, value_col=None, **kwargs):
        """
        Crea pie/donut chart.
        """
        from collections import Counter, defaultdict
        slices = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if category_col is None:
                raise ValueError("category_col requerido para pie")
            if value_col and value_col in data.columns:
                agg = data.groupby(category_col)[value_col].sum().reset_index()
                slices = [{'category': r[category_col], 'value': float(r[value_col])} for _, r in agg.iterrows()]
            else:
                counts = data[category_col].value_counts()
                slices = [{'category': cat, 'value': int(cnt)} for cat, cnt in counts.items()]
        else:
            items = data or []
            if value_col:
                sums = defaultdict(float)
                for it in items:
                    sums[str(it.get(category_col, 'unknown'))] += float(it.get(value_col, 0))
                slices = [{'category': k, 'value': float(v)} for k, v in sums.items()]
            else:
                counts = Counter([str(it.get(category_col, 'unknown')) for it in items])
                slices = [{'category': k, 'value': int(v)} for k, v in counts.items()]
        spec = { 'type': 'pie', 'data': slices, **kwargs }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_violin(cls, letter, data, value_col=None, category_col=None, bins=20, **kwargs):
        """
        Crea datos para violin: para cada categoría, calcula histograma normalizado
        y retorna perfiles (x: bin, width: densidad) para render (aproximación).
        """
        if value_col is None:
            raise ValueError("value_col es requerido para violin")
        def build_profile(values):
            values = [float(v) for v in values if v is not None]
            if not values:
                return []
            try:
                import numpy as np
                hist, edges = np.histogram(values, bins=bins)
                dens = hist / (np.max(hist) if np.max(hist) > 0 else 1)
                centers = [(edges[i] + edges[i+1]) / 2 for i in range(len(edges)-1)]
                return [{'y': float(c), 'w': float(d)} for c, d in zip(centers, dens)]
            except Exception:
                mn, mx = min(values), max(values)
                step = (mx - mn) / bins if mx > mn else 1
                counts = [0]*bins
                edges = [mn + i*step for i in range(bins+1)]
                for v in values:
                    idx = min(int((v - mn)/step), bins-1) if step>0 else 0
                    counts[idx] += 1
                m = max(counts) or 1
                dens = [c/m for c in counts]
                centers = [(edges[i] + edges[i+1]) / 2 for i in range(bins)]
                return [{'y': float(c), 'w': float(d)} for c, d in zip(centers, dens)]
        violins = []
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            if category_col and category_col in data.columns:
                for cat, sub in data.groupby(category_col):
                    prof = build_profile(sub[value_col].dropna().tolist())
                    violins.append({'category': cat, 'profile': prof})
            else:
                prof = build_profile(data[value_col].dropna().tolist())
                violins.append({'category': 'All', 'profile': prof})
        else:
            items = data or []
            if category_col:
                from collections import defaultdict
                groups = defaultdict(list)
                for it in items:
                    groups[str(it.get(category_col, 'unknown'))].append(it.get(value_col))
                for cat, vals in groups.items():
                    violins.append({'category': cat, 'profile': build_profile(vals)})
            else:
                violins.append({'category': 'All', 'profile': build_profile([it.get(value_col) for it in items])})
        spec = { 'type': 'violin', 'data': violins, **kwargs }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec

    @classmethod
    def map_radviz(cls, letter, data, features=None, class_col=None, **kwargs):
        """
        Crea datos para RadViz simple: anclas uniformes y proyección ponderada.
        Retorna puntos {x,y,category} normalizados en [0,1].
        """
        if not (HAS_PANDAS and isinstance(data, pd.DataFrame)):
            raise ValueError("map_radviz requiere DataFrame")
        import math
        df = data.copy()
        feats = features or df.select_dtypes(include=['number']).columns.tolist()
        if len(feats) < 2:
            raise ValueError("Se requieren al menos 2 features para RadViz")
        # normalizar 0-1
        for c in feats:
            col = df[c].astype(float)
            mn, mx = col.min(), col.max()
            if mx > mn:
                df[c] = (col - mn) / (mx - mn)
            else:
                df[c] = 0.5
        k = len(feats)
        anchors = []
        for i in range(k):
            ang = 2*math.pi * i / k
            anchors.append((math.cos(ang), math.sin(ang)))
        points = []
        for _, row in df.iterrows():
            weights = [row[c] for c in feats]
            s = sum(weights) or 1.0
            x = sum(w * anchors[i][0] for i, w in enumerate(weights)) / s
            y = sum(w * anchors[i][1] for i, w in enumerate(weights)) / s
            points.append({'x': float(x), 'y': float(y), 'category': str(row[class_col]) if class_col and class_col in df.columns else None})
        spec = { 'type': 'radviz', 'data': points, 'features': feats, **kwargs }
        if not hasattr(cls, '_map') or cls._map is None:
            cls._map = {}
        cls._map[letter] = spec
        return spec
    @classmethod
    def set_safe_html(cls, safe: bool):
        cls._safe_html = bool(safe)
    
    @classmethod
    def get_status(cls):
        """Retorna el estado actual del sistema de comunicación."""
        active_instances = {
            div_id: ref() is not None 
            for div_id, ref in cls._instances.items()
        }
        
        return {
            "comm_registered": cls._comm_registered,
            "debug_mode": cls._debug,
            "active_instances": sum(active_instances.values()),
            "total_instances": len(cls._instances),
            "instance_ids": list(cls._instances.keys()),
            "global_handlers": list(cls._global_handlers.keys()),
        }

    def __init__(self, ascii_layout=None):
        """
        Crea una nueva instancia de MatrixLayout.
        
        Args:
            ascii_layout (str, optional): Layout ASCII. Si no se proporciona, se genera uno simple.
        """
        # Si no se proporciona layout, crear uno simple
        if ascii_layout is None:
            ascii_layout = "A"
        
        self.ascii_layout = ascii_layout
        self.div_id = "matrix-" + str(uuid.uuid4())
        MatrixLayout._instances[self.div_id] = weakref.ref(self)
        self._handlers = {}
        self._reactive_model = None  # Para modelo reactivo
        self._merge_opt = None  # Merge explícito por instancia (True | False | [letras])
        
        # Asegurar que el comm esté registrado
        MatrixLayout._ensure_comm_target()
    
    def connect_selection(self, reactive_model, scatter_letter=None):
        """
        Conecta un modelo reactivo para actualizar automáticamente.
        
        Args:
            reactive_model: Instancia de ReactiveData o SelectionModel
            scatter_letter: Letra del scatter plot (opcional, para enrutamiento específico)
        
        Ejemplo:
            from BESTLIB.reactive import SelectionModel
            
            selection = SelectionModel()
            selection.on_change(lambda items, count: print(f"{count} seleccionados"))
            
            layout = MatrixLayout("S")
            layout.connect_selection(selection, scatter_letter='S')
            layout.display()
        """
        if not HAS_WIDGETS:
            print("⚠️ ipywidgets no está instalado. Instala con: pip install ipywidgets")
            return
        
        self._reactive_model = reactive_model
        self._scatter_letter = scatter_letter  # Guardar letra del scatter para enrutamiento
        
        # Crear handler que actualiza el modelo reactivo
        def update_model(payload):
            # Verificar si el evento viene del scatter plot correcto
            event_scatter_letter = payload.get('__scatter_letter__')
            if scatter_letter and event_scatter_letter and event_scatter_letter != scatter_letter:
                # Este evento no es para este scatter plot
                return
            
            items = payload.get('items', [])
            # Extraer filas originales completas si existen
            original_rows = []
            for item in items:
                if '_original_row' in item:
                    original_rows.append(item['_original_row'])
                else:
                    # Si no hay _original_row, usar el item completo
                    original_rows.append(item)
            reactive_model.update(original_rows)
        
        # Registrar el handler
        self.on('select', update_model)
        
        return self
    
    def __del__(self):
        """Limpia la referencia cuando se destruye la instancia"""
        if hasattr(self, 'div_id') and self.div_id in MatrixLayout._instances:
            del MatrixLayout._instances[self.div_id]

    def _repr_html_(self):
        # Cargar JS y CSS desde el mismo paquete
        js_path = os.path.join(os.path.dirname(__file__), "matrix.js")
        css_path = os.path.join(os.path.dirname(__file__), "style.css")

        with open(js_path, "r", encoding="utf-8") as f:
            js_code = f.read()

        with open(css_path, "r", encoding="utf-8") as f:
            css_code = f.read()

        # Validar layout ASCII: mismas columnas por fila
        rows = [r for r in self.ascii_layout.strip().split("\n") if r]
        if not rows:
            raise ValueError("ascii_layout no puede estar vacío")
        col_len = len(rows[0])
        if any(len(r) != col_len for r in rows):
            raise ValueError("Todas las filas del ascii_layout deben tener igual longitud")

        # Escapar backticks para no romper el template literal JS
        escaped_layout = self.ascii_layout.replace("`", "\\`")

        # Pasar metadata al JS
        meta = {
            "__safe_html__": bool(self._safe_html),
            "__div_id__": self.div_id
        }
        # Si hay merge explícito por instancia, sobreescribir en el mapping
        mapping_merged = {**self._map, **meta}
        if self._merge_opt is not None:
            mapping_merged["__merge__"] = self._merge_opt

        mapping_js = json.dumps(_sanitize_for_json(mapping_merged))

        # Render HTML con contenedor + CSS + JS inline (compatible con Notebook clásico)
        html = f"""
        <style>{css_code}</style>
        <div id="{self.div_id}" class="matrix-layout"></div>
        <script>
        {js_code}
        render("{self.div_id}", `{escaped_layout}`, {mapping_js});
        </script>
        """
        return html

    def _repr_mimebundle_(self, include=None, exclude=None):
        # Asegurar que el comm target está registrado
        MatrixLayout._ensure_comm_target()
        
        # Cargar JS y CSS desde el mismo paquete
        js_path = os.path.join(os.path.dirname(__file__), "matrix.js")
        css_path = os.path.join(os.path.dirname(__file__), "style.css")

        with open(js_path, "r", encoding="utf-8") as f:
            js_code = f.read()

        with open(css_path, "r", encoding="utf-8") as f:
            css_code = f.read()

        rows = [r for r in self.ascii_layout.strip().split("\n") if r]
        if not rows:
            raise ValueError("ascii_layout no puede estar vacío")
        col_len = len(rows[0])
        if any(len(r) != col_len for r in rows):
            raise ValueError("Todas las filas del ascii_layout deben tener igual longitud")

        escaped_layout = self.ascii_layout.replace("`", "\\`")

        html = f"""
        <style>{css_code}</style>
        <div id="{self.div_id}" class="matrix-layout"></div>
        """
        
        # Pasar div_id y safe_html al JS
        meta = {
            "__safe_html__": bool(self._safe_html),
            "__div_id__": self.div_id
        }
        mapping_merged = {**self._map, **meta}
        if self._merge_opt is not None:
            mapping_merged["__merge__"] = self._merge_opt
        mapping_js = json.dumps(_sanitize_for_json(mapping_merged))

        js = (
            js_code
            + "\n"
            + f'render("{self.div_id}", `{escaped_layout}`, {mapping_js});'
        )

        return {
            "text/html": html,
            "application/javascript": js,
        }
    
    def display(self, ascii_layout=None):
        """
        Muestra el layout usando IPython.display.
        
        Args:
            ascii_layout (str, optional): Layout ASCII a usar. Si no se proporciona, usa self.ascii_layout.
        """
        try:
            from IPython.display import display, HTML, Javascript
            
            MatrixLayout._ensure_comm_target()
            
            # Usar el layout proporcionado o el de la instancia
            layout_to_use = ascii_layout if ascii_layout is not None else self.ascii_layout
            
            js_path = os.path.join(os.path.dirname(__file__), "matrix.js")
            css_path = os.path.join(os.path.dirname(__file__), "style.css")
            
            with open(js_path, "r", encoding="utf-8") as f:
                js_code = f.read()
            
            with open(css_path, "r", encoding="utf-8") as f:
                css_code = f.read()
            
            rows = [r for r in layout_to_use.strip().split("\n") if r]
            if not rows:
                raise ValueError("ascii_layout no puede estar vacío")
            
            escaped_layout = layout_to_use.replace("`", "\\`")
            
            meta = {
                "__safe_html__": bool(self._safe_html),
                "__div_id__": self.div_id
            }
            mapping_merged = {**self._map, **meta}
            if self._merge_opt is not None:
                mapping_merged["__merge__"] = self._merge_opt
            mapping_js = json.dumps(_sanitize_for_json(mapping_merged))
            
            html_content = f"""
            <style>{css_code}</style>
            <div id="{self.div_id}" class="matrix-layout"></div>
            """
            
            js_content = f"""
            (function() {{
                function ensureD3() {{
                    if (window.d3) return Promise.resolve(window.d3);
                    
                    return new Promise((resolve, reject) => {{
                        const script = document.createElement('script');
                        script.src = 'https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js';
                        script.onload = () => {{
                            if (window.d3) resolve(window.d3);
                            else reject(new Error('D3 no se cargó'));
                        }};
                        script.onerror = () => reject(new Error('Error al cargar D3'));
                        document.head.appendChild(script);
                    }});
                }}
                
                ensureD3().then(d3 => {{
                    {js_code}
                    render("{self.div_id}", `{escaped_layout}`, {mapping_js});
                }}).catch(e => {{
                    const errorDiv = document.getElementById("{self.div_id}");
                    if (errorDiv) {{
                        errorDiv.innerHTML = '<div style="color: #e74c3c; padding: 20px; border: 2px solid #e74c3c; border-radius: 5px;">' +
                            '<strong>❌ Error:</strong> ' + e.message + '</div>';
                    }}
                }});
            }})();
            """
            
            display(HTML(html_content))
            display(Javascript(js_content))
            
        except Exception as e:
            print(f"❌ Error: {e}")

    # ==========================
    # API de Merge por Instancia
    # ==========================
    def merge(self, letters=True):
        """Configura merge explícito para este layout.

        Args:
            letters: True para todas las letras, False para desactivar, o lista de letras ["A", "B"].
        """
        self._merge_opt = letters
        return self

    def merge_all(self):
        """Activa merge para todas las letras (equivalente a merge(True))."""
        self._merge_opt = True
        return self

    def merge_off(self):
        """Desactiva merge (equivalente a merge(False))."""
        self._merge_opt = False
        return self

    def merge_only(self, letters):
        """Activa merge solo para las letras indicadas (equivalente a merge([...]))."""
        self._merge_opt = list(letters) if letters is not None else []
        return self


# ==========================
# Utilidades
# ==========================
def _sanitize_for_json(obj):
    """Convierte recursivamente tipos numpy y no serializables a tipos JSON puros."""
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
    # Fallback a string para objetos desconocidos
    return str(obj)
