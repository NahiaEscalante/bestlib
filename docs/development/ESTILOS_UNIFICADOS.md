# 🎨 Sistema de Estilos Unificados para BESTLIB

## 📋 Resumen

Se ha implementado un sistema completo de estilos unificados para todos los gráficos de BESTLIB, garantizando una apariencia visual consistente y profesional en todos los tipos de visualización.

## ✅ Cambios Implementados

### 1. **Variables CSS Unificadas** (`BESTLIB/style.css`)

Se agregaron variables CSS en `:root` para:

- **Colores principales:**
  - `--chart-primary-color: #4a90e2` (azul principal)
  - `--chart-primary-hover: #357abd` (azul hover)
  - `--chart-selection-color: #ff6b35` (naranja para selección)
  - `--chart-text-color: #000000` (negro para texto)
  - `--chart-grid-color: #e0e0e0` (gris para grid)

- **Grosores de línea:**
  - `--chart-line-width: 2px` (líneas estándar)
  - `--chart-line-width-thick: 2.5px` (líneas gruesas)
  - `--chart-line-width-thin: 1.5px` (líneas finas)
  - `--chart-axis-width: 2px` (ejes más gruesos y profesionales)

- **Opacidades:**
  - `--chart-opacity-default: 1`
  - `--chart-opacity-hover: 0.85`
  - `--chart-opacity-selected: 1`
  - `--chart-opacity-unselected: 0.3`
  - `--chart-opacity-fill: 0.3`

- **Tipografía:**
  - `--chart-label-font-size: 13px`
  - `--chart-label-font-weight: 700`
  - `--chart-tick-font-size: 11px`
  - `--chart-tick-font-weight: 600`

- **Transiciones:**
  - `--chart-transition-duration: 300ms`
  - `--chart-transition-duration-slow: 500ms`

### 2. **Clases CSS Reutilizables**

Se crearon clases CSS para aplicar estilos consistentes:

- `.bestlib-axis` - Ejes unificados
- `.bestlib-axis-label` - Etiquetas de ejes
- `.bestlib-point` - Puntos en scatter plots
- `.bestlib-point-selected` - Puntos seleccionados
- `.bestlib-bar` - Barras en bar charts
- `.bestlib-line` - Líneas en line plots
- `.bestlib-area` - Áreas rellenas
- `.bestlib-marker` - Marcadores
- `.bestlib-box` - Cajas en boxplots
- `.bestlib-median` - Línea mediana en boxplots
- `.bestlib-hexbin` - Celdas hexagonales
- `.bestlib-errorbar` - Barras de error
- `.bestlib-grid` - Grid de fondo

### 3. **Funciones Helper en JavaScript** (`BESTLIB/matrix.js`)

Se agregaron funciones helper:

- `getUnifiedStyles()` - Retorna objeto con valores de estilo estándar
- `applyUnifiedAxisStyles(axisSelection)` - Aplica estilos unificados a ejes D3

### 4. **Gráficos Actualizados**

#### ✅ Scatter Plot (`renderScatterPlotD3`)
- Puntos usan `bestlib-point` class
- Colores unificados desde `getUnifiedStyles()`
- Ejes usan `applyUnifiedAxisStyles()`
- Puntos seleccionados usan `bestlib-point-selected`

#### ✅ Bar Chart (`renderBarChartD3`)
- Ejes usan `applyUnifiedAxisStyles()`
- Etiquetas de ejes usan clases unificadas

#### ✅ Histogram (`renderHistogramD3`)
- Ejes usan `applyUnifiedAxisStyles()`
- Etiquetas de ejes usan clases unificadas

#### ✅ Boxplot (`renderBoxplotD3`)
- Ejes usan `applyUnifiedAxisStyles()`
- Cajas usan `bestlib-box` class
- Mediana usa `bestlib-median` class
- Colores unificados

#### ✅ Line Plot (`renderLinePlotD3`)
- Ejes usan `applyUnifiedAxisStyles()`
- Etiquetas de ejes usan clases unificadas

#### ⏳ Pendientes (aplicar mismo patrón):
- Horizontal Bar
- Hexbin
- Errorbars
- Fill Between
- Step Plot
- Heatmap
- Pie
- Violin
- RadViz
- Star Coordinates
- Parallel Coordinates

## 🎯 Beneficios

1. **Consistencia Visual:** Todos los gráficos comparten el mismo estilo
2. **Mantenibilidad:** Cambios globales se hacen en un solo lugar (CSS)
3. **Profesionalismo:** Ejes más gruesos (2px), tipografía consistente
4. **Flexibilidad:** Variables CSS permiten personalización fácil
5. **Rendimiento:** Clases CSS son más eficientes que estilos inline

## 📝 Uso

Los estilos se aplican automáticamente. No se requiere cambio en la API del usuario.

Para personalizar, modificar variables CSS en `BESTLIB/style.css`:

```css
:root {
  --chart-primary-color: #4a90e2;  /* Cambiar color principal */
  --chart-axis-width: 2px;         /* Cambiar grosor de ejes */
  --chart-label-font-size: 13px;   /* Cambiar tamaño de labels */
}
```

## 🔄 Próximos Pasos

1. Completar actualización de todos los gráficos restantes
2. Aplicar estilos unificados a tooltips
3. Unificar transiciones en todos los gráficos
4. Documentar paleta de colores por categoría

## 📄 Archivos Modificados

- `BESTLIB/style.css` - Variables CSS y clases reutilizables
- `BESTLIB/matrix.js` - Funciones helper y actualización de renderers

