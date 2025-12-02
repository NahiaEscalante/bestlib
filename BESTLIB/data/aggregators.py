"""
Agregadores de datos para BESTLIB
"""
from collections import defaultdict
from ._imports import ensure_pandas

pd = ensure_pandas()
HAS_PANDAS = pd is not None

def group_by_category(data, category_col, value_col=None, agg_func='sum'):
    """
    Agrupa datos por categoría y agrega valores.
    
    Args:
        data: DataFrame o lista de diccionarios
        category_col: Columna categórica
        value_col: Columna numérica (opcional)
        agg_func: Función de agregación ('sum', 'count', 'mean')
    
    Returns:
        list: Datos agrupados
    """
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        if value_col and value_col in data.columns:
            if agg_func == 'sum':
                grouped = data.groupby(category_col)[value_col].sum().reset_index()
            elif agg_func == 'mean':
                grouped = data.groupby(category_col)[value_col].mean().reset_index()
            elif agg_func == 'count':
                grouped = data.groupby(category_col)[value_col].count().reset_index()
            else:
                grouped = data.groupby(category_col)[value_col].sum().reset_index()
            return grouped.rename(columns={category_col: 'category', value_col: 'value'}).to_dict('records')
        else:
            counts = data[category_col].value_counts()
            return [{'category': cat, 'value': count} for cat, count in counts.items()]
    else:
        if value_col:
            sums = defaultdict(float)
            for item in data:
                cat = item.get(category_col, 'unknown')
                val = item.get(value_col, 0)
                if agg_func == 'sum':
                    sums[cat] += float(val)
                elif agg_func == 'mean':
                    # Calcular media requiere dos pasadas
                    pass  # Implementar si es necesario
            return [{'category': k, 'value': v} for k, v in sums.items()]
        else:
            from collections import Counter
            counts = Counter([item.get(category_col, 'unknown') for item in data])
            return [{'category': k, 'value': v} for k, v in counts.items()]


def bin_numeric_data(data, column, bins=10):
    """
    Binnear datos numéricos.
    
    Args:
        data: DataFrame o lista de diccionarios
        column: Columna numérica a binnear
        bins: Número de bins o lista de bordes
    
    Returns:
        tuple: (hist_data, bin_edges)
    """
    import math
    
    values = []
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        series = data[column].dropna()
        try:
            values = series.astype(float).tolist()
        except Exception:
            values = [float(v) for v in series.tolist()]
    else:
        for item in data:
            v = item.get(column)
            if v is not None:
                try:
                    values.append(float(v))
                except Exception:
                    continue
    
    if not values:
        return [], []
    
    vmin = min(values)
    vmax = max(values)
    if isinstance(bins, int):
        step = (vmax - vmin) / bins if vmax > vmin else 1.0
        edges = [vmin + i * step for i in range(bins + 1)]
    else:
        edges = list(bins)
        edges.sort()
    
    # Calcular conteos por bin
    hist = [0] * (len(edges) - 1)
    for val in values:
        for i in range(len(edges) - 1):
            left, right = edges[i], edges[i + 1]
            if (val >= left and val < right) or (i == len(edges) - 2 and val == right):
                hist[i] += 1
                break
    
    hist_data = [
        {
            'bin': float((edges[i] + edges[i + 1]) / 2.0),
            'count': int(hist[i])
        }
        for i in range(len(hist))
    ]
    
    return hist_data, edges


def calculate_statistics(data, column):
    """
    Calcula estadísticas básicas de una columna numérica.
    
    Args:
        data: DataFrame o lista de diccionarios
        column: Columna numérica
    
    Returns:
        dict: Estadísticas (min, max, mean, median, etc.)
    """
    import statistics
    
    values = []
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        series = data[column].dropna()
        values = series.astype(float).tolist()
    else:
        for item in data:
            v = item.get(column)
            if v is not None:
                try:
                    values.append(float(v))
                except Exception:
                    continue
    
    if not values:
        return {}
    
    return {
        'min': float(min(values)),
        'max': float(max(values)),
        'mean': float(statistics.mean(values)),
        'median': float(statistics.median(values)),
        'count': len(values)
    }

