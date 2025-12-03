"""
Preparadores de datos para diferentes tipos de gráficos
"""
from .validators import validate_scatter_data, validate_bar_data, validate_data_structure
from ..core.exceptions import DataError
from ._imports import ensure_pandas
from datetime import datetime

pd = ensure_pandas()
HAS_PANDAS = pd is not None


def _safe_to_number(value):
    """
    Convierte un valor a número de forma segura, manejando Timestamps, datetimes y otros tipos.
    
    Args:
        value: Valor a convertir (puede ser int, float, Timestamp, datetime, string numérico, etc.)
    
    Returns:
        float: Valor convertido a número
    
    Raises:
        ValueError: Si el valor no se puede convertir a número
    """
    if value is None:
        raise ValueError("Cannot convert None to number")
    
    # Si ya es un número, retornarlo directamente
    if isinstance(value, (int, float)):
        return float(value)
    
    # Manejar Timestamps de pandas
    if HAS_PANDAS:
        import pandas as pd
        if isinstance(value, pd.Timestamp):
            return float(value.timestamp())
        if isinstance(value, pd.Period):
            return float(value.to_timestamp().timestamp())
        if pd.isna(value):
            raise ValueError("Cannot convert NaN/NaT to number")
    
    # Manejar datetime estándar de Python
    if isinstance(value, datetime):
        return float(value.timestamp())
    
    # Manejar numpy datetime64 si está disponible
    try:
        import numpy as np
        if isinstance(value, (np.datetime64, np.timedelta64)):
            # Convertir a timestamp (segundos desde epoch)
            return float(pd.Timestamp(value).timestamp()) if HAS_PANDAS else float(value.astype('datetime64[s]').astype('float64'))
    except (ImportError, AttributeError):
        pass
    
    # Intentar convertir string a float
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            # Intentar parsear como fecha
            if HAS_PANDAS:
                try:
                    return float(pd.to_datetime(value).timestamp())
                except:
                    pass
    
    # Intentar conversión genérica
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Cannot convert {type(value).__name__} '{value}' to number: {e}")


def prepare_scatter_data(data, x_col=None, y_col=None, category_col=None, size_col=None, color_col=None):
    """
    Prepara datos para scatter plot.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        x_col: Nombre de columna para eje X
        y_col: Nombre de columna para eje Y
        category_col: Nombre de columna para categorías (opcional)
        size_col: Nombre de columna para tamaño (opcional)
        color_col: Nombre de columna para color (opcional)
    
    Returns:
        tuple: (datos_procesados, datos_originales)
    """
    # Validar datos
    if x_col and y_col:
        if HAS_PANDAS and isinstance(data, pd.DataFrame):
            validate_scatter_data(data, x_col, y_col)
        else:
            validate_scatter_data(data, x_col, y_col)
    
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        original_data = data.to_dict('records')
        df_work = pd.DataFrame(index=data.index)
        
        # Mapear columnas según especificación (vectorizado)
        if x_col and x_col in data.columns:
            df_work['x'] = data[x_col]
        elif 'x' in data.columns:
            df_work['x'] = data['x']
        
        if y_col and y_col in data.columns:
            df_work['y'] = data[y_col]
        elif 'y' in data.columns:
            df_work['y'] = data['y']
        
        if category_col and category_col in data.columns:
            df_work['category'] = data[category_col]
        elif 'category' in data.columns:
            df_work['category'] = data['category']
        
        if size_col and size_col in data.columns:
            df_work['size'] = data[size_col]
        if color_col and color_col in data.columns:
            df_work['color'] = data[color_col]
        
        processed_data = df_work.to_dict('records')
        
        # Agregar referencias a filas originales e índices
        for idx, item in enumerate(processed_data):
            item['_original_row'] = original_data[idx]
            item['_original_index'] = int(data.index[idx])
        
        return processed_data, original_data
    else:
        if isinstance(data, list):
            processed_data = []
            for idx, item in enumerate(data):
                processed_item = item.copy()
                if '_original_row' not in processed_item:
                    processed_item['_original_row'] = item
                if '_original_index' not in processed_item:
                    processed_item['_original_index'] = idx
                processed_data.append(processed_item)
            return processed_data, data
        else:
            raise DataError("Los datos deben ser un DataFrame de pandas o una lista de diccionarios")


def prepare_bar_data(data, category_col=None, value_col=None):
    """
    Prepara datos para bar chart.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        category_col: Nombre de columna para categorías
        value_col: Nombre de columna para valores (opcional)
    
    Returns:
        list: Datos preparados para bar chart
    """
    from collections import Counter
    
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        if value_col and value_col in data.columns:
            bar_data = data.groupby(category_col)[value_col].sum().reset_index()
            bar_data = bar_data.rename(columns={category_col: 'category', value_col: 'value'})
            bar_data = bar_data.to_dict('records')
        elif category_col and category_col in data.columns:
            counts = data[category_col].value_counts()
            bar_data = [{'category': cat, 'value': count} for cat, count in counts.items()]
        else:
            raise DataError("Debe especificar category_col")
        
        # Agregar datos originales para referencia
        original_data = data.to_dict('records')
        for i, bar_item in enumerate(bar_data):
            matching_rows = [row for row in original_data if row.get(category_col) == bar_item['category']]
            bar_item['_original_rows'] = matching_rows
        
        return bar_data
    else:
        if isinstance(data, list):
            if value_col:
                from collections import defaultdict
                sums = defaultdict(float)
                for item in data:
                    cat = item.get(category_col, 'unknown')
                    val = item.get(value_col, 0)
                    sums[cat] += val
                categories = dict(sums)
            else:
                categories = Counter([item.get(category_col, 'unknown') for item in data])
            
            bar_data = [
                {'category': cat, 'value': count}
                for cat, count in categories.items()
            ]
            
            # Agregar datos originales
            for bar_item in bar_data:
                matching_rows = [row for row in data if row.get(category_col or 'category') == bar_item['category']]
                bar_item['_original_rows'] = matching_rows
            
            return bar_data
        else:
            raise DataError("Los datos deben ser un DataFrame de pandas o una lista de diccionarios")


def prepare_histogram_data(data, value_col=None, bins=10):
    """
    Prepara datos para histograma.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        value_col: Columna numérica a binnear
        bins: Número de bins
    
    Returns:
        list: Datos preparados para histograma con _original_rows por bin
    """
    import math
    
    values = []
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        if not value_col or value_col not in data.columns:
            raise DataError("Debe especificar value_col para histograma con DataFrame")
        series = data[value_col].dropna()
        try:
            values = series.astype(float).tolist()
        except Exception:
            values = [float(v) for v in series.tolist()]
    else:
        if not isinstance(data, list):
            raise DataError("Datos inválidos para histograma")
        col = value_col or 'value'
        for item in data:
            v = item.get(col)
            if v is not None:
                try:
                    values.append(float(v))
                except Exception:
                    continue
    
    if not values:
        return []
    
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
    
    # Almacenar filas originales para cada bin
    bin_rows = [[] for _ in range(len(edges) - 1)]
    
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        original_data = data.to_dict('records')
        for row in original_data:
            v = row.get(value_col)
            if v is not None:
                try:
                    v_float = float(v)
                    idx = None
                    for i in range(len(edges) - 1):
                        left, right = edges[i], edges[i + 1]
                        if (v_float >= left and v_float < right) or (i == len(edges) - 2 and v_float == right):
                            idx = i
                            break
                    if idx is not None:
                        bin_rows[idx].append(row)
                except Exception:
                    continue
    else:
        items = data if isinstance(data, list) else []
        for item in items:
            v = item.get(value_col or 'value')
            if v is not None:
                try:
                    v_float = float(v)
                    idx = None
                    for i in range(len(edges) - 1):
                        left, right = edges[i], edges[i + 1]
                        if (v_float >= left and v_float < right) or (i == len(edges) - 2 and v_float == right):
                            idx = i
                            break
                    if idx is not None:
                        bin_rows[idx].append(item)
                except Exception:
                    continue
    
    hist_data = [
        {
            'bin': float((edges[i] + edges[i + 1]) / 2.0),
            'count': int(len(bin_rows[i])),
            '_original_rows': bin_rows[i]
        }
        for i in range(len(bin_rows))
    ]
    
    return hist_data


def prepare_boxplot_data(data, category_col=None, value_col=None):
    """
    Prepara datos para boxplot.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        category_col: Columna categórica (opcional)
        value_col: Columna numérica para calcular cuantiles
    
    Returns:
        list: Datos preparados para boxplot
    """
    import statistics
    
    def five_num_summary(values_list):
        vals = sorted([float(v) for v in values_list if v is not None])
        if not vals:
            return None
        n = len(vals)
        median = statistics.median(vals)
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
            raise DataError("Debe especificar value_col para boxplot con DataFrame")
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
        if not isinstance(data, list):
            raise DataError("Datos inválidos para boxplot")
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
    
    return box_data


def prepare_heatmap_data(data, x_col=None, y_col=None, value_col=None):
    """
    Prepara datos para heatmap.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        x_col: Columna para eje X
        y_col: Columna para eje Y
        value_col: Columna para valores
    
    Returns:
        tuple: (cells, x_labels, y_labels)
    """
    cells = []
    x_labels, y_labels = [], []
    
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        if value_col and x_col and y_col:
            # Mantener todas las columnas originales para poder reconstruir filas completas
            df = data[[x_col, y_col, value_col]].dropna()
            x_labels = df[x_col].astype(str).unique().tolist()
            y_labels = df[y_col].astype(str).unique().tolist()
            for idx, r in df.iterrows():
                # Recuperar la fila original completa (todas las columnas)
                try:
                    original_row = data.loc[idx].to_dict()
                except Exception:
                    original_row = {x_col: r[x_col], y_col: r[y_col], value_col: r[value_col]}
                cells.append({
                    'x': str(r[x_col]),
                    'y': str(r[y_col]),
                    'value': float(r[value_col]),
                    '_original_row': original_row
                })
        elif x_col is None and y_col is None and value_col is None:
            # Matriz: usar índices y columnas automáticamente
            index_list = data.index.tolist()
            cols_list = data.columns.tolist()
            
            if len(index_list) == len(cols_list) and set(index_list) == set(cols_list):
                cols = sorted(cols_list)
                x_labels = cols
                y_labels = cols
                for i, xi in enumerate(cols):
                    for j, yj in enumerate(cols):
                        val = data.loc[yj, xi]
                        if pd.notna(val):
                            cells.append({'x': str(xi), 'y': str(yj), 'value': float(val)})
            else:
                x_labels = cols_list
                y_labels = index_list
                for i, y_val in enumerate(data.index):
                    for j, x_val in enumerate(data.columns):
                        val = data.iloc[i, j]
                        if pd.notna(val):
                            cells.append({'x': str(x_val), 'y': str(y_val), 'value': float(val)})
        else:
            raise DataError("Especifique x_col, y_col y value_col para heatmap, o pase una matriz sin especificar columnas")
    else:
        if not isinstance(data, list):
            raise DataError("Datos inválidos para heatmap")
        for item in data:
            if x_col in item and y_col in item and value_col in item:
                # Conservar la fila original completa para selección
                original_row = item.copy()
                cells.append({
                    'x': str(item[x_col]),
                    'y': str(item[y_col]),
                    'value': float(item[value_col]),
                    '_original_row': original_row
                })
                x_labels.append(str(item[x_col]))
                y_labels.append(str(item[y_col]))
        x_labels = sorted(list(set(x_labels)))
        y_labels = sorted(list(set(y_labels)))
    
    return cells, x_labels, y_labels


def prepare_line_data(data, x_col=None, y_col=None, series_col=None):
    """
    Prepara datos para line chart.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        x_col: Columna para eje X (soporta valores numéricos y temporales como Timestamp, datetime)
        y_col: Columna para eje Y
        series_col: Columna para series (opcional)
    
    Returns:
        dict: Datos preparados con 'series'
    
    Note:
        Los valores de x_col que sean Timestamps, datetimes u otros tipos temporales
        serán convertidos automáticamente a timestamps numéricos (segundos desde epoch).
    """
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        if x_col is None or y_col is None:
            raise DataError("x_col e y_col son requeridos para line plot")
        df = data[[x_col, y_col] + ([series_col] if series_col else [])].dropna()
        if series_col:
            series_names = df[series_col].unique().tolist()
            series = {}
            for name in series_names:
                sdf = df[df[series_col] == name].sort_values(by=x_col)
                series[name] = [{'x': _safe_to_number(x), 'y': _safe_to_number(y), 'series': str(name)} for x, y in zip(sdf[x_col], sdf[y_col])]
            return {'series': series}
        else:
            sdf = df.sort_values(by=x_col)
            return {'series': {'default': [{'x': _safe_to_number(x), 'y': _safe_to_number(y)} for x, y in zip(sdf[x_col], sdf[y_col])]}}
    else:
        items = [d for d in (data or []) if x_col in d and y_col in d]
        if series_col:
            series = {}
            for item in items:
                key = str(item.get(series_col))
                series.setdefault(key, []).append({'x': _safe_to_number(item[x_col]), 'y': _safe_to_number(item[y_col]), 'series': key})
            for k in series:
                series[k] = sorted(series[k], key=lambda p: p['x'])
            return {'series': series}
        else:
            pts = sorted([{'x': _safe_to_number(i[x_col]), 'y': _safe_to_number(i[y_col])} for i in items], key=lambda p: p['x'])
            return {'series': {'default': pts}}


def prepare_pie_data(data, category_col=None, value_col=None):
    """
    Prepara datos para pie chart.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        category_col: Columna categórica
        value_col: Columna numérica (opcional)
    
    Returns:
        list: Datos preparados para pie chart con _original_rows
    """
    from collections import Counter, defaultdict
    
    slices = []
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        if category_col is None:
            raise DataError("category_col requerido para pie")
        
        original_data = data.to_dict('records')
        category_rows = defaultdict(list)
        
        for row in original_data:
            cat = row.get(category_col)
            if cat is not None:
                category_rows[str(cat)].append(row)
        
        if value_col and value_col in data.columns:
            agg = data.groupby(category_col)[value_col].sum().reset_index()
            slices = [
                {
                    'category': str(r[category_col]),
                    'value': float(r[value_col]),
                    '_original_rows': category_rows.get(str(r[category_col]), [])
                }
                for _, r in agg.iterrows()
            ]
        else:
            counts = data[category_col].value_counts()
            slices = [
                {
                    'category': str(cat),
                    'value': int(cnt),
                    '_original_rows': category_rows.get(str(cat), [])
                }
                for cat, cnt in counts.items()
            ]
    else:
        items = data or []
        category_rows = defaultdict(list)
        
        for it in items:
            cat = it.get(category_col, 'unknown')
            if cat is not None:
                category_rows[str(cat)].append(it)
        
        if value_col:
            sums = defaultdict(float)
            for it in items:
                cat = str(it.get(category_col, 'unknown'))
                val = it.get(value_col, 0)
                try:
                    sums[cat] += float(val)
                except Exception:
                    pass
            slices = [
                {
                    'category': k,
                    'value': float(v),
                    '_original_rows': category_rows.get(k, [])
                }
                for k, v in sums.items()
            ]
        else:
            counts = Counter([str(it.get(category_col, 'unknown')) for it in items])
            slices = [
                {
                    'category': k,
                    'value': int(v),
                    '_original_rows': category_rows.get(k, [])
                }
                for k, v in counts.items()
            ]
    
    return slices


def prepare_grouped_bar_data(data, main_col=None, sub_col=None, value_col=None):
    """
    Prepara datos para grouped bar chart.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        main_col: Columna principal (categorías en eje X)
        sub_col: Columna de sub-grupos (series/barras agrupadas)
        value_col: Columna de valores (opcional, si no se especifica cuenta ocurrencias)
    
    Returns:
        tuple: (rows, groups, series)
            - rows: lista de categorías principales (eje X)
            - groups: lista de sub-categorías (series)
            - series: lista de listas, cada una con valores para cada grupo
    """
    from collections import defaultdict
    
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        if value_col and value_col in data.columns:
            # Sumar valores
            agg = data.groupby([main_col, sub_col])[value_col].sum().reset_index()
        else:
            # Contar ocurrencias
            agg = data.groupby([main_col, sub_col]).size().reset_index(name='value')
            value_col = 'value'
        
        # Obtener categorías únicas
        rows = agg[main_col].unique().tolist()
        groups = agg[sub_col].unique().tolist()
        
        # Crear matriz de valores: series[group_idx][row_idx]
        series = []
        for group in groups:
            group_values = []
            for row in rows:
                # Buscar el valor para esta combinación row+group
                mask = (agg[main_col] == row) & (agg[sub_col] == group)
                values = agg[mask][value_col].values
                value = float(values[0]) if len(values) > 0 else 0.0
                group_values.append(value)
            series.append(group_values)
    else:
        # Caso lista de diccionarios
        if not isinstance(data, list):
            raise DataError("Datos inválidos para grouped barplot")
        
        # Acumular valores
        value_map = defaultdict(lambda: defaultdict(float))
        for item in data:
            row_key = item.get(main_col, 'unknown')
            group_key = item.get(sub_col, 'unknown')
            if value_col:
                value_map[row_key][group_key] += float(item.get(value_col, 0))
            else:
                value_map[row_key][group_key] += 1
        
        # Extraer categorías únicas
        rows = sorted(value_map.keys())
        all_groups = set()
        for row_dict in value_map.values():
            all_groups.update(row_dict.keys())
        groups = sorted(all_groups)
        
        # Crear matriz de valores
        series = []
        for group in groups:
            group_values = []
            for row in rows:
                value = value_map[row].get(group, 0.0)
                group_values.append(float(value))
            series.append(group_values)
    
    return rows, groups, series

