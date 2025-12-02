# Investigación de Errores en BESTLIB

## Resumen Ejecutivo

Este documento presenta una investigación detallada de los errores encontrados durante las pruebas de los 30 gráficos de la librería BESTLIB. Los errores se clasifican en dos categorías principales:

1. **Errores que rompen el código** (excepciones en tiempo de ejecución)
2. **Gráficos que no se visualizan** (el código corre sin errores pero no se muestra nada)

---

## 1. Errores que Rompen el Código

### 1.1. ChartError: "El spec debe incluir 'data'"

**Gráficos afectados:**
- Heatmap
- Line Plot
- Confusion Matrix

**Error completo:**
```
ChartError: El spec debe incluir 'data'
```

**Ubicación del error:**
- `BESTLIB/charts/spec_utils.py:11-12` en la función `validate_spec()`

**Análisis:**

El problema radica en que `validate_spec()` requiere que todos los specs tengan un campo `'data'`, pero algunos gráficos generan specs con estructuras diferentes:

1. **Heatmap** (`BESTLIB/charts/heatmap.py:19-21`):
   - `get_spec()` retorna: `{'type': 'heatmap', 'cells': [...], 'x_labels': [...], 'y_labels': [...]}`
   - **NO incluye** `'data'`, sino `'cells'`, `'x_labels'`, `'y_labels'`

2. **Line Plot** (`BESTLIB/charts/line_plot.py:131-134`):
   - `get_spec()` retorna: `{'type': 'line_plot', 'series': {...}, ...}`
   - **NO incluye** `'data'`, sino `'series'`

3. **Confusion Matrix** (`BESTLIB/layouts/reactive.py:3364`):
   - Llama a `MatrixLayout.map_heatmap()` que genera un spec con `'data'` (línea 1311 de `matrix.py`)
   - Sin embargo, cuando se llama desde `add_confusion_matrix`, el spec generado pasa por `validate_spec()` antes de ser registrado
   - **Hipótesis**: El spec generado por `map_heatmap()` SÍ tiene `'data'`, pero algo en el flujo de `add_confusion_matrix` está perdiendo o modificando el spec antes de que llegue a `validate_spec()`

**Flujo de validación:**

1. `ReactiveMatrixLayout.add_heatmap()` → `MatrixLayout.map_heatmap()` → genera spec con `'data'`
2. `ReactiveMatrixLayout.add_line_plot()` → `MatrixLayout.map_line_plot()` → `ChartRegistry.get('line_plot').get_spec()` → genera spec con `'series'` (NO `'data'`)
3. `ReactiveMatrixLayout.add_confusion_matrix()` → `MatrixLayout.map_heatmap()` → genera spec con `'data'`, pero luego se valida

**Causa raíz:**

El problema es una **inconsistencia en la estructura de specs**:

- Algunos gráficos usan `'data'` (scatter, bar, pie, etc.)
- Otros usan `'series'` (line_plot)
- Otros usan `'cells'` (heatmap)
- Otros usan `'rows'`, `'groups'`, `'series'` (grouped_bar)

Pero `validate_spec()` solo valida la presencia de `'data'`, lo cual es demasiado restrictivo.

**Supuestos:**

1. **Supuesto 1**: `validate_spec()` fue diseñado para validar specs que siempre tienen `'data'`, pero algunos gráficos nuevos no siguen esta convención.

2. **Supuesto 2**: Los gráficos que usan estructuras diferentes (`'series'`, `'cells'`, etc.) deberían ser excluidos de la validación de `'data'`, o `validate_spec()` debería ser más flexible.

3. **Supuesto 3**: Para `Confusion Matrix`, el spec generado por `map_heatmap()` SÍ tiene `'data'`, pero el problema podría estar en cómo se llama `map_heatmap()` desde `add_confusion_matrix()` - específicamente, el DataFrame que se pasa después de `melt()` podría no tener las columnas esperadas.

**Evidencia:**

- `BESTLIB/matrix.py:1309-1315`: `map_heatmap()` genera `spec = {'type': 'heatmap', 'data': cells, ...}`
- `BESTLIB/charts/heatmap.py:19-21`: `HeatmapChart.get_spec()` genera `{'type': 'heatmap', 'cells': ..., ...}` (sin `'data'`)
- `BESTLIB/charts/line_plot.py:131-134`: `LinePlotChart.get_spec()` genera `{'type': 'line_plot', 'series': ..., ...}` (sin `'data'`)

**Conclusión:**

Hay dos implementaciones diferentes para algunos gráficos:
- Implementación legacy en `MatrixLayout.map_*()` que genera specs con `'data'`
- Implementación nueva en `ChartRegistry` que genera specs con estructuras diferentes (`'series'`, `'cells'`, etc.)

Cuando se usa `ChartRegistry` (vía `_register_chart()`), el spec no tiene `'data'` y falla `validate_spec()`. Cuando se usa directamente `MatrixLayout.map_*()`, el spec SÍ tiene `'data'` y pasa la validación.

---

### 1.2. AttributeError: "type object 'MatrixLayout' has no attribute 'map_correlation_heatmap'"

**Gráfico afectado:**
- Correlation Heatmap

**Error completo:**
```
AttributeError: type object 'MatrixLayout' has no attribute 'map_correlation_heatmap'
```

**Ubicación del error:**
- `BESTLIB/layouts/reactive.py:2521` en `add_correlation_heatmap()`

**Análisis:**

El método `add_correlation_heatmap()` intenta llamar a `MatrixLayout.map_correlation_heatmap()`, pero el error indica que este método no existe en la clase `MatrixLayout`.

**Evidencia:**

1. `BESTLIB/layouts/reactive.py:2518-2521`:
   ```python
   from .matrix import MatrixLayout
   ...
   MatrixLayout.map_correlation_heatmap(letter, self._data, **kwargs)
   ```

2. `BESTLIB/matrix.py:1322-1362`: El método `map_correlation_heatmap()` **SÍ existe** como `@classmethod` en `MatrixLayout`.

**Causa raíz:**

El problema es un **conflicto de importación**:

- `BESTLIB/layouts/reactive.py` importa `MatrixLayout` desde `.matrix` (relativo)
- `BESTLIB/matrix.py` define `MatrixLayout` con el método `map_correlation_heatmap()`

**Supuestos:**

1. **Supuesto 1**: Hay dos archivos diferentes con clases llamadas `MatrixLayout`:
   - `BESTLIB/matrix.py` (legacy, con métodos `map_*`)
   - `BESTLIB/layouts/matrix.py` (nuevo, sin algunos métodos `map_*`)

2. **Supuesto 2**: El import `from .matrix import MatrixLayout` en `BESTLIB/layouts/reactive.py` está importando desde `BESTLIB/layouts/matrix.py` en lugar de `BESTLIB/matrix.py`.

3. **Supuesto 3**: `BESTLIB/layouts/matrix.py` no tiene el método `map_correlation_heatmap()`, por lo que cuando se importa desde ahí, el método no está disponible.

**Evidencia adicional:**

- `BESTLIB/layouts/matrix.py` existe y define `MatrixLayout` (línea 57 según búsqueda)
- `BESTLIB/matrix.py` también existe y define `MatrixLayout` con `map_correlation_heatmap()` (línea 1322)

**Conclusión:**

Hay dos implementaciones de `MatrixLayout`:
- Una en `BESTLIB/matrix.py` (legacy, con todos los métodos `map_*`)
- Otra en `BESTLIB/layouts/matrix.py` (nuevo, posiblemente sin algunos métodos)

El import relativo `from .matrix import MatrixLayout` en `BESTLIB/layouts/reactive.py` está importando desde `BESTLIB/layouts/matrix.py` en lugar de `BESTLIB/matrix.py`, causando que el método `map_correlation_heatmap()` no esté disponible.

---

### 1.3. AttributeError: "'ReactiveMatrixLayout' object has no attribute 'add_kde'"

**Gráfico afectado:**
- KDE

**Error completo:**
```
AttributeError: 'ReactiveMatrixLayout' object has no attribute 'add_kde'
```

**Análisis:**

Similar al problema anterior, pero con `add_kde()`. El método existe en `BESTLIB/reactive.py` pero no en `BESTLIB/layouts/reactive.py`.

**Causa raíz:**

Hay dos implementaciones de `ReactiveMatrixLayout`:
- `BESTLIB/reactive.py` (legacy, con métodos como `add_kde`, `add_distplot`, etc.)
- `BESTLIB/layouts/reactive.py` (nuevo, sin algunos métodos)

Cuando se importa `ReactiveMatrixLayout` desde `BESTLIB.reactive` o `BESTLIB.layouts.reactive`, se obtiene una u otra implementación dependiendo del import.

**Evidencia:**

- `BESTLIB/reactive/__init__.py` probablemente importa desde `BESTLIB.layouts.reactive` en lugar de `BESTLIB.reactive`
- `BESTLIB/__init__.py` también podría estar importando desde `BESTLIB.layouts.reactive`

**Conclusión:**

Problema de importación similar al de `Correlation Heatmap`, pero con `ReactiveMatrixLayout` en lugar de `MatrixLayout`.

---

## 2. Gráficos que No Se Visualizan

Los siguientes gráficos ejecutan código sin errores, pero no muestran ningún contenido visual (solo un espacio en blanco):

1. Grouped Bar Chart
2. Pie Chart
3. Line Chart
4. RadViz
5. Star Coordinates
6. Parallel Coordinates
7. Horizontal Bar Chart
8. Hexbin
9. Errorbars
10. Fill Between
11. Step Plot

### 2.1. Análisis General

**Hipótesis principales:**

1. **Falta de renderer JavaScript**: Los gráficos no tienen una función de renderizado en `matrix.js`
2. **Spec inválido**: El spec generado no tiene la estructura esperada por el renderer
3. **Datos vacíos**: El spec tiene `'data'` pero está vacío o en formato incorrecto
4. **Error silencioso en JavaScript**: El renderer existe pero falla silenciosamente

### 2.2. Análisis por Gráfico

#### 2.2.1. Grouped Bar Chart

**Clase Python:** `BESTLIB/charts/grouped_bar.py`

**Spec generado:**
```python
{
    'type': 'grouped_bar',
    'grouped': True,
    'rows': [...],
    'groups': [...],
    'series': [...],
    ...
}
```

**Renderer JavaScript:**
- **NO existe** `renderGroupedBarD3()` en `matrix.js`
- No hay case para `'grouped_bar'` en el switch de `renderChartD3()`

**Causa:**
El gráfico no tiene renderer JavaScript, por lo que no se puede visualizar.

**Supuesto:**
El renderer nunca fue implementado o fue eliminado en alguna refactorización.

---

#### 2.2.2. Pie Chart

**Clase Python:** `BESTLIB/charts/pie.py`

**Spec generado:**
```python
{
    'type': 'pie',
    'data': [...],
    ...
}
```

**Renderer JavaScript:**
- **SÍ existe** `renderPieD3()` en `matrix.js` (línea 2265)
- **SÍ existe** case para `'pie'` en el switch (línea 1526)

**Causa:**
El renderer existe, pero algo está fallando silenciosamente.

**Supuestos:**
1. El spec no tiene `'data'` cuando se valida (pero `PieChart.get_spec()` SÍ genera `'data'`)
2. El spec tiene `'data'` pero está vacío
3. Hay un error JavaScript que se está capturando silenciosamente

**Evidencia:**
- `BESTLIB/charts/pie.py:22`: `get_spec()` retorna `{'type': 'pie', 'data': pie_data, ...}`
- `BESTLIB/matrix.js:2269`: `renderPieD3()` espera `spec.data`

**Conclusión:**
El problema podría estar en cómo se genera o valida el spec antes de llegar al renderer.

---

#### 2.2.3. Line Chart

**Clase Python:** `BESTLIB/charts/line.py`

**Spec generado:**
```python
{
    'type': 'line',
    'series': {...},
    ...
}
```

**Renderer JavaScript:**
- **SÍ existe** `renderLineD3()` en `matrix.js` (línea 1864)
- **SÍ existe** case para `'line'` en el switch (línea 1525)

**Causa:**
Similar a Pie Chart - el renderer existe pero algo falla.

**Supuestos:**
1. El spec no tiene `'data'` (tiene `'series'`), pero `validate_spec()` requiere `'data'` y falla antes de llegar al renderer
2. El spec tiene `'series'` pero está vacío o mal formado

**Evidencia:**
- `BESTLIB/charts/line.py:22`: `get_spec()` retorna `{'type': 'line', **line_data, ...}` donde `line_data` contiene `'series'`
- `BESTLIB/matrix.js:1868`: `renderLineD3()` espera `spec.series`

**Conclusión:**
El problema es que `validate_spec()` requiere `'data'`, pero `LineChart.get_spec()` genera `'series'`. Esto causa que el spec nunca llegue al renderer porque falla la validación.

---

#### 2.2.4. RadViz, Star Coordinates, Parallel Coordinates

**Clases Python:**
- `BESTLIB/charts/radviz.py`
- `BESTLIB/charts/star_coordinates.py`
- `BESTLIB/charts/parallel_coordinates.py`

**Specs generados:**
- RadViz: `{'type': 'radviz', 'data': points, 'features': feats, ...}`
- Star Coordinates: `{'type': 'star_coordinates', 'data': points, 'features': sorted_feats, ...}`
- Parallel Coordinates: `{'type': 'parallel_coordinates', 'data': points, 'dimensions': dims, ...}`

**Renderers JavaScript:**
- **SÍ existen** `renderRadvizD3()`, `renderStarCoordinatesD3()`, `renderParallelCoordinatesD3()` en `matrix.js`
- **SÍ existen** cases en el switch

**Causa:**
Similar a los anteriores - los renderers existen pero algo falla.

**Supuestos:**
1. Los specs se generan correctamente pero hay un error en el renderer JavaScript
2. Los datos están vacíos o mal formados
3. Hay un problema con las dimensiones o el cálculo de features

---

#### 2.2.5. Horizontal Bar Chart, Hexbin, Errorbars, Fill Between, Step Plot

**Clases Python:**
- `BESTLIB/charts/horizontal_bar.py`
- `BESTLIB/charts/hexbin.py`
- `BESTLIB/charts/errorbars.py`
- `BESTLIB/charts/fill_between.py`
- `BESTLIB/charts/step_plot.py`

**Renderers JavaScript:**
- **SÍ existen** todos los renderers en `matrix.js`:
  - `renderHorizontalBarD3()` (línea 6626)
  - `renderHexbinD3()` (línea 6737)
  - `renderErrorbarsD3()` (línea 6887)
  - `renderFillBetweenD3()` (línea 7058)
  - `renderStepPlotD3()` (línea 7191)
- **SÍ existen** cases en el switch

**Causa:**
Similar a los anteriores - los renderers existen pero algo falla.

**Supuestos:**
1. Los specs no tienen `'data'` cuando se validan (similar a Line Chart)
2. Los datos están vacíos o mal formados
3. Hay errores JavaScript silenciosos

---

## 3. Relación entre Line Chart y Line Plot

**Pregunta del usuario:** "Mucho ojo con el Line Chart y el Line Plot, creo que son lo mismo, aunque no estoy seguro, me parece que uno tiene codigo legacy que hay que eliminar."

**Análisis:**

### Line Chart
- **Clase:** `BESTLIB/charts/line.py` - `LineChart`
- **Tipo:** `'line'`
- **Spec:** `{'type': 'line', 'series': {...}, ...}`
- **Renderer:** `renderLineD3()` en `matrix.js`
- **Método en ReactiveMatrixLayout:** `add_line()` (línea 2538 de `reactive.py`)

### Line Plot
- **Clase:** `BESTLIB/charts/line_plot.py` - `LinePlotChart`
- **Tipo:** `'line_plot'`
- **Spec:** `{'type': 'line_plot', 'series': {...}, ...}`
- **Renderer:** `renderLinePlotD3()` en `matrix.js` (línea 6469)
- **Método en ReactiveMatrixLayout:** `add_line_plot()` (línea 3393 de `reactive.py`)

**Diferencias:**

1. **Estructura de spec:**
   - `LineChart` usa `prepare_line_data()` que retorna `{'series': {...}}`
   - `LinePlotChart` también usa `prepare_line_data()` pero agrega más campos al spec (`encoding`, `options`, `interaction`)

2. **Funcionalidad:**
   - `LineChart` es más simple
   - `LinePlotChart` es más completo con más opciones (marcadores, colores, etc.)

3. **Implementación:**
   - `LineChart` es más antiguo (legacy)
   - `LinePlotChart` es más nuevo y completo

**Conclusión:**

Son gráficos **similares pero diferentes**:
- `Line Chart` es la versión legacy/simple
- `Line Plot` es la versión mejorada/completa

**Recomendación:**

No son exactamente lo mismo, pero `Line Plot` es una versión mejorada de `Line Chart`. Si se quiere eliminar código legacy, se podría considerar deprecar `Line Chart` en favor de `Line Plot`, pero primero habría que verificar que todos los casos de uso de `Line Chart` estén cubiertos por `Line Plot`.

---

## 4. Resumen de Problemas por Categoría

### 4.1. Problemas de Validación de Spec

**Gráficos afectados:**
- Heatmap (usa `'cells'` en lugar de `'data'`)
- Line Plot (usa `'series'` en lugar de `'data'`)
- Line Chart (usa `'series'` en lugar de `'data'`)
- Grouped Bar Chart (usa `'rows'`, `'groups'`, `'series'` en lugar de `'data'`)

**Solución propuesta:**
- Hacer `validate_spec()` más flexible para aceptar diferentes estructuras de datos
- O excluir ciertos tipos de gráficos de la validación de `'data'`
- O estandarizar todos los specs para que usen `'data'`

### 4.2. Problemas de Importación

**Gráficos afectados:**
- Correlation Heatmap (importa `MatrixLayout` incorrecto)
- KDE (importa `ReactiveMatrixLayout` incorrecto)

**Solución propuesta:**
- Unificar las importaciones para usar siempre la misma implementación
- O asegurar que todas las implementaciones tengan los mismos métodos

### 4.3. Problemas de Renderizado

**Gráficos afectados:**
- Grouped Bar Chart (no tiene renderer)
- Todos los demás (tienen renderer pero no se visualizan)

**Solución propuesta:**
- Implementar renderer para Grouped Bar Chart
- Investigar por qué los otros renderers no funcionan (posiblemente relacionado con validación de spec)

---

## 5. Recomendaciones

1. **Estandarizar estructura de specs:** Todos los gráficos deberían usar `'data'` o se debería hacer `validate_spec()` más flexible.

2. **Unificar implementaciones:** Resolver los conflictos entre `BESTLIB/matrix.py` y `BESTLIB/layouts/matrix.py`, y entre `BESTLIB/reactive.py` y `BESTLIB/layouts/reactive.py`.

3. **Implementar renderer faltante:** Crear `renderGroupedBarD3()` para Grouped Bar Chart.

4. **Mejorar manejo de errores:** Los errores JavaScript deberían mostrarse en la consola o en el gráfico en lugar de fallar silenciosamente.

5. **Deprecar código legacy:** Considerar deprecar `Line Chart` en favor de `Line Plot` si son funcionalmente equivalentes.

---

## 6. Notas Finales

Esta investigación se realizó **sin modificar ningún código**, solo analizando el código existente. Todos los supuestos y conclusiones están basados en evidencia del código fuente.

Para resolver estos problemas, se recomienda:

1. Primero, estandarizar la estructura de specs o hacer `validate_spec()` más flexible
2. Segundo, unificar las implementaciones duplicadas
3. Tercero, implementar el renderer faltante y depurar los renderers existentes

