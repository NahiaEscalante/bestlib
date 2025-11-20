# 📊 Visualizaciones Disponibles en BESTLIB

**Total: 23 tipos de visualizaciones**

---

## 🎨 Categoría 1: Elementos Visuales Simples (3)

Elementos SVG básicos que no requieren D3.js.

### 1. **Círculo** (`circle`)
- Método: `MatrixLayout.map()` con `'shape': 'circle'`
- Parámetros: `color`, `size`, `opacity`, `stroke`, `strokeWidth`

### 2. **Rectángulo** (`rect`)
- Método: `MatrixLayout.map()` con `'shape': 'rect'`
- Parámetros: `color`, `width`, `height`, `borderRadius`, `opacity`

### 3. **Línea** (`line`)
- Método: `MatrixLayout.map()` con `'shape': 'line'`
- Parámetros: `color`, `strokeWidth`, `x1`, `y1`, `x2`, `y2`

---

## 📊 Categoría 2: Gráficos D3.js Interactivos (20)

### 4. **Scatter Plot** (`scatter`)
- ✅ MatrixLayout: `map_scatter()`
- ✅ ReactiveMatrixLayout: `add_scatter()`
- Características: Brush selection, zoom, tooltips, linked views
- Parámetros: `x_col`, `y_col`, `category_col`, `color_col`, `size_col`, `interactive`

### 5. **Bar Chart** (`bar`)
- ✅ MatrixLayout: `map_barchart()`
- ✅ ReactiveMatrixLayout: `add_barchart()`
- Características: Barras verticales, tooltips, linked views
- Parámetros: `category_col`, `value_col`, `interactive`, `color`

### 6. **Grouped Bar Chart** (`grouped_bar`)
- ✅ MatrixLayout: `map_grouped_barchart()`
- ✅ ReactiveMatrixLayout: `add_grouped_barchart()`
- Características: Barras agrupadas por categorías
- Parámetros: `main_col`, `sub_col`, `value_col`, `interactive`

### 7. **Histogram** (`histogram`)
- ✅ MatrixLayout: `map_histogram()`
- ✅ ReactiveMatrixLayout: `add_histogram()`
- Características: Distribución de frecuencias, linked views
- Parámetros: `column`, `bins`, `linked_to`, `xLabel`, `yLabel`

### 8. **Boxplot** (`boxplot`)
- ✅ MatrixLayout: `map_boxplot()`
- ✅ ReactiveMatrixLayout: `add_boxplot()`
- Características: Diagrama de cajas y bigotes, tooltips
- Parámetros: `column`, `category_col`, `linked_to`, `xLabel`, `yLabel`

### 9. **Heatmap** (`heatmap`)
- ✅ MatrixLayout: `map_heatmap()`
- ✅ ReactiveMatrixLayout: `add_heatmap()`
- Características: Mapa de calor 2D, tooltips
- Parámetros: `x_col`, `y_col`, `value_col`, `colorMap`, `linked_to`

### 10. **Line Chart** (`line`)
- ✅ MatrixLayout: `map_line()`
- ✅ ReactiveMatrixLayout: `add_line()`
- Características: Gráfico de líneas multi-series
- Parámetros: `x_col`, `y_col`, `series_col`, `linked_to`, `axes`

### 11. **Pie Chart / Donut Chart** (`pie`)
- ✅ MatrixLayout: `map_pie()`
- ✅ ReactiveMatrixLayout: `add_pie()`
- Características: Gráfico circular, donut chart opcional
- Parámetros: `category_col`, `value_col`, `donut`, `innerRadius`, `interactive`

### 12. **Violin Plot** (`violin`)
- ✅ MatrixLayout: `map_violin()`
- ✅ ReactiveMatrixLayout: `add_violin()`
- Características: Distribución de densidad
- Parámetros: `value_col`, `category_col`, `bins`, `linked_to`

### 13. **RadViz** (`radviz`)
- ✅ MatrixLayout: `map_radviz()`
- ✅ ReactiveMatrixLayout: `add_radviz()`
- Características: Visualización radial multi-dimensional
- Parámetros: `features`, `class_col`, `linked_to`

### 14. **Star Coordinates** (`star_coordinates`)
- ✅ MatrixLayout: `map_star_coordinates()` (si existe)
- ✅ ReactiveMatrixLayout: `add_star_coordinates()`
- Características: Coordenadas estelares
- Parámetros: `features`, `class_col`, `linked_to`

### 15. **Parallel Coordinates** (`parallel_coordinates`)
- ✅ MatrixLayout: `map_parallel_coordinates()`
- ✅ ReactiveMatrixLayout: `add_parallel_coordinates()`
- Características: Ejes paralelos, arrastrables, selección de líneas
- Parámetros: `dimensions`, `category_col`, `linked_to`

### 16. **Line Plot** (`line_plot`) ⭐ **NUEVO**
- ✅ MatrixLayout: `map_line_plot()`
- ✅ ReactiveMatrixLayout: `add_line_plot()`
- Características: Gráfico de líneas completo con múltiples series, marcadores
- Parámetros: `x_col`, `y_col`, `series_col`, `strokeWidth`, `markers`, `xLabel`, `yLabel`

### 17. **Horizontal Bar** (`horizontal_bar`) ⭐ **NUEVO**
- ✅ MatrixLayout: `map_horizontal_bar()`
- ✅ ReactiveMatrixLayout: `add_horizontal_bar()`
- Características: Barras horizontales
- Parámetros: `category_col`, `value_col`, `xLabel`, `yLabel`

### 18. **Hexbin** (`hexbin`) ⭐ **NUEVO**
- ✅ MatrixLayout: `map_hexbin()`
- ✅ ReactiveMatrixLayout: `add_hexbin()`
- Características: Visualización de densidad hexagonal
- Parámetros: `x_col`, `y_col`, `bins`, `colorScale`, `xLabel`, `yLabel`

### 19. **Errorbars** (`errorbars`) ⭐ **NUEVO**
- ✅ MatrixLayout: `map_errorbars()`
- ✅ ReactiveMatrixLayout: `add_errorbars()`
- Características: Barras de error en X e Y
- Parámetros: `x_col`, `y_col`, `yerr`, `xerr`, `xLabel`, `yLabel`

### 20. **Fill Between** (`fill_between`) ⭐ **NUEVO**
- ✅ MatrixLayout: `map_fill_between()`
- ✅ ReactiveMatrixLayout: `add_fill_between()`
- Características: Área rellena entre dos líneas
- Parámetros: `x_col`, `y1`, `y2`, `color`, `opacity`, `showLines`, `xLabel`, `yLabel`

### 21. **Step Plot** (`step_plot`) ⭐ **NUEVO**
- ✅ MatrixLayout: `map_step()`
- ✅ ReactiveMatrixLayout: `add_step()`
- Características: Gráfico escalonado
- Parámetros: `x_col`, `y_col`, `stepType` ('step', 'stepBefore', 'stepAfter'), `strokeWidth`, `xLabel`, `yLabel`

### 22. **Correlation Heatmap** (`correlation_heatmap`)
- ❌ MatrixLayout: No disponible
- ✅ ReactiveMatrixLayout: `add_correlation_heatmap()`
- Características: Matriz de correlación
- Parámetros: `linked_to`, `colorScale`

### 23. **Confusion Matrix** (`confusion_matrix`)
- ❌ MatrixLayout: No disponible
- ✅ ReactiveMatrixLayout: `add_confusion_matrix()`
- Características: Matriz de confusión para ML
- Parámetros: `y_true_col`, `y_pred_col`, `normalize`, `linked_to`
- Requisito: `scikit-learn` instalado

---

## 📋 Tabla Resumen Completa

| # | Visualización | Tipo | MatrixLayout | ReactiveMatrixLayout | Estilos Unificados |
|---|---------------|------|--------------|---------------------|-------------------|
| 1 | Círculo | Simple | ✅ | ❌ | - |
| 2 | Rectángulo | Simple | ✅ | ❌ | - |
| 3 | Línea | Simple | ✅ | ❌ | - |
| 4 | Scatter Plot | D3.js | ✅ | ✅ | ✅ |
| 5 | Bar Chart | D3.js | ✅ | ✅ | ✅ |
| 6 | Grouped Bar | D3.js | ✅ | ✅ | ⏳ |
| 7 | Histogram | D3.js | ✅ | ✅ | ✅ |
| 8 | Boxplot | D3.js | ✅ | ✅ | ✅ |
| 9 | Heatmap | D3.js | ✅ | ✅ | ⏳ |
| 10 | Line Chart | D3.js | ✅ | ✅ | ⏳ |
| 11 | Pie/Donut | D3.js | ✅ | ✅ | ⏳ |
| 12 | Violin Plot | D3.js | ✅ | ✅ | ⏳ |
| 13 | RadViz | D3.js | ✅ | ✅ | ⏳ |
| 14 | Star Coordinates | D3.js | ⚠️ | ✅ | ⏳ |
| 15 | Parallel Coordinates | D3.js | ✅ | ✅ | ⏳ |
| 16 | **Line Plot** ⭐ | D3.js | ✅ | ✅ | ⏳ |
| 17 | **Horizontal Bar** ⭐ | D3.js | ✅ | ✅ | ⏳ |
| 18 | **Hexbin** ⭐ | D3.js | ✅ | ✅ | ⏳ |
| 19 | **Errorbars** ⭐ | D3.js | ✅ | ✅ | ⏳ |
| 20 | **Fill Between** ⭐ | D3.js | ✅ | ✅ | ⏳ |
| 21 | **Step Plot** ⭐ | D3.js | ✅ | ✅ | ⏳ |
| 22 | Correlation Heatmap | D3.js | ❌ | ✅ | ⏳ |
| 23 | Confusion Matrix | D3.js | ❌ | ✅ | ⏳ |

**Leyenda:**
- ✅ Disponible
- ❌ No disponible
- ⚠️ Parcialmente disponible
- ⏳ Pendiente aplicar estilos unificados
- ⭐ Nuevo gráfico agregado recientemente

---

## 🎨 Estilos Unificados

Los siguientes gráficos ya tienen estilos unificados aplicados:
- ✅ Scatter Plot
- ✅ Bar Chart
- ✅ Histogram
- ✅ Boxplot
- ✅ Line Plot (parcial)

**Estilos incluyen:**
- Ejes más gruesos (2px) y profesionales
- Tipografía consistente (11px ticks, 13px labels)
- Colores unificados (#4a90e2 principal, #ff6b35 selección)
- Transiciones uniformes (300ms)
- Opacidades consistentes

---

## 📝 Notas

1. **Nuevos gráficos**: Los 6 gráficos marcados con ⭐ fueron agregados recientemente y están completamente funcionales.

2. **Estilos unificados**: Se está aplicando progresivamente el sistema de estilos unificados a todos los gráficos.

3. **MatrixLayout vs ReactiveMatrixLayout**:
   - `MatrixLayout`: Gráficos estáticos o con selección básica
   - `ReactiveMatrixLayout`: Gráficos con vistas enlazadas y actualización reactiva

4. **Requisitos especiales**:
   - Confusion Matrix requiere `scikit-learn`
   - RadViz/Star Coordinates/Parallel Coordinates requieren DataFrame de pandas

---

**Última actualización**: Incluye los 6 nuevos gráficos y sistema de estilos unificados

