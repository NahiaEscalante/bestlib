# Plan de Corrección de Errores - BESTLIB

## Resumen Ejecutivo

Este documento presenta un plan detallado para corregir todos los errores identificados en la librería BESTLIB. El plan está organizado por prioridad y agrupa los errores por categoría para una corrección sistemática.

---

## Análisis de Errores Verificados

### 1. Errores de Validación de Spec (CRÍTICO)

**Archivo afectado**: `BESTLIB/charts/spec_utils.py`

```python
# Líneas 11-12 - Problema actual
def validate_spec(spec):
    if 'data' not in spec:
        raise ChartError("El spec debe incluir 'data'")
```

**Gráficos afectados que NO tienen `'data'` en su spec**:

| Gráfico | Archivo | Estructura Actual | ¿Funciona? |
|---------|---------|-------------------|------------|
| `HeatmapChart` | `charts/heatmap.py` | `{'type': 'heatmap', 'cells': [...], 'x_labels': [...], 'y_labels': [...]}` | ❌ |
| `LineChart` | `charts/line.py` | `{'type': 'line', 'series': {...}}` | ❌ |
| `LinePlotChart` | `charts/line_plot.py` | `{'type': 'line_plot', 'series': {...}}` | ❌ |
| `GroupedBarChart` | `charts/grouped_bar.py` | `{'type': 'grouped_bar', 'rows': [...], 'groups': [...], 'series': [...]}` | ❌ |
| `StepPlotChart` | `charts/step_plot.py` | Bug: devuelve dict donde debería ser lista | ❌ |

**Gráficos que SÍ tienen `'data'` (funcionan)**:
- `ScatterChart`, `BarChart`, `PieChart`, `HistogramChart`, `BoxplotChart`
- `ViolinChart`, `RadvizChart`, `StarCoordinatesChart`, `ParallelCoordinatesChart`
- `HorizontalBarChart`, `HexbinChart`, `ErrorbarsChart`, `FillBetweenChart`
- `KdeChart`, `DistplotChart`, `RugChart`, `QqplotChart`, `EcdfChart`
- `RidgelineChart`, `RibbonChart`, `Hist2dChart`, `PolarChart`, `FunnelChart`

---

### 2. Errores de Importación (CRÍTICO)

#### 2.1. `map_correlation_heatmap` no encontrado

**Ubicación del error**: `BESTLIB/layouts/reactive.py:46`

```python
# Actualmente importa desde layouts/matrix.py (incorrecto)
from .matrix import MatrixLayout
```

**Problema**: 
- `BESTLIB/layouts/matrix.py` NO tiene `map_correlation_heatmap`
- `BESTLIB/matrix.py` (legacy) SÍ tiene `map_correlation_heatmap` (línea 1322)

#### 2.2. Métodos `add_*` faltantes

**Métodos que existen SOLO en `BESTLIB/reactive.py` (legacy)**:
- `add_kde` (línea 3633)
- `add_distplot` (línea 3658)
- `add_rug` (línea 3683)
- `add_qqplot` (línea 3708)
- `add_ecdf` (línea 3733)

**Archivo afectado**: `BESTLIB/layouts/reactive.py` - NO tiene estos métodos

---

### 3. Renderer JavaScript Faltante (CRÍTICO)

**Archivo**: `BESTLIB/matrix.js`

**Problema**: No existe `renderGroupedBarD3()` para el tipo `'grouped_bar'`

**Switch en `renderChartD3()` (líneas 1514-1568)**:
- ✅ `bar`, `scatter`, `histogram`, `boxplot`, `heatmap`, `line`, `pie`, `violin`
- ✅ `radviz`, `star_coordinates`, `parallel_coordinates`, `line_plot`
- ✅ `horizontal_bar`, `hexbin`, `errorbars`, `fill_between`, `step_plot`
- ✅ `kde`, `distplot`, `rug`, `qqplot`, `ecdf`, `ridgeline`, `ribbon`
- ✅ `hist2d`, `polar`, `funnel`
- ❌ **`grouped_bar`** - FALTA

---

### 4. Bug en `StepPlotChart` (ALTO)

**Archivo**: `BESTLIB/charts/step_plot.py`

**Problema en `prepare_data()` (líneas 89-95)**:
```python
# INCORRECTO - prepare_line_data devuelve dict, no tupla
processed_data, original_data = prepare_line_data(...)  # ❌ Error de desempaquetado
```

**Lo que devuelve `prepare_line_data()`** (línea 402 de `preparators.py`):
```python
return {'series': series}  # Devuelve dict, NO tupla
```

---

### 5. Análisis de Line Chart vs Line Plot

| Característica | Line Chart (`line.py`) | Line Plot (`line_plot.py`) |
|---------------|----------------------|--------------------------|
| Tipo | `'line'` | `'line_plot'` |
| Spec | `{'type': 'line', 'series': {...}}` | `{'type': 'line_plot', 'series': {...}, 'encoding': {...}, 'options': {...}}` |
| Renderer JS | `renderLineD3()` (línea 1864) | `renderLinePlotD3()` (línea 6469) |
| Complejidad | Simple | Completo (más opciones) |

**Recomendación**: Mantener ambos ya que tienen renderers diferentes en JavaScript.

---

## Plan de Ejecución

### Fase 1: Corrección de `validate_spec()` [PRIORITARIO]

**Archivo**: `BESTLIB/charts/spec_utils.py`

**Acción**: Modificar `validate_spec()` para ser más flexible:

```python
def validate_spec(spec):
    if not isinstance(spec, dict):
        raise ChartError("El spec debe ser un diccionario")
    if 'type' not in spec:
        raise ChartError("El spec debe incluir 'type'")
    
    # Tipos de gráficos que usan estructuras diferentes
    type_data_fields = {
        'heatmap': ['cells', 'data'],  # acepta 'cells' O 'data'
        'line': ['series', 'data'],
        'line_plot': ['series', 'data'],
        'grouped_bar': ['rows', 'groups', 'series', 'data'],
        'step_plot': ['series', 'data'],
    }
    
    chart_type = spec.get('type')
    
    # Verificar si el tipo tiene campos alternativos
    if chart_type in type_data_fields:
        valid_fields = type_data_fields[chart_type]
        if not any(field in spec for field in valid_fields):
            raise ChartError(f"El spec de '{chart_type}' debe incluir alguno de: {valid_fields}")
    else:
        # Para otros tipos, requerir 'data'
        if 'data' not in spec:
            raise ChartError("El spec debe incluir 'data'")
    
    return spec
```

**Archivos a modificar**: 1 archivo

---

### Fase 2: Corrección de Gráficos con Specs Incorrectos

#### 2.1. `HeatmapChart` - Agregar campo `'data'`

**Archivo**: `BESTLIB/charts/heatmap.py`

**Cambio**: Modificar `get_spec()` para incluir `'data'`:

```python
def get_spec(self, data, x_col=None, y_col=None, value_col=None, **kwargs):
    prepared = self.prepare_data(data, x_col=x_col, y_col=y_col, value_col=value_col, **kwargs)
    return {
        'type': self.chart_type,
        'data': prepared['cells'],  # Agregar 'data' para compatibilidad
        'cells': prepared['cells'],
        'x_labels': prepared['x_labels'],
        'y_labels': prepared['y_labels'],
        **kwargs
    }
```

#### 2.2. `LineChart` - Agregar campo `'data'`

**Archivo**: `BESTLIB/charts/line.py`

**Cambio**: Modificar `get_spec()` para incluir `'data'`:

```python
def get_spec(self, data, x_col=None, y_col=None, series_col=None, **kwargs):
    self.validate_data(data, x_col=x_col, y_col=y_col, **kwargs)
    line_data = self.prepare_data(data, x_col=x_col, y_col=y_col, series_col=series_col, **kwargs)
    
    # Extraer puntos de todas las series para 'data'
    all_points = []
    for series_points in line_data.get('series', {}).values():
        all_points.extend(series_points)
    
    return {
        'type': self.chart_type,
        'data': all_points,  # Agregar 'data' para compatibilidad
        **line_data,
        **kwargs
    }
```

#### 2.3. `LinePlotChart` - Agregar campo `'data'`

**Archivo**: `BESTLIB/charts/line_plot.py`

**Cambio similar al de LineChart** en el método `get_spec()`.

#### 2.4. `GroupedBarChart` - Agregar campo `'data'`

**Archivo**: `BESTLIB/charts/grouped_bar.py`

**Cambio**: Modificar `get_spec()`:

```python
def get_spec(self, data, main_col=None, sub_col=None, value_col=None, **kwargs):
    self.validate_data(data, main_col=main_col, sub_col=sub_col, **kwargs)
    prepared = self.prepare_data(data, main_col=main_col, sub_col=sub_col, value_col=value_col, **kwargs)
    
    # Crear datos planos para 'data'
    flat_data = []
    for row_idx, row in enumerate(prepared['rows']):
        for group_idx, group in enumerate(prepared['groups']):
            flat_data.append({
                'row': row,
                'group': group,
                'value': prepared['series'][group_idx][row_idx] if group_idx < len(prepared['series']) and row_idx < len(prepared['series'][group_idx]) else 0
            })
    
    return {
        'type': self.chart_type,
        'grouped': True,
        'data': flat_data,  # Agregar 'data' para compatibilidad
        **prepared,
        **kwargs
    }
```

**Archivos a modificar**: 4 archivos

---

### Fase 3: Corrección de Bug en `StepPlotChart`

**Archivo**: `BESTLIB/charts/step_plot.py`

**Problema**: `prepare_line_data()` devuelve dict, no tupla.

**Corrección en `prepare_data()` y `get_spec()`**:

```python
def prepare_data(self, data, x_col=None, y_col=None, **kwargs):
    # Ordenar por x_col para step plot
    if HAS_PANDAS and isinstance(data, pd.DataFrame):
        data_sorted = data.sort_values(by=x_col).copy()
    else:
        data_sorted = sorted(data, key=lambda d: d.get(x_col, 0))
    
    # prepare_line_data devuelve {'series': {...}}
    line_data = prepare_line_data(
        data_sorted,
        x_col=x_col,
        y_col=y_col
    )
    
    return line_data  # Devolver dict directamente

def get_spec(self, data, x_col=None, y_col=None, **kwargs):
    self.validate_data(data, x_col=x_col, y_col=y_col, **kwargs)
    
    prepared_data = self.prepare_data(data, x_col=x_col, y_col=y_col, **kwargs)
    
    # Extraer puntos de series para 'data'
    all_points = []
    for series_points in prepared_data.get('series', {}).values():
        all_points.extend(series_points)
    
    process_figsize_in_kwargs(kwargs)
    
    if 'xLabel' not in kwargs and x_col:
        kwargs['xLabel'] = x_col
    if 'yLabel' not in kwargs and y_col:
        kwargs['yLabel'] = y_col
    
    spec = {
        'type': self.chart_type,
        'data': all_points,  # Lista de puntos
        'series': prepared_data.get('series', {}),
    }
    
    # ... resto igual
```

**Archivos a modificar**: 1 archivo

---

### Fase 4: Agregar Métodos Faltantes a `layouts/reactive.py`

**Archivo**: `BESTLIB/layouts/reactive.py`

**Métodos a agregar** (copiar desde `BESTLIB/reactive.py`):

1. `add_kde` (líneas 3633-3656 de reactive.py)
2. `add_distplot` (líneas 3658-3681)
3. `add_rug` (líneas 3683-3706)
4. `add_qqplot` (líneas 3708-3731)
5. `add_ecdf` (líneas 3733-3756)
6. `add_correlation_heatmap` - corregir importación (usar matrix.py legacy o agregar método a layouts/matrix.py)

**Opción A**: Agregar `map_correlation_heatmap` a `layouts/matrix.py`
**Opción B**: Cambiar importación en `layouts/reactive.py` para usar `BESTLIB.matrix.MatrixLayout`

**Recomendación**: Opción A - Agregar el método a `layouts/matrix.py` para mantener consistencia modular.

**Archivos a modificar**: 2 archivos (`layouts/reactive.py`, `layouts/matrix.py`)

---

### Fase 5: Implementar Renderer JavaScript para `grouped_bar`

**Archivo**: `BESTLIB/matrix.js`

**Acciones**:

1. Agregar case para `'grouped_bar'` en `renderChartD3()` (después de línea 1567):

```javascript
} else if (chartType === 'grouped_bar' || chartType === 'grouped_barchart') {
  renderGroupedBarD3(container, spec, d3, divId);
}
```

2. Implementar `renderGroupedBarD3()`:

```javascript
function renderGroupedBarD3(container, spec, d3, divId) {
  const rows = spec.rows || [];
  const groups = spec.groups || [];
  const series = spec.series || [];
  
  const dims = getChartDimensions(container, spec, 500, 400);
  const margin = { top: 20, right: 30, bottom: 40, left: 60 };
  const width = dims.width - margin.left - margin.right;
  const height = dims.height - margin.top - margin.bottom;
  
  container.innerHTML = '';
  
  const svg = d3.select(container)
    .append('svg')
    .attr('width', dims.width)
    .attr('height', dims.height)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);
  
  // Escala X para grupos principales (rows)
  const x0 = d3.scaleBand()
    .domain(rows)
    .rangeRound([0, width])
    .paddingInner(0.1);
  
  // Escala X para subgrupos (groups)
  const x1 = d3.scaleBand()
    .domain(groups)
    .rangeRound([0, x0.bandwidth()])
    .padding(0.05);
  
  // Escala Y
  const maxValue = d3.max(series, s => d3.max(s));
  const y = d3.scaleLinear()
    .domain([0, maxValue || 1])
    .nice()
    .rangeRound([height, 0]);
  
  // Colores
  const color = d3.scaleOrdinal()
    .domain(groups)
    .range(d3.schemeCategory10);
  
  // Dibujar barras
  svg.append('g')
    .selectAll('g')
    .data(rows)
    .join('g')
    .attr('transform', d => `translate(${x0(d)},0)`)
    .selectAll('rect')
    .data((d, i) => groups.map((group, j) => ({
      key: group,
      value: series[j] ? series[j][i] : 0
    })))
    .join('rect')
    .attr('x', d => x1(d.key))
    .attr('y', d => y(d.value))
    .attr('width', x1.bandwidth())
    .attr('height', d => height - y(d.value))
    .attr('fill', d => color(d.key));
  
  // Eje X
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x0));
  
  // Eje Y
  svg.append('g')
    .call(d3.axisLeft(y));
  
  // Leyenda
  const legend = svg.append('g')
    .attr('transform', `translate(${width - 100}, 0)`);
  
  groups.forEach((group, i) => {
    const g = legend.append('g')
      .attr('transform', `translate(0, ${i * 20})`);
    
    g.append('rect')
      .attr('width', 15)
      .attr('height', 15)
      .attr('fill', color(group));
    
    g.append('text')
      .attr('x', 20)
      .attr('y', 12)
      .attr('font-size', '12px')
      .text(group);
  });
}
```

**Archivos a modificar**: 1 archivo

---

## Resumen del Plan

| Fase | Descripción | Archivos | Prioridad |
|------|-------------|----------|-----------|
| 1 | Corregir `validate_spec()` | 1 | CRÍTICA |
| 2 | Corregir specs de gráficos | 4 | CRÍTICA |
| 3 | Corregir bug en `StepPlotChart` | 1 | ALTA |
| 4 | Agregar métodos faltantes | 2 | ALTA |
| 5 | Implementar renderer JS para grouped_bar | 1 | ALTA |

**Total de archivos a modificar**: 9 archivos

---

## Orden de Ejecución Recomendado

1. **Primero**: Fase 1 (validate_spec) - Desbloquea varios gráficos inmediatamente
2. **Segundo**: Fase 2 (specs de gráficos) - Hace compatibles los gráficos existentes
3. **Tercero**: Fase 3 (StepPlotChart) - Corrige bug específico
4. **Cuarto**: Fase 4 (métodos faltantes) - Completa la API
5. **Quinto**: Fase 5 (renderer JS) - Habilita visualización de grouped_bar

---

## Verificación Post-Corrección

Después de implementar las correcciones, ejecutar pruebas para verificar:

1. **Gráficos que generaban error `"El spec debe incluir 'data'"`**:
   - Heatmap ✓
   - Line Plot ✓
   - Line Chart ✓
   - Grouped Bar ✓
   - Step Plot ✓

2. **Gráficos que no se visualizaban**:
   - Pie Chart ✓
   - RadViz ✓
   - Star Coordinates ✓
   - Parallel Coordinates ✓
   - Horizontal Bar ✓
   - Hexbin ✓
   - Errorbars ✓
   - Fill Between ✓
   - Grouped Bar Chart ✓

3. **Métodos que generaban AttributeError**:
   - `add_correlation_heatmap` ✓
   - `add_kde` ✓
   - `add_distplot` ✓
   - `add_rug` ✓
   - `add_qqplot` ✓
   - `add_ecdf` ✓

---

## Notas Adicionales

### Sobre Line Chart vs Line Plot

Ambos gráficos tienen propósitos similares pero implementaciones diferentes:
- **Line Chart** (`line.py`): Versión simple, usa `renderLineD3()`
- **Line Plot** (`line_plot.py`): Versión completa con más opciones, usa `renderLinePlotD3()`

**Recomendación**: Mantener ambos por compatibilidad, pero documentar que `Line Plot` es la versión recomendada para nuevos usos.

### Sobre Duplicación de Código

Existe duplicación entre:
- `BESTLIB/matrix.py` (legacy) y `BESTLIB/layouts/matrix.py` (modular)
- `BESTLIB/reactive.py` (legacy) y `BESTLIB/layouts/reactive.py` (modular)

**Recomendación futura**: Unificar el código en los módulos modulares y deprecar los archivos legacy.

---

*Plan generado el: 2 de diciembre de 2025*
*Basado en: Análisis del código fuente y documento INVESTIGACION_ERRORES.md*

