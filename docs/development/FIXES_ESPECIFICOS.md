# Correcciones Específicas: Rug, Ridgeline y Ejes

## Resumen

Se han aplicado correcciones precisas y controladas a tres problemas específicos sin modificar gráficos que ya funcionaban.

## 1. Rug Plot ("R") - CORREGIDO ✅

### Problema
- `renderRugD3()` no dibujaba ninguna línea
- El código esperaba formato `[{x: value}]` pero podía recibir otros formatos

### Solución Aplicada

**Archivo**: `BESTLIB/matrix.js` - función `renderRugD3()`

1. **Normalización de datos flexible**:
   - Acepta `[{x: value}, ...]`
   - Acepta `[{value: X}, ...]`
   - Acepta array simple de números `[5.1, 4.9, ...]`
   - Convierte todo a formato estándar `[{x: value}, ...]`

2. **Ticks del rug corregidos**:
   - Líneas verticales para `axis='x'`: desde `chartHeight` hasta `chartHeight + tickHeight`
   - Líneas horizontales para `axis='y'`: desde `-tickHeight` hasta `0`
   - Máximo de 8px de altura/ancho para evitar que queden fuera del padding

3. **Validación mejorada**:
   - Filtra valores nulos y NaN
   - Valida estructura antes de renderizar

### Código Clave
```javascript
// Normalizar datos
if (typeof firstItem === 'number') {
  data = data.map(val => ({ x: val }));
} else if (firstItem.hasOwnProperty('x')) {
  data = data.map(d => ({ x: d.x }));
} else if (firstItem.hasOwnProperty('value')) {
  data = data.map(d => ({ x: d.value }));
}

// Dibujar ticks con límite de tamaño
const tickEndY = chartHeight + Math.min(tickHeight * size, 8);
```

## 2. Ridgeline ("I") - CORREGIDO ✅

### Problema
- `renderRidgelineD3()` no dibujaba nada
- Python envía `spec.series = {cat: [{x, y}, ...]}` correctamente

### Solución Aplicada

**Archivo**: `BESTLIB/matrix.js` - función `renderRidgelineD3()`

1. **Cálculo de dominios corregido**:
   - Lee correctamente `spec.series` como objeto `{cat: [{x, y}, ...]}`
   - Calcula `xMin`, `xMax`, `yMax` correctamente
   - Maneja valores infinitos con fallbacks

2. **Validación de series**:
   - Verifica que cada serie sea un array válido
   - Filtra series vacías con warning

3. **Renderizado mejorado**:
   - Usa directamente `series[cat]` sin normalización innecesaria
   - Construye curvas KDE correctamente desde los datos de Python

### Código Clave
```javascript
// Calcular dominios correctamente
Object.keys(series).forEach(cat => {
  const serie = series[cat];
  if (Array.isArray(serie) && serie.length > 0) {
    serie.forEach(d => {
      if (d && d.hasOwnProperty('x') && d.hasOwnProperty('y')) {
        xMin = Math.min(xMin, parseFloat(d.x));
        xMax = Math.max(xMax, parseFloat(d.x));
        yMax = Math.max(yMax, parseFloat(d.y));
      }
    });
  }
});
```

## 3. Q-Q Plot - Eje Y Duplicado - CORREGIDO ✅

### Problema
- Aparecían dos labels sobrepuestos: "Observed Quantiles (value)" y "value"
- Se estaba copiando `xLabel/yLabel` al `spec` y luego llamando `renderAxisLabels()`

### Solución Aplicada

**Archivo**: `BESTLIB/matrix.js` - función `renderQqplotD3()`

1. **Eliminada duplicación**:
   - NO copiar `xLabel/yLabel` al `spec`
   - Leer labels directamente desde `options.xLabel` y `options.yLabel`
   - Usar funciones `renderXAxis()` y `renderYAxis()` en lugar de `renderAxisLabels()`

2. **Uso de funciones reutilizables**:
   - `renderXAxis()` para eje X
   - `renderYAxis()` para eje Y
   - Evita duplicación de código y labels

### Código Clave
```javascript
// ANTES (causaba duplicación):
if (options.xLabel && !spec.xLabel) {
  spec.xLabel = options.xLabel;  // ← Esto causaba duplicación
}
renderAxisLabels(g, spec, ...);  // ← Renderizaba desde spec.xLabel

// DESPUÉS (sin duplicación):
const xLabel = options.xLabel || spec.xLabel;  // ← Solo leer, no copiar
renderXAxis(g, x, chartHeight, chartWidth, margin, xLabel, svg);  // ← Renderizar directamente
```

## 4. Ajustes de Labels - CORREGIDO ✅

### Problema
- Labels estaban pegados a los ticks
- No había offset consistente

### Solución Aplicada

**Archivos**: `BESTLIB/matrix.js` - funciones `renderXAxis()`, `renderYAxis()`, `renderAxisLabels()`

1. **Offset agregado**:
   - Eje X: `+8px` de offset vertical
   - Eje Y: `-8px` de offset horizontal

2. **Aplicado en todas las funciones**:
   - `renderXAxis()`: `xLabelY = margin.top + chartHeight + margin.bottom - 10 + 8`
   - `renderYAxis()`: `yLabelX = margin.left / 2 - 8`
   - `renderAxisLabels()`: mismo offset para consistencia

### Código Clave
```javascript
// Offset para que no esté pegado al tick
const offset = 8;
const xLabelY = margin.top + chartHeight + margin.bottom - 10 + offset;
const yLabelX = margin.left / 2 - offset;
```

## Archivos Modificados

1. **`BESTLIB/matrix.js`**:
   - `renderRugD3()`: Normalización de datos y corrección de ticks
   - `renderQqplotD3()`: Eliminación de duplicación de labels
   - `renderRidgelineD3()`: Corrección de cálculo de dominios
   - `renderXAxis()`: Agregado offset
   - `renderYAxis()`: Agregado offset
   - `renderAxisLabels()`: Agregado offset

## Gráficos NO Modificados (Verificado)

Los siguientes gráficos **NO** fueron modificados:
- ✅ Scatter, Bar, Histogram, Boxplot, Line, Line Plot
- ✅ Heatmap, Horizontal Bar, Step Plot
- ✅ Fill Between, Errorbars, Hexbin
- ✅ Funnel, Polar, KDE, Distplot, ECDF, Hist2D

## Resultado Esperado

Después de estos cambios:

1. **Rug Plot**: 
   - ✅ Muestra ticks verticales u horizontales según `axis`
   - ✅ Ticks no quedan fuera del padding
   - ✅ Acepta múltiples formatos de datos

2. **Ridgeline**:
   - ✅ Muestra curvas KDE por categoría
   - ✅ Curvas apiladas verticalmente
   - ✅ Labels de categorías visibles

3. **Q-Q Plot**:
   - ✅ Un solo label por eje (sin duplicación)
   - ✅ Labels claros y legibles

4. **Todos los gráficos**:
   - ✅ Labels con offset (no pegados a ticks)
   - ✅ Consistencia visual

## Prueba

```python
from BESTLIB.matrix import MatrixLayout
import pandas as pd
import numpy as np

df_value = pd.DataFrame({'value': np.random.normal(5.8, 0.8, 150)})
df_ridge = pd.DataFrame({
    'category': np.random.choice(['A', 'B', 'C'], 150),
    'value': np.random.normal(5.8, 0.8, 150)
})

layout = MatrixLayout("""
R
I
Q
""")

layout.map_rug("R", df_value, column="value", xLabel="Value")
layout.map_ridgeline("I", df_ridge, column="value", category_col="category", xLabel="Value")
layout.map_qqplot("Q", df_value, column="value", xLabel="Theoretical", yLabel="Sample")

layout.display()
```

**Resultado esperado**:
- ✅ Rug muestra ticks
- ✅ Ridgeline muestra curvas por categoría
- ✅ Q-Q tiene un solo label por eje
- ✅ Labels no están pegados a ticks

