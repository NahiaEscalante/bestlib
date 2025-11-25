"""
Preparadores de datos para diferentes tipos de gráficos
"""
from ..utils.imports import has_pandas, get_pandas
from typing import Any, Dict, List, Optional, Tuple

from .validators import validate_scatter_data, validate_bar_data, validate_data_structure
from ..core.exceptions import DataError
from ..core.validation import validate_dataframe, safe_dataframe


def prepare_scatter_data(data: Any, x_col: Optional[str] = None, y_col: Optional[str] = None, 
                         category_col: Optional[str] = None, size_col: Optional[str] = None, 
                         color_col: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
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
    
    Raises:
        DataError: Si los datos son inválidos o los parámetros no son strings válidos.
    """
    if data is None:
        raise DataError("data cannot be None")
    if x_col is not None and (not isinstance(x_col, str) or not x_col):
        raise DataError("x_col must be None or non-empty str")
    if y_col is not None and (not isinstance(y_col, str) or not y_col):
        raise DataError("y_col must be None or non-empty str")
    if category_col is not None and (not isinstance(category_col, str) or not category_col):
        raise DataError("category_col must be None or non-empty str")
    if size_col is not None and (not isinstance(size_col, str) or not size_col):
        raise DataError("size_col must be None or non-empty str")
    if color_col is not None and (not isinstance(color_col, str) or not color_col):
        raise DataError("color_col must be None or non-empty str")
    # Validar datos
    if x_col and y_col:
        validate_scatter_data(data, x_col, y_col)
    
    if has_pandas():
        pd = get_pandas()
        if pd is not None:
            try:
                # ✅ CRIT-001, CRIT-007: Usar validate_dataframe() para validar DataFrame y columnas
                if isinstance(data, pd.DataFrame):
                    validate_dataframe(data, allow_empty=True)
                    
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
                        if idx < len(original_data) and idx < len(data.index):
                item['_original_row'] = original_data[idx]
                item['_original_index'] = int(data.index[idx])
                        else:
                            # Fallback si hay desajuste
                            item['_original_row'] = item.copy()
                            item['_original_index'] = idx
            
            return processed_data, original_data
            except (AttributeError, TypeError) as e:
                # Fallback si hay problema accediendo DataFrame
                raise DataError(f"Error accediendo DataFrame: {e}")
            else:
                # No es DataFrame, continuar con lógica de lista
                pass
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


def prepare_bar_data(data: Any, category_col: Optional[str] = None, value_col: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Prepara datos para bar chart.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        category_col: Nombre de columna para categorías
        value_col: Nombre de columna para valores (opcional)
    
    Returns:
        list: Datos preparados para bar chart
    
    Raises:
        DataError: Si los datos son inválidos o los parámetros no son strings válidos.
    """
    if data is None:
        raise DataError("data cannot be None")
    if not isinstance(category_col, str) or not category_col:
        raise DataError("category_col must be non-empty str")
    if value_col is not None and (not isinstance(value_col, str) or not value_col):
        raise DataError("value_col must be None or non-empty str")
    from collections import Counter
    
    if has_pandas():
        pd = get_pandas()
        if pd is not None:
            try:
                if isinstance(data, pd.DataFrame):
                    # ✅ CRIT-001, CRIT-007: Usar validación centralizada
                    required_cols = []
                    if category_col:
                        required_cols.append(category_col)
                    if value_col:
                        required_cols.append(value_col)
                    validate_dataframe(data, required_cols=required_cols if required_cols else None, allow_empty=False)
                    
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
                        matching_rows = [
                            row for row in original_data 
                            if row.get(category_col, None) == bar_item['category']
                        ]
                bar_item['_original_rows'] = matching_rows
            
            return bar_data
            except (AttributeError, TypeError) as e:
                # Fallback si hay problema accediendo DataFrame
                raise DataError(f"Error accediendo DataFrame: {e}")
            else:
                # No es DataFrame, continuar con lógica de lista
                pass
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
                matching_rows = [
                    row for row in data 
                    if row.get(category_col or 'category', None) == bar_item['category']
                ]
                # Validación opcional: advertir si no se encuentran filas
                if not matching_rows:
                    # No imprimir advertencia aquí para evitar ruido, pero está validado
                    pass
                bar_item['_original_rows'] = matching_rows
            
            return bar_data
        else:
            raise DataError("Los datos deben ser un DataFrame de pandas o una lista de diccionarios")


def prepare_histogram_data(data: Any, value_col: Optional[str] = None, bins: int = 10) -> List[Dict[str, Any]]:
    """
    Prepara datos para histograma.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        value_col: Columna numérica a binnear
        bins: Número de bins
    
    Returns:
        list: Datos preparados para histograma con _original_rows por bin
    
    Raises:
        DataError: Si los datos son inválidos o los parámetros no son válidos.
    """
    if data is None:
        raise DataError("data cannot be None")
    if value_col is not None and (not isinstance(value_col, str) or not value_col):
        raise DataError("value_col must be None or non-empty str")
    if not isinstance(bins, int) or bins <= 0:
        raise DataError(f"bins must be positive int, received: {bins!r}")
    import math
    
    values = []
    if has_pandas():
        pd = get_pandas()
        if pd is not None:
            try:
                if isinstance(data, pd.DataFrame):
                    # ✅ CRIT-001, CRIT-007: Usar validación centralizada
                    required_cols = [value_col] if value_col else None
                    validate_dataframe(data, required_cols=required_cols, allow_empty=False)
                    
                    if not value_col or not isinstance(value_col, str) or not value_col.strip():
                        raise DataError("value_col debe ser un string no vacío para histograma con DataFrame")
                    if value_col not in data.columns:
                        raise DataError(
                            f"Columna '{value_col}' no existe en el DataFrame. "
                            f"Columnas disponibles: {list(data.columns)}"
                        )
                    
            series = data[value_col].dropna()
            try:
                values = series.astype(float).tolist()
                    except (ValueError, TypeError):
                values = [float(v) for v in series.tolist()]
            except (AttributeError, TypeError) as e:
                raise DataError(f"Error accediendo DataFrame: {e}")
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
        if vmax > vmin:
            step = (vmax - vmin) / bins
        edges = [vmin + i * step for i in range(bins + 1)]
        else:
            # Todos los valores son iguales - crear un solo bin
            edges = [vmin - 0.5, vmax + 0.5]
    else:
        edges = list(bins)
        edges.sort()
    
    # Almacenar filas originales para cada bin
    bin_rows = [[] for _ in range(len(edges) - 1)]
    
    if has_pandas():
        pd = get_pandas()
        if pd is not None:
            try:
                if isinstance(data, pd.DataFrame):
                    # ✅ CRIT-001, CRIT-007: Validar DataFrame antes de acceder
                    validate_dataframe(data, allow_empty=False)
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
                            except (ValueError, TypeError):
                    continue
            except (AttributeError, TypeError) as e:
                raise DataError(f"Error accediendo DataFrame: {e}")
        else:
            # Si no es DataFrame, tratar como lista
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


def prepare_boxplot_data(data: Any, category_col: Optional[str] = None, value_col: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Prepara datos para boxplot.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        category_col: Columna categórica (opcional)
        value_col: Columna numérica para calcular cuantiles
    
    Returns:
        list: Datos preparados para boxplot
    
    Raises:
        DataError: Si los datos son inválidos o los parámetros no son strings válidos.
    """
    if data is None:
        raise DataError("data cannot be None")
    if category_col is not None and (not isinstance(category_col, str) or not category_col):
        raise DataError("category_col must be None or non-empty str")
    if value_col is not None and (not isinstance(value_col, str) or not value_col):
        raise DataError("value_col must be None or non-empty str")
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
    if has_pandas():
        pd = get_pandas()
        if pd is not None:
            try:
                if isinstance(data, pd.DataFrame):
                    # ✅ CRIT-001, CRIT-007: Usar validación centralizada
                    required_cols = []
                    if category_col:
                        required_cols.append(category_col)
                    if value_col:
                        required_cols.append(value_col)
                    validate_dataframe(data, required_cols=required_cols if required_cols else None, allow_empty=False)
                    
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
                    return box_data
                except (AttributeError, TypeError) as e:
                    # Fallback si hay problema accediendo DataFrame
                    raise DataError(f"Error accediendo DataFrame: {e}")
            else:
                # No es DataFrame, continuar con lógica de lista
                pass
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


def prepare_heatmap_data(data: Any, x_col: Optional[str] = None, y_col: Optional[str] = None, 
                         value_col: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Prepara datos para heatmap.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        x_col: Columna para eje X
        y_col: Columna para eje Y
        value_col: Columna para valores
    
    Returns:
        tuple: (cells, x_labels, y_labels)
    
    Raises:
        DataError: Si los datos son inválidos o los parámetros no son strings válidos.
    """
    if data is None:
        raise DataError("data cannot be None")
    if x_col is not None and (not isinstance(x_col, str) or not x_col):
        raise DataError("x_col must be None or non-empty str")
    if y_col is not None and (not isinstance(y_col, str) or not y_col):
        raise DataError("y_col must be None or non-empty str")
    if value_col is not None and (not isinstance(value_col, str) or not value_col):
        raise DataError("value_col must be None or non-empty str")
    cells = []
    x_labels, y_labels = [], []
    
    if has_pandas():
        pd = get_pandas()
        if pd is not None:
            try:
                if isinstance(data, pd.DataFrame):
                    # ✅ CRIT-001, CRIT-007: Validar DataFrame antes de acceder
                    required_cols = []
                    if value_col and x_col and y_col:
                        required_cols = [x_col, y_col, value_col]
                    validate_dataframe(data, required_cols=required_cols if required_cols else None, allow_empty=False)
                    
            if value_col and x_col and y_col:
                df = data[[x_col, y_col, value_col]].dropna()
                x_labels = df[x_col].astype(str).unique().tolist()
                y_labels = df[y_col].astype(str).unique().tolist()
                cells = [
                    {'x': str(r[x_col]), 'y': str(r[y_col]), 'value': float(r[value_col])}
                    for _, r in df.iterrows()
                ]
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
            except (AttributeError, TypeError) as e:
                raise DataError(f"Error accediendo DataFrame: {e}")
    else:
        if not isinstance(data, list):
            raise DataError("Datos inválidos para heatmap")
        for item in data:
            if x_col in item and y_col in item and value_col in item:
                cells.append({'x': str(item[x_col]), 'y': str(item[y_col]), 'value': float(item[value_col])})
                x_labels.append(str(item[x_col]))
                y_labels.append(str(item[y_col]))
        x_labels = sorted(list(set(x_labels)))
        y_labels = sorted(list(set(y_labels)))
    
    return cells, x_labels, y_labels


def prepare_line_data(data: Any, x_col: Optional[str] = None, y_col: Optional[str] = None, 
                      series_col: Optional[str] = None) -> Dict[str, Any]:
    """
    Prepara datos para line chart.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        x_col: Columna para eje X
        y_col: Columna para eje Y
        series_col: Columna para series (opcional)
    
    Returns:
        dict: Datos preparados con 'series'
    
    Raises:
        DataError: Si los datos son inválidos o los parámetros no son strings válidos.
    """
    if data is None:
        raise DataError("data cannot be None")
    if not isinstance(x_col, str) or not x_col:
        raise DataError("x_col must be non-empty str")
    if not isinstance(y_col, str) or not y_col:
        raise DataError("y_col must be non-empty str")
    if series_col is not None and (not isinstance(series_col, str) or not series_col):
        raise DataError("series_col must be None or non-empty str")
    if has_pandas():
        pd = get_pandas()
        if pd is not None:
            try:
                if isinstance(data, pd.DataFrame):
                    # ✅ CRIT-001, CRIT-007: Validar DataFrame antes de acceder
                    required_cols = [x_col, y_col] + ([series_col] if series_col else [])
                    validate_dataframe(data, required_cols=required_cols, allow_empty=False)
                    
            if x_col is None or y_col is None:
                raise DataError("x_col e y_col son requeridos para line plot")
            df = data[[x_col, y_col] + ([series_col] if series_col else [])].dropna()
            if series_col:
                series_names = df[series_col].unique().tolist()
                series = {}
                for name in series_names:
                    sdf = df[df[series_col] == name].sort_values(by=x_col)
                    series[name] = [{'x': float(x), 'y': float(y), 'series': str(name)} for x, y in zip(sdf[x_col], sdf[y_col])]
                return {'series': series}
            else:
                sdf = df.sort_values(by=x_col)
                return {'series': {'default': [{'x': float(x), 'y': float(y)} for x, y in zip(sdf[x_col], sdf[y_col])]}}
            except (AttributeError, TypeError) as e:
                raise DataError(f"Error accediendo DataFrame: {e}")
    else:
        items = [d for d in (data or []) if x_col in d and y_col in d]
        if series_col:
            series = {}
            for item in items:
                key = str(item.get(series_col))
                series.setdefault(key, []).append({'x': float(item[x_col]), 'y': float(item[y_col]), 'series': key})
            for k in series:
                series[k] = sorted(series[k], key=lambda p: p['x'])
            return {'series': series}
        else:
            pts = sorted([{'x': float(i[x_col]), 'y': float(i[y_col])} for i in items], key=lambda p: p['x'])
            return {'series': {'default': pts}}


def prepare_pie_data(data: Any, category_col: Optional[str] = None, value_col: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Prepara datos para pie chart.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        category_col: Columna categórica
        value_col: Columna numérica (opcional)
    
    Returns:
        list: Datos preparados para pie chart con _original_rows
    
    Raises:
        DataError: Si los datos son inválidos o category_col no es string válido.
    """
    if data is None:
        raise DataError("data cannot be None")
    if not isinstance(category_col, str) or not category_col:
        raise DataError("category_col must be non-empty str")
    if value_col is not None and (not isinstance(value_col, str) or not value_col):
        raise DataError("value_col must be None or non-empty str")
    from collections import Counter, defaultdict
    
    slices = []
    if has_pandas():
        pd = get_pandas()
        if pd is not None:
            try:
                if isinstance(data, pd.DataFrame):
                    # ✅ CRIT-001, CRIT-007: Validar DataFrame antes de acceder
                    required_cols = [category_col] + ([value_col] if value_col else [])
                    validate_dataframe(data, required_cols=required_cols, allow_empty=False)
                    
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
            except (AttributeError, TypeError) as e:
                raise DataError(f"Error accediendo DataFrame: {e}")
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


def prepare_grouped_bar_data(data: Any, main_col: Optional[str] = None, sub_col: Optional[str] = None, 
                            value_col: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Prepara datos para grouped bar chart.
    
    Args:
        data: DataFrame de pandas o lista de diccionarios
        main_col: Columna principal
        sub_col: Columna de sub-grupos
        value_col: Columna de valores (opcional)
    
    Returns:
        tuple: (rows, groups, series)
    
    Raises:
        DataError: Si los datos son inválidos o los parámetros no son strings válidos.
    """
    if data is None:
        raise DataError("data cannot be None")
    if not isinstance(main_col, str) or not main_col:
        raise DataError("main_col must be non-empty str")
    if not isinstance(sub_col, str) or not sub_col:
        raise DataError("sub_col must be non-empty str")
    if value_col is not None and (not isinstance(value_col, str) or not value_col):
        raise DataError("value_col must be None or non-empty str")
    rows = []
    if has_pandas():
        pd = get_pandas()
        if pd is not None:
            try:
                if isinstance(data, pd.DataFrame):
                    # ✅ CRIT-001, CRIT-007: Validar DataFrame antes de acceder
                    required_cols = [main_col, sub_col] + ([value_col] if value_col else [])
                    validate_dataframe(data, required_cols=required_cols, allow_empty=False)
                    
            if value_col and value_col in data.columns:
                agg = data.groupby([main_col, sub_col])[value_col].sum().reset_index()
                for _, r in agg.iterrows():
                    rows.append({'group': r[main_col], 'series': r[sub_col], 'value': float(r[value_col])})
                groups = agg[main_col].unique().tolist()
                series = agg[sub_col].unique().tolist()
            else:
                counts = data.groupby([main_col, sub_col]).size().reset_index(name='value')
                for _, r in counts.iterrows():
                    rows.append({'group': r[main_col], 'series': r[sub_col], 'value': float(r['value'])})
                groups = counts[main_col].unique().tolist()
                series = counts[sub_col].unique().tolist()
            except (AttributeError, TypeError) as e:
                raise DataError(f"Error accediendo DataFrame: {e}")
    else:
        from collections import defaultdict
        if not isinstance(data, list):
            raise DataError("Datos inválidos para grouped barplot")
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
    
    return rows, groups, series

