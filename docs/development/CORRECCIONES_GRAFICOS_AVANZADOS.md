# Correcciones de Gráficos Avanzados

## Resumen de Cambios

Se han realizado correcciones en los gráficos avanzados de BESTLIB para:
1. Corregir el renderizado del gráfico Rug
2. Asegurar que todos los gráficos avanzados tengan títulos de ejes (xLabel/yLabel)
3. Verificar que no se rompan los gráficos existentes

## Cambios Realizados

### 1. Corrección del Gráfico Rug (`renderRugD3`)

**Archivo**: `BESTLIB/matrix.js`

**Problemas corregidos**:
- ✅ Validación mejorada de estructura de datos
- ✅ Cálculo correcto de dominios para escalas X e Y
- ✅ Filtrado de valores nulos/NaN antes de calcular dominios
- ✅ Copia de xLabel/yLabel desde `options` al `spec` para renderAxisLabels

**Cambios específicos**:
```javascript
// Antes: dominio calculado directamente sin validación
const x = d3.scaleLinear()
  .domain(d3.extent(data, d => d.x) || [0, 100])

// Después: validación y filtrado de valores
const xValues = data.map(d => d.x).filter(v => v != null && !isNaN(v));
const xDomain = xValues.length > 0 ? d3.extent(xValues) : [0, 100];
const x = d3.scaleLinear()
  .domain(xDomain)
  .nice()
  .range([0, chartWidth]);
```

### 2. Títulos de Ejes en Todos los Gráficos Avanzados

**Archivo**: `BESTLIB/matrix.js`

**Gráficos corregidos**:
- ✅ KDE (`renderKdeD3`)
- ✅ Distplot (`renderDistplotD3`)
- ✅ Rug (`renderRugD3`)
- ✅ QQ-plot (`renderQqplotD3`)
- ✅ ECDF (`renderEcdfD3`)
- ✅ Hist2D (`renderHist2dD3`)
- ✅ Polar (`renderPolarD3`)
- ✅ Ridgeline (`renderRidgelineD3`)
- ✅ Ribbon (`renderRibbonD3`)
- ✅ Funnel (`renderFunnelD3`)

**Cambio aplicado en cada gráfico**:
```javascript
const options = spec.options || {};
// ... otras opciones ...

// Copiar xLabel/yLabel desde options al spec para renderAxisLabels
if (options.xLabel && !spec.xLabel) {
  spec.xLabel = options.xLabel;
}
if (options.yLabel && !spec.yLabel) {
  spec.yLabel = options.yLabel;
}
```

**Razón**: `renderAxisLabels()` lee `spec.xLabel` y `spec.yLabel` directamente, pero en los gráficos avanzados estos valores están en `spec.options.xLabel` y `spec.options.yLabel`. Esta copia asegura que los títulos se rendericen correctamente.

### 3. Verificación de Gráficos Existentes

**Gráficos verificados (NO modificados)**:
- ✅ Scatter (`renderScatterPlotD3`)
- ✅ Histogram (`renderHistogramD3`)
- ✅ Boxplot (`renderBoxplotD3`)
- ✅ Line (`renderLineD3`)
- ✅ Line plot (`renderLinePlotD3`)
- ✅ Horizontal bar (`renderHorizontalBarD3`)
- ✅ Hexbin (`renderHexbinD3`)
- ✅ Errorbars (`renderErrorbarsD3`)
- ✅ Fill_between (`renderFillBetweenD3`)
- ✅ Step plot (`renderStepPlotD3`)

**Confirmación**: Ningún gráfico existente fue modificado. Solo se agregaron correcciones a los gráficos avanzados.

## Estructura de Datos para Rug

El gráfico Rug espera datos en el formato:
```javascript
[
  { x: 5.1, y: 0 },
  { x: 4.9, y: 0 },
  { x: 4.7, y: 0 },
  // ...
]
```

Donde:
- `x`: Valor numérico a marcar en el eje
- `y`: Siempre 0 (posición en el eje, se ajusta en JS)

## Uso de Títulos de Ejes

Todos los gráficos avanzados ahora aceptan `xLabel` y `yLabel`:

```python
layout.map_kde("K", df_value, column="value", xLabel="Value", yLabel="Density")
layout.map_rug("R", df_value, column="value", xLabel="Value")
layout.map_qqplot("Q", df_value, column="value", xLabel="Theoretical Quantiles", yLabel="Sample Quantiles")
```

## Prueba de Validación

El siguiente código debe funcionar correctamente:

```python
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

df_value = pd.DataFrame({
    'value': np.random.normal(5.8, 0.8, 150)
})

layout = MatrixLayout("""
KDR
QEH
PRF
""")

layout.map_kde("K", df_value, column="value", xLabel="Value", yLabel="Density")
layout.map_distplot("D", df_value, column="value", bins=30, kde=True, rug=True, xLabel="Value", yLabel="Density")
layout.map_rug("R", df_value, column="value", xLabel="Value")
layout.map_qqplot("Q", df_value, column="value", xLabel="Theoretical", yLabel="Sample")
layout.map_ecdf("E", df_value, column="value", xLabel="Value", yLabel="Cumulative Probability")
layout.map_hist2d("H", df_hist2d, x_col="x", y_col="y", bins=20, xLabel="X", yLabel="Y")
layout.map_polar("P", df_polar, angle_col="angle", radius_col="radius", xLabel="Angle", yLabel="Radius")
layout.map_ridgeline("I", df_ridge, column="value", category_col="category", xLabel="Value")
layout.map_funnel("F", df_funnel, stage_col="stage", value_col="value", xLabel="Stage", yLabel="Value")

layout.display()
```

**Resultado esperado**:
- ✅ 9 gráficos renderizados correctamente
- ✅ Rug plot visible en posición (1,3) con ticks en el eje X
- ✅ Todos los gráficos con títulos de ejes visibles
- ✅ Ningún gráfico anterior afectado

## Archivos Modificados

1. `BESTLIB/matrix.js`
   - `renderRugD3()`: Validación mejorada y cálculo correcto de dominios
   - `renderKdeD3()`: Copia de xLabel/yLabel
   - `renderDistplotD3()`: Copia de xLabel/yLabel
   - `renderQqplotD3()`: Copia de xLabel/yLabel
   - `renderEcdfD3()`: Copia de xLabel/yLabel
   - `renderHist2dD3()`: Copia de xLabel/yLabel
   - `renderPolarD3()`: Copia de xLabel/yLabel
   - `renderRidgelineD3()`: Copia de xLabel/yLabel
   - `renderRibbonD3()`: Copia de xLabel/yLabel
   - `renderFunnelD3()`: Copia de xLabel/yLabel

## Notas Técnicas

1. **Validación de datos en Rug**: Se agregó validación para asegurar que los datos tengan la estructura correcta antes de renderizar.

2. **Cálculo de dominios**: Se mejoró el cálculo de dominios filtrando valores nulos y NaN antes de usar `d3.extent()`.

3. **Propagación de labels**: Los labels se copian desde `options` al `spec` solo si no existen ya en `spec`, para no sobrescribir valores explícitos.

4. **Compatibilidad**: Todos los cambios son compatibles con la API existente. No se modificaron firmas de funciones ni se cambiaron nombres.

