# 📊 Visualizaciones Disponibles en BESTLIB

Análisis completo de todas las visualizaciones implementadas en BESTLIB.

---

## 📋 Resumen Ejecutivo

**Total de visualizaciones: 15 tipos**

- ✅ **3 Elementos Visuales Simples** (sin D3.js)
- ✅ **12 Gráficos D3.js** (interactivos con D3.js)

---

## 🎨 Categoría 1: Elementos Visuales Simples

Estos elementos se renderizan directamente con SVG, sin necesidad de D3.js.

### 1. **Círculo** (`circle`)
- **Tipo**: Elemento SVG simple
- **Método**: `MatrixLayout.map()` con `'shape': 'circle'`
- **Parámetros**:
  - `color`: Color de relleno
  - `size`: Radio del círculo
  - `opacity`: Opacidad (0-1)
  - `stroke`: Color del borde
  - `strokeWidth`: Grosor del borde
  - `title`: Tooltip/título

**Ejemplo:**
```python
MatrixLayout.map({
    'C': {
        'shape': 'circle',
        'color': '#e74c3c',
        'size': 40,
        'opacity': 0.8,
        'title': 'Mi Círculo'
    }
})
```

### 2. **Rectángulo** (`rect`)
- **Tipo**: Elemento SVG simple
- **Método**: `MatrixLayout.map()` con `'shape': 'rect'`
- **Parámetros**:
  - `color`: Color de relleno
  - `width`: Ancho
  - `height`: Altura
  - `borderRadius`: Radio de esquinas redondeadas
  - `opacity`: Opacidad
  - `stroke`: Color del borde
  - `strokeWidth`: Grosor del borde

**Ejemplo:**
```python
MatrixLayout.map({
    'R': {
        'shape': 'rect',
        'color': '#3498db',
        'width': 80,
        'height': 50,
        'borderRadius': 5
    }
})
```

### 3. **Línea** (`line`)
- **Tipo**: Elemento SVG simple
- **Método**: `MatrixLayout.map()` con `'shape': 'line'`
- **Parámetros**:
  - `color`: Color de la línea
  - `strokeWidth`: Grosor de la línea
  - `x1`, `y1`: Coordenadas inicio
  - `x2`, `y2`: Coordenadas fin

**Ejemplo:**
```python
MatrixLayout.map({
    'L': {
        'shape': 'line',
        'color': '#2ecc71',
        'strokeWidth': 5,
        'x1': 10,
        'y1': 50,
        'x2': 90,
        'y2': 50
    }
})
```

---

## 📊 Categoría 2: Gráficos D3.js Interactivos

Todos estos gráficos se renderizan con D3.js y soportan interactividad.

### 4. **Scatter Plot** (`scatter`)
- **Tipo**: Gráfico de dispersión
- **Método MatrixLayout**: `MatrixLayout.map_scatter()`
- **Método ReactiveMatrixLayout**: `add_scatter()`
- **Clase Chart**: `ScatterChart`
- **Render JS**: `renderScatterPlotD3()`
- **Parámetros principales**:
  - `x_col`: Columna para eje X
  - `y_col`: Columna para eje Y
  - `category_col`: Columna para categorías (colorear puntos)
  - `color_col`: Columna para colores personalizados
  - `size_col`: Columna para tamaño de puntos
  - `interactive`: Habilita selección con brush
  - `zoom`: Habilita zoom con rueda del mouse
  - `axes`: Muestra ejes y etiquetas
  - `xLabel`, `yLabel`: Etiquetas de ejes

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_scatter('S', df, x_col='x', y_col='y', category_col='cat', interactive=True)

# ReactiveMatrixLayout
layout.add_scatter('S', x_col='x', y_col='y', color_col='category', interactive=True)
```

---

### 5. **Bar Chart** (`bar`)
- **Tipo**: Gráfico de barras
- **Método MatrixLayout**: `MatrixLayout.map_barchart()`
- **Método ReactiveMatrixLayout**: `add_barchart()`
- **Clase Chart**: `BarChart`
- **Render JS**: `renderBarChartD3()`
- **Parámetros principales**:
  - `category_col`: Columna de categorías
  - `value_col`: Columna de valores (opcional, cuenta si se omite)
  - `interactive`: Habilita selección con brush
  - `axes`: Muestra ejes y etiquetas
  - `color`: Color de las barras
  - `hoverColor`: Color al pasar el mouse

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_barchart('B', df, category_col='dept', value_col='ventas', interactive=True)

# ReactiveMatrixLayout
layout.add_barchart('B', category_col='category', value_col='value', linked_to='S')
```

---

### 6. **Grouped Bar Chart** (`grouped_bar`)
- **Tipo**: Gráfico de barras agrupadas (nested)
- **Método MatrixLayout**: `MatrixLayout.map_grouped_barchart()`
- **Método ReactiveMatrixLayout**: `add_grouped_barchart()`
- **Clase Chart**: `GroupedBarChart`
- **Render JS**: `renderGroupedBarChartD3()` (implícito en `renderBarChartD3()`)
- **Parámetros principales**:
  - `main_col`: Columna de categoría principal
  - `sub_col`: Columna de subcategoría
  - `value_col`: Columna de valores (opcional)
  - `interactive`: Habilita selección
  - `linked_to`: Enlaza a otra vista

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_grouped_barchart('G', df, main_col='region', sub_col='producto', value_col='ventas')

# ReactiveMatrixLayout
layout.add_grouped_barchart('G', main_col='region', sub_col='producto', value_col='ventas', linked_to='S')
```

---

### 7. **Histogram** (`histogram`)
- **Tipo**: Histograma de frecuencias
- **Método MatrixLayout**: `MatrixLayout.map_histogram()`
- **Método ReactiveMatrixLayout**: `add_histogram()`
- **Clase Chart**: `HistogramChart`
- **Render JS**: `renderHistogramD3()`
- **Parámetros principales**:
  - `column` / `value_col`: Columna numérica a analizar
  - `bins`: Número de bins (por defecto 20)
  - `interactive`: Habilita selección
  - `linked_to`: Enlaza a otra vista
  - `xLabel`, `yLabel`: Etiquetas de ejes

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_histogram('H', df, value_col='edad', bins=20)

# ReactiveMatrixLayout
layout.add_histogram('H', column='edad', bins=20, linked_to='S')
```

---

### 8. **Boxplot** (`boxplot`)
- **Tipo**: Diagrama de cajas y bigotes
- **Método MatrixLayout**: `MatrixLayout.map_boxplot()`
- **Método ReactiveMatrixLayout**: `add_boxplot()`
- **Clase Chart**: `BoxplotChart`
- **Render JS**: `renderBoxplotD3()`
- **Parámetros principales**:
  - `column` / `value_col`: Columna numérica
  - `category_col`: Columna de categorías (opcional)
  - `linked_to`: Enlaza a otra vista
  - `xLabel`, `yLabel`: Etiquetas de ejes

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_boxplot('X', df, category_col='dept', value_col='salario')

# ReactiveMatrixLayout
layout.add_boxplot('X', column='salario', category_col='dept', linked_to='S')
```

---

### 9. **Heatmap** (`heatmap`)
- **Tipo**: Mapa de calor
- **Método MatrixLayout**: `MatrixLayout.map_heatmap()`
- **Método ReactiveMatrixLayout**: `add_heatmap()`
- **Clase Chart**: `HeatmapChart`
- **Render JS**: `renderHeatmapD3()`
- **Parámetros principales**:
  - `x_col`: Columna para eje X
  - `y_col`: Columna para eje Y
  - `value_col`: Columna de valores
  - `colorMap`: Escala de colores
  - `linked_to`: Enlaza a otra vista
  - `axes`: Muestra ejes y etiquetas

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_heatmap('H', df, x_col='col', y_col='row', value_col='val')

# ReactiveMatrixLayout
layout.add_heatmap('H', x_col='col', y_col='row', value_col='val', linked_to='S')
```

---

### 10. **Correlation Heatmap** (`correlation_heatmap`)
- **Tipo**: Mapa de calor de correlación
- **Método ReactiveMatrixLayout**: `add_correlation_heatmap()`
- **Render JS**: `renderHeatmapD3()` (con datos de correlación)
- **Parámetros principales**:
  - `linked_to`: Enlaza a otra vista
  - `colorScale`: Escala de colores ('diverging', etc.)

**Ejemplo:**
```python
# Solo en ReactiveMatrixLayout
layout.add_correlation_heatmap('C', linked_to='S', colorScale='diverging')
```

---

### 11. **Line Chart** (`line`)
- **Tipo**: Gráfico de líneas (multi-series)
- **Método MatrixLayout**: `MatrixLayout.map_line()`
- **Método ReactiveMatrixLayout**: `add_line()`
- **Clase Chart**: `LineChart`
- **Render JS**: `renderLineD3()`
- **Parámetros principales**:
  - `x_col`: Columna para eje X (tiempo, etc.)
  - `y_col`: Columna para eje Y (valores)
  - `series_col`: Columna para series múltiples
  - `linked_to`: Enlaza a otra vista
  - `axes`: Muestra ejes y etiquetas

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_line('L', df, x_col='time', y_col='value', series_col='serie')

# ReactiveMatrixLayout
layout.add_line('L', x_col='time', y_col='value', series_col='serie', linked_to='S')
```

---

### 12. **Pie Chart / Donut Chart** (`pie`)
- **Tipo**: Gráfico circular (tarta/donut)
- **Método MatrixLayout**: `MatrixLayout.map_pie()`
- **Método ReactiveMatrixLayout**: `add_pie()`
- **Clase Chart**: `PieChart`
- **Render JS**: `renderPieD3()`
- **Parámetros principales**:
  - `category_col`: Columna de categorías
  - `value_col`: Columna de valores
  - `donut`: Si True, crea donut chart
  - `innerRadius`: Radio interno (para donut)
  - `interactive`: Habilita selección
  - `linked_to`: Enlaza a otra vista

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_pie('P', df, category_col='cat', value_col='val', donut=True)

# ReactiveMatrixLayout
layout.add_pie('P', category_col='cat', value_col='val', donut=True, innerRadius=60, linked_to='S')
```

---

### 13. **Violin Plot** (`violin`)
- **Tipo**: Gráfico de violín (distribución)
- **Método MatrixLayout**: `MatrixLayout.map_violin()`
- **Método ReactiveMatrixLayout**: `add_violin()`
- **Clase Chart**: `ViolinChart`
- **Render JS**: `renderViolinD3()`
- **Parámetros principales**:
  - `value_col`: Columna numérica
  - `category_col`: Columna de categorías
  - `bins`: Número de bins para KDE (por defecto 20)
  - `linked_to`: Enlaza a otra vista

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_violin('V', df, value_col='salario', category_col='dept', bins=20)

# ReactiveMatrixLayout
layout.add_violin('V', value_col='salario', category_col='dept', bins=20, linked_to='S')
```

---

### 14. **RadViz** (`radviz`)
- **Tipo**: Visualización radial de múltiples dimensiones
- **Método MatrixLayout**: `MatrixLayout.map_radviz()`
- **Método ReactiveMatrixLayout**: `add_radviz()`
- **Clase Chart**: `RadvizChart`
- **Render JS**: `renderRadVizD3()`
- **Parámetros principales**:
  - `features`: Lista de columnas numéricas (dimensiones)
  - `class_col`: Columna de clases/categorías
  - `linked_to`: Enlaza a otra vista

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_radviz('R', df, features=['f1', 'f2', 'f3'], class_col='label')

# ReactiveMatrixLayout
layout.add_radviz('R', features=['f1', 'f2', 'f3'], class_col='label', linked_to='S')
```

---

### 15. **Star Coordinates** (`star_coordinates`)
- **Tipo**: Coordenadas estelares (similar a RadViz)
- **Método MatrixLayout**: `MatrixLayout.map_star_coordinates()` (si existe)
- **Método ReactiveMatrixLayout**: `add_star_coordinates()`
- **Clase Chart**: `StarCoordinatesChart`
- **Render JS**: `renderStarCoordinatesD3()`
- **Parámetros principales**:
  - `features`: Lista de columnas numéricas
  - `class_col`: Columna de clases/categorías
  - `linked_to`: Enlaza a otra vista

**Ejemplo:**
```python
# ReactiveMatrixLayout
layout.add_star_coordinates('S', features=['f1', 'f2', 'f3'], class_col='label', linked_to='S')
```

---

### 16. **Parallel Coordinates** (`parallel_coordinates`)
- **Tipo**: Coordenadas paralelas (múltiples ejes)
- **Método MatrixLayout**: `MatrixLayout.map_parallel_coordinates()`
- **Método ReactiveMatrixLayout**: `add_parallel_coordinates()`
- **Clase Chart**: `ParallelCoordinatesChart`
- **Render JS**: `renderParallelCoordinatesD3()`
- **Parámetros principales**:
  - `dimensions`: Lista de columnas numéricas (opcional, usa todas por defecto)
  - `category_col`: Columna para categorías (colorear líneas)
  - `linked_to`: Enlaza a otra vista
  - **Características especiales**:
    - Ejes arrastrables y reordenables
    - Selección de líneas con click
    - Interactividad avanzada

**Ejemplo:**
```python
# MatrixLayout
MatrixLayout.map_parallel_coordinates('Y', df, dimensions=['f1', 'f2', 'f3'], category_col='class')

# ReactiveMatrixLayout
layout.add_parallel_coordinates('Y', dimensions=['f1', 'f2', 'f3'], category_col='class', linked_to='S')
```

---

### 17. **Confusion Matrix** (`confusion_matrix`)
- **Tipo**: Matriz de confusión (ML)
- **Método ReactiveMatrixLayout**: `add_confusion_matrix()`
- **Render JS**: `renderHeatmapD3()` (con datos de confusión)
- **Parámetros principales**:
  - `y_true_col`: Columna con etiquetas reales
  - `y_pred_col`: Columna con etiquetas predichas
  - `normalize`: Si True, muestra proporciones
  - `linked_to`: Enlaza a otra vista
  - **Requisito**: `scikit-learn` instalado

**Ejemplo:**
```python
# Solo en ReactiveMatrixLayout
layout.add_confusion_matrix('C', y_true_col='y_true', y_pred_col='y_pred', normalize=True, linked_to='S')
```

---

## 📊 Tabla Resumen

| # | Visualización | Tipo | MatrixLayout | ReactiveMatrixLayout | Chart Class | Render JS |
|---|---------------|------|--------------|---------------------|-------------|-----------|
| 1 | Círculo | Simple | ✅ | ❌ | - | SVG directo |
| 2 | Rectángulo | Simple | ✅ | ❌ | - | SVG directo |
| 3 | Línea | Simple | ✅ | ❌ | - | SVG directo |
| 4 | Scatter Plot | D3.js | ✅ | ✅ | ScatterChart | renderScatterPlotD3 |
| 5 | Bar Chart | D3.js | ✅ | ✅ | BarChart | renderBarChartD3 |
| 6 | Grouped Bar | D3.js | ✅ | ✅ | GroupedBarChart | renderBarChartD3 |
| 7 | Histogram | D3.js | ✅ | ✅ | HistogramChart | renderHistogramD3 |
| 8 | Boxplot | D3.js | ✅ | ✅ | BoxplotChart | renderBoxplotD3 |
| 9 | Heatmap | D3.js | ✅ | ✅ | HeatmapChart | renderHeatmapD3 |
| 10 | Correlation Heatmap | D3.js | ❌ | ✅ | - | renderHeatmapD3 |
| 11 | Line Chart | D3.js | ✅ | ✅ | LineChart | renderLineD3 |
| 12 | Pie/Donut Chart | D3.js | ✅ | ✅ | PieChart | renderPieD3 |
| 13 | Violin Plot | D3.js | ✅ | ✅ | ViolinChart | renderViolinD3 |
| 14 | RadViz | D3.js | ✅ | ✅ | RadvizChart | renderRadVizD3 |
| 15 | Star Coordinates | D3.js | ❌ | ✅ | StarCoordinatesChart | renderStarCoordinatesD3 |
| 16 | Parallel Coordinates | D3.js | ✅ | ✅ | ParallelCoordinatesChart | renderParallelCoordinatesD3 |
| 17 | Confusion Matrix | D3.js | ❌ | ✅ | - | renderHeatmapD3 |

---

## 🎯 Características por Visualización

### Interactividad

| Visualización | Brush Selection | Click Events | Zoom | Tooltips | Linked Views |
|---------------|----------------|--------------|------|----------|--------------|
| Scatter Plot | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bar Chart | ✅ | ❌ | ❌ | ✅ | ✅ |
| Grouped Bar | ✅ | ❌ | ❌ | ✅ | ✅ |
| Histogram | ✅ | ❌ | ❌ | ✅ | ✅ |
| Boxplot | ❌ | ❌ | ❌ | ✅ | ✅ |
| Heatmap | ❌ | ❌ | ❌ | ✅ | ✅ |
| Line Chart | ❌ | ❌ | ❌ | ✅ | ✅ |
| Pie Chart | ✅ | ❌ | ❌ | ✅ | ✅ |
| Violin Plot | ❌ | ❌ | ❌ | ✅ | ✅ |
| RadViz | ❌ | ❌ | ❌ | ✅ | ✅ |
| Star Coordinates | ❌ | ❌ | ❌ | ✅ | ✅ |
| Parallel Coordinates | ❌ | ✅ (líneas) | ❌ | ✅ | ✅ |

### Requisitos de Datos

| Visualización | Requiere DataFrame | Columnas Mínimas | Columnas Especiales |
|---------------|-------------------|------------------|---------------------|
| Scatter Plot | ⚠️ Opcional | 2 (x, y) | category_col, size_col |
| Bar Chart | ⚠️ Opcional | 1 (category) | value_col |
| Grouped Bar | ⚠️ Opcional | 2 (main, sub) | value_col |
| Histogram | ⚠️ Opcional | 1 (numérica) | - |
| Boxplot | ⚠️ Opcional | 1 (numérica) | category_col |
| Heatmap | ⚠️ Opcional | 3 (x, y, value) | - |
| Line Chart | ⚠️ Opcional | 2 (x, y) | series_col |
| Pie Chart | ⚠️ Opcional | 1 (category) | value_col |
| Violin Plot | ⚠️ Opcional | 1 (numérica) | category_col |
| RadViz | ✅ **Sí** | 2+ (features) | class_col |
| Star Coordinates | ✅ **Sí** | 2+ (features) | class_col |
| Parallel Coordinates | ✅ **Sí** | 2+ (dimensions) | category_col |
| Confusion Matrix | ✅ **Sí** | 2 (y_true, y_pred) | - |

---

## 📝 Notas Importantes

1. **Elementos Simples**: Los círculos, rectángulos y líneas no requieren D3.js y se renderizan directamente con SVG.

2. **ReactiveMatrixLayout**: Algunas visualizaciones solo están disponibles en `ReactiveMatrixLayout`:
   - Correlation Heatmap
   - Star Coordinates
   - Confusion Matrix

3. **Linked Views**: Todas las visualizaciones en `ReactiveMatrixLayout` pueden enlazarse usando `linked_to`.

4. **Interactividad**: La mayoría de gráficos soportan `interactive=True` para habilitar selección con brush.

5. **Requisitos Especiales**:
   - **Confusion Matrix**: Requiere `scikit-learn`
   - **RadViz/Star Coordinates/Parallel Coordinates**: Requieren DataFrame de pandas

---

## 🔗 Referencias

- **Archivos de implementación**: `BESTLIB/charts/`
- **Renderizado JavaScript**: `BESTLIB/matrix.js`
- **Métodos MatrixLayout**: `BESTLIB/matrix.py` y `BESTLIB/layouts/matrix.py`
- **Métodos ReactiveMatrixLayout**: `BESTLIB/reactive.py` y `BESTLIB/layouts/reactive.py`

---

**Última actualización**: Análisis completo del código base de BESTLIB

