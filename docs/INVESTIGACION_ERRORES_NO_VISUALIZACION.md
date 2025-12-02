# Investigación de Errores de No Visualización en BESTLIB

## Resumen Ejecutivo

Este documento presenta una investigación detallada de los errores encontrados en 5 gráficos que no se visualizan correctamente en BESTLIB, a pesar de que el código Python se ejecuta sin errores. Los gráficos afectados son:

1. **Ridgeline Plot (Joy Plot)**
2. **Ribbon Plot**
3. **Histogram 2D**
4. **Polar Plot**
5. **Funnel Plot**

Todos estos gráficos muestran solo la letra del layout (por ejemplo, "P" o "F") en lugar del gráfico visualizado, indicando que el código se ejecuta correctamente pero el renderizado en JavaScript falla silenciosamente.

---

## 1. Análisis del Flujo de Datos: Python → JavaScript

### 1.1. Pipeline Completo

El flujo de datos desde Python hasta JavaScript sigue estos pasos:

1. **Llamada del Usuario**: `layout.add_ridgeline('RL', column='age', category_col='category')`
2. **Método en ReactiveMatrixLayout**: `add_ridgeline()` llama a `MatrixLayout.map_ridgeline()`
3. **Método en MatrixLayout**: `map_ridgeline()` obtiene el chart del `ChartRegistry` y llama a `chart.get_spec()`
4. **Generación del Spec**: El chart genera un spec con `type`, `data`/`series`, `options`, etc.
5. **Almacenamiento**: El spec se guarda en `MatrixLayout._map[letter] = spec`
6. **Preparación para Renderizado**: `_prepare_repr_data()` combina `MatrixLayout._map` con metadata
7. **Serialización JSON**: `_sanitize_for_json()` convierte el spec a JSON
8. **Envío al Frontend**: El JSON se incrusta en el HTML/JavaScript
9. **Renderizado JavaScript**: `render()` en `matrix.js` lee el spec y llama al renderer correspondiente

### 1.2. Puntos Críticos de Falla

Los siguientes puntos son críticos y pueden causar que los gráficos no se visualicen:

- **Validación del Spec**: `validate_spec()` en `spec_utils.py` verifica que el spec tenga los campos requeridos
- **Serialización JSON**: `_sanitize_for_json()` debe convertir correctamente todos los tipos de datos
- **Estructura del Spec**: El spec debe tener la estructura exacta que espera el renderer JavaScript
- **Datos Vacíos o Inválidos**: Los renderers JavaScript verifican si hay datos y muestran errores si están vacíos

---

## 2. Análisis Detallado por Gráfico

### 2.1. Ridgeline Plot (Joy Plot)

**Ubicación del Código:**
- Python: `BESTLIB/charts/ridgeline.py`
- JavaScript: `BESTLIB/matrix.js:7903-8091` (`renderRidgelineD3`)

**Estructura del Spec Generado:**
```python
{
    'type': 'ridgeline',
    'series': {
        'category1': [{'x': float, 'y': float}, ...],
        'category2': [{'x': float, 'y': float}, ...],
        ...
    },
    'options': {
        'overlap': 0.5,
        'opacity': 0.7,
        'xLabel': '...',
        'yLabel': 'Density'
    }
}
```

**Problemas Identificados:**

1. **Validación del Spec:**
   - `validate_spec()` en `spec_utils.py:30` incluye `'ridgeline': ['series', 'data']` en `alternative_fields`
   - ✅ **CORRECTO**: El spec puede tener `'series'` en lugar de `'data'`

2. **Generación del Spec:**
   - `RidgelineChart.get_spec()` en `ridgeline.py:182-241` genera un spec con `'series'` (línea 216)
   - ✅ **CORRECTO**: El spec se genera correctamente

3. **Renderer JavaScript:**
   - `renderRidgelineD3()` en `matrix.js:7903` verifica `spec.series` (línea 7914)
   - Si `spec.series` está vacío o no existe, muestra error: "No hay series para Ridgeline" (línea 7923)
   - ✅ **CORRECTO**: El renderer verifica datos y muestra errores

**Supuestos de Causa:**

1. **Datos Vacíos en Series:**
   - Si `prepare_data()` no genera datos válidos (por ejemplo, todas las categorías tienen 0 puntos), `series` será un diccionario vacío `{}`
   - El renderer JavaScript detecta esto y muestra un error, pero el error puede no ser visible si el contenedor no se renderiza correctamente

2. **Problema de Serialización JSON:**
   - Si `_sanitize_for_json()` no serializa correctamente los valores `float` o `numpy` en los datos, el spec puede llegar al frontend con valores `NaN` o `null`
   - El renderer JavaScript puede fallar silenciosamente si encuentra valores inválidos

3. **Problema de Estructura del Spec:**
   - Si el spec no tiene exactamente la estructura esperada (por ejemplo, `series` es una lista en lugar de un diccionario), el renderer puede fallar

**Recomendaciones:**

1. Verificar que `prepare_data()` genere datos válidos para todas las categorías
2. Agregar logging en JavaScript para ver qué spec se recibe
3. Verificar que `_sanitize_for_json()` serialice correctamente los valores numéricos

---

### 2.2. Ribbon Plot

**Ubicación del Código:**
- Python: `BESTLIB/charts/ribbon.py`
- JavaScript: `BESTLIB/matrix.js:8096-8238` (`renderRibbonD3`)

**Estructura del Spec Generado:**
```python
{
    'type': 'ribbon',
    'data': [
        {'x': float, 'y1': float, 'y2': float},
        ...
    ],
    'options': {
        'color1': '#4a90e2',
        'color2': '#e24a4a',
        'opacity': 0.4,
        'showLines': True,
        'gradient': True
    }
}
```

**Problemas Identificados:**

1. **Validación del Spec:**
   - `validate_spec()` requiere `'data'` para tipos que no están en `alternative_fields`
   - ✅ **CORRECTO**: El spec debe tener `'data'`

2. **Generación del Spec:**
   - `RibbonChart.get_spec()` en `ribbon.py:112-177` genera un spec con `'data'` (línea 145)
   - ✅ **CORRECTO**: El spec se genera correctamente

3. **Problema con Timestamp:**
   - `RibbonChart.prepare_data()` en `ribbon.py:71-110` usa `_safe_to_number()` para convertir valores (líneas 95-97)
   - `_safe_to_number()` debería manejar `Timestamp`, pero si falla, los datos pueden tener valores inválidos

4. **Renderer JavaScript:**
   - `renderRibbonD3()` en `matrix.js:8096` verifica `spec.data` (línea 8097)
   - Si `spec.data` está vacío, retorna sin mostrar error (línea 8100)
   - ⚠️ **PROBLEMA**: El renderer no muestra error visible si los datos están vacíos

**Supuestos de Causa:**

1. **Datos Vacíos:**
   - Si `prepare_data()` genera una lista vacía, el renderer retorna silenciosamente sin mostrar nada
   - El contenedor queda vacío, mostrando solo la letra del layout

2. **Problema con Timestamp:**
   - Si `_safe_to_number()` no maneja correctamente `Timestamp`, los valores de `x` pueden ser `NaN` o `null`
   - El renderer puede fallar al calcular dominios o al dibujar el área

3. **Problema de Serialización:**
   - Si `_sanitize_for_json()` no serializa correctamente los valores, el spec puede llegar al frontend con datos inválidos

**Recomendaciones:**

1. Verificar que `_safe_to_number()` maneje correctamente `Timestamp`
2. Agregar logging en JavaScript para ver qué datos se reciben
3. Mejorar el renderer para mostrar un error visible si los datos están vacíos

---

### 2.3. Histogram 2D

**Ubicación del Código:**
- Python: `BESTLIB/charts/hist2d.py`
- JavaScript: `BESTLIB/matrix.js:8243-8360` (`renderHist2dD3`)

**Estructura del Spec Generado:**
```python
{
    'type': 'hist2d',
    'data': [
        {
            'x': float,
            'y': float,
            'value': float,
            'x_bin_start': float,
            'x_bin_end': float,
            'y_bin_start': float,
            'y_bin_end': float
        },
        ...
    ],
    'options': {
        'bins': 20,
        'colorScale': 'Blues'
    }
}
```

**Problemas Identificados:**

1. **Validación del Spec:**
   - `validate_spec()` requiere `'data'` para `hist2d`
   - ✅ **CORRECTO**: El spec debe tener `'data'`

2. **Generación del Spec:**
   - `Hist2dChart.get_spec()` en `hist2d.py:129-189` genera un spec con `'data'` (línea 162)
   - ✅ **CORRECTO**: El spec se genera correctamente

3. **Renderer JavaScript:**
   - `renderHist2dD3()` en `matrix.js:8243` verifica `spec.data` (línea 8255)
   - Si `spec.data` está vacío, muestra error: "Error: No hay datos para Hist2D" (línea 8263)
   - ✅ **CORRECTO**: El renderer muestra error si los datos están vacíos

**Supuestos de Causa:**

1. **Datos Vacíos:**
   - Si `prepare_data()` genera una lista vacía (por ejemplo, todos los valores son `NaN`), el renderer muestra un error
   - Sin embargo, el error puede no ser visible si el contenedor no se renderiza correctamente

2. **Problema con Bins:**
   - Si `np.histogram2d()` genera bins inválidos (por ejemplo, todos los valores son iguales), los datos pueden tener valores `NaN` o `Inf`
   - El renderer puede fallar al calcular dominios o al dibujar las celdas

3. **Problema de Serialización:**
   - Si `_sanitize_for_json()` no serializa correctamente los valores `numpy`, el spec puede llegar al frontend con datos inválidos

**Recomendaciones:**

1. Verificar que `prepare_data()` genere datos válidos incluso cuando todos los valores son iguales
2. Agregar validación en `prepare_data()` para manejar casos edge (valores constantes, NaN, etc.)
3. Mejorar el renderer para manejar valores `NaN` o `Inf` en los datos

---

### 2.4. Polar Plot

**Ubicación del Código:**
- Python: `BESTLIB/charts/polar.py`
- JavaScript: `BESTLIB/matrix.js:8365-8526` (`renderPolarD3`)

**Estructura del Spec Generado:**
```python
{
    'type': 'polar',
    'data': [
        {
            'x': float,  # Coordenada cartesiana X
            'y': float,  # Coordenada cartesiana Y
            'angle': float,  # Ángulo en radianes
            'radius': float  # Radio
        },
        ...
    ],
    'options': {
        'angle_unit': 'rad',
        'showGrid': True,
        'showLabels': True,
        'color': '#4a90e2'
    }
}
```

**Problemas Identificados:**

1. **Validación del Spec:**
   - `validate_spec()` requiere `'data'` para `polar`
   - ✅ **CORRECTO**: El spec debe tener `'data'`

2. **Generación del Spec:**
   - `PolarChart.get_spec()` en `polar.py:128-184` genera un spec con `'data'` (línea 156)
   - ✅ **CORRECTO**: El spec se genera correctamente

3. **Renderer JavaScript:**
   - `renderPolarD3()` en `matrix.js:8365` verifica `spec.data` (línea 8377)
   - Si `spec.data` está vacío, muestra error: "Error: No hay datos para Polar" (línea 8385)
   - ✅ **CORRECTO**: El renderer muestra error si los datos están vacíos

4. **Problema con Conversión de Coordenadas:**
   - El renderer JavaScript recalcula coordenadas desde `angle` y `radius` (líneas 8462-8470)
   - Si `angle` o `radius` son `NaN` o `null`, el cálculo falla silenciosamente

**Supuestos de Causa:**

1. **Datos Vacíos:**
   - Si `prepare_data()` genera una lista vacía, el renderer muestra un error
   - Sin embargo, el error puede no ser visible si el contenedor no se renderiza correctamente

2. **Problema con Conversión de Coordenadas:**
   - Si `angle` o `radius` son `NaN` o `null`, el renderer puede fallar al calcular coordenadas
   - El renderer no valida que `angle` y `radius` sean válidos antes de usarlos

3. **Problema de Serialización:**
   - Si `_sanitize_for_json()` no serializa correctamente los valores `numpy`, el spec puede llegar al frontend con datos inválidos

**Recomendaciones:**

1. Verificar que `prepare_data()` genere datos válidos con `angle` y `radius` correctos
2. Agregar validación en el renderer JavaScript para verificar que `angle` y `radius` sean válidos
3. Mejorar el renderer para manejar valores `NaN` o `null` en los datos

---

### 2.5. Funnel Plot

**Ubicación del Código:**
- Python: `BESTLIB/charts/funnel.py`
- JavaScript: `BESTLIB/matrix.js:8531-8721` (`renderFunnelD3`)

**Estructura del Spec Generado:**
```python
{
    'type': 'funnel',
    'data': [
        {
            'stage': str,
            'value': float,
            'index': int
        },
        ...
    ],
    'options': {
        'color': '#4a90e2',
        'opacity': 0.7,
        'orientation': 'vertical'
    }
}
```

**Problemas Identificados:**

1. **Validación del Spec:**
   - `validate_spec()` requiere `'data'` para `funnel`
   - ✅ **CORRECTO**: El spec debe tener `'data'`

2. **Generación del Spec:**
   - `FunnelChart.get_spec()` en `funnel.py:122-181` genera un spec con `'data'` (línea 153)
   - ✅ **CORRECTO**: El spec se genera correctamente

3. **Renderer JavaScript:**
   - `renderFunnelD3()` en `matrix.js:8531` verifica `spec.data` (línea 8543)
   - Si `spec.data` está vacío, muestra error: "Error: No hay datos para Funnel" (línea 8551)
   - ✅ **CORRECTO**: El renderer muestra error si los datos están vacíos

**Supuestos de Causa:**

1. **Datos Vacíos:**
   - Si `prepare_data()` genera una lista vacía, el renderer muestra un error
   - Sin embargo, el error puede no ser visible si el contenedor no se renderiza correctamente

2. **Problema con Valores Negativos o Ceros:**
   - Si todos los valores son 0 o negativos, el renderer puede fallar al calcular escalas
   - El renderer no valida que los valores sean positivos antes de usarlos

3. **Problema de Serialización:**
   - Si `_sanitize_for_json()` no serializa correctamente los valores, el spec puede llegar al frontend con datos inválidos

**Recomendaciones:**

1. Verificar que `prepare_data()` genere datos válidos con valores positivos
2. Agregar validación en el renderer JavaScript para verificar que los valores sean válidos
3. Mejorar el renderer para manejar valores 0 o negativos

---

## 3. Problemas Comunes Identificados

### 3.1. Problema de Serialización JSON

**Descripción:**
`_sanitize_for_json()` en `matrix.py:2792-2815` convierte tipos no serializables a JSON, pero puede no manejar correctamente todos los casos:

- Valores `numpy.float64` o `numpy.int64` pueden no convertirse correctamente
- Valores `NaN` o `Inf` pueden causar problemas en JSON
- Objetos complejos pueden convertirse a strings en lugar de estructuras válidas

**Impacto:**
Si el spec contiene valores no serializables, el JSON puede ser inválido o los valores pueden llegar al frontend como `null` o `NaN`, causando que el renderer falle silenciosamente.

**Recomendaciones:**
1. Agregar logging para verificar qué valores se están serializando
2. Mejorar `_sanitize_for_json()` para manejar `NaN` y `Inf` explícitamente
3. Validar el JSON generado antes de enviarlo al frontend

---

### 3.2. Problema de Validación de Datos en JavaScript

**Descripción:**
Los renderers JavaScript verifican si los datos están vacíos, pero pueden no validar que los valores sean válidos (no `NaN`, no `null`, etc.):

- `renderRidgelineD3()` verifica `spec.series` pero no valida que los valores dentro de las series sean válidos
- `renderRibbonD3()` verifica `spec.data` pero no valida que `x`, `y1`, `y2` sean válidos
- `renderHist2dD3()` verifica `spec.data` pero no valida que los valores de bins sean válidos
- `renderPolarD3()` verifica `spec.data` pero no valida que `angle` y `radius` sean válidos
- `renderFunnelD3()` verifica `spec.data` pero no valida que los valores sean positivos

**Impacto:**
Si los datos contienen valores inválidos (`NaN`, `null`, `Inf`), el renderer puede fallar silenciosamente al calcular dominios o al dibujar elementos.

**Recomendaciones:**
1. Agregar validación de valores en cada renderer antes de usarlos
2. Filtrar valores inválidos antes de calcular dominios
3. Mostrar errores visibles si se detectan valores inválidos

---

### 3.3. Problema de Estructura del Spec

**Descripción:**
Los specs generados por Python pueden no tener exactamente la estructura esperada por los renderers JavaScript:

- `RidgelineChart.get_spec()` genera `'series'` como un diccionario, pero el renderer puede esperar una estructura diferente
- `RibbonChart.get_spec()` genera `'data'` con `x`, `y1`, `y2`, pero el renderer puede esperar campos adicionales
- `Hist2dChart.get_spec()` genera `'data'` con campos de bins, pero el renderer puede esperar una estructura diferente
- `PolarChart.get_spec()` genera `'data'` con `x`, `y`, `angle`, `radius`, pero el renderer puede esperar solo `angle` y `radius`
- `FunnelChart.get_spec()` genera `'data'` con `stage`, `value`, `index`, pero el renderer puede esperar una estructura diferente

**Impacto:**
Si la estructura del spec no coincide exactamente con lo que espera el renderer, el renderer puede fallar silenciosamente o mostrar datos incorrectos.

**Recomendaciones:**
1. Documentar la estructura exacta esperada por cada renderer
2. Validar la estructura del spec antes de enviarlo al frontend
3. Agregar logging en JavaScript para ver qué estructura se recibe

---

### 3.4. Problema de Renderizado del Contenedor

**Descripción:**
Si el contenedor no se renderiza correctamente (por ejemplo, si el layout ASCII no incluye la letra del gráfico), el gráfico no se mostrará:

- El método `render()` en `matrix.js` busca celdas en el layout ASCII
- Si la letra no está en el layout, no se crea el contenedor
- Si el contenedor no existe, el renderer no puede dibujar el gráfico

**Impacto:**
Si el layout ASCII no incluye la letra del gráfico, el gráfico no se mostrará, pero no habrá error visible.

**Recomendaciones:**
1. Validar que el layout ASCII incluya todas las letras de los gráficos
2. Mostrar un error visible si una letra no está en el layout
3. Agregar logging para verificar qué letras se están renderizando

---

## 4. Soluciones Propuestas

### 4.1. Solución Inmediata: Agregar Logging

**Descripción:**
Agregar logging detallado en Python y JavaScript para diagnosticar problemas:

1. **En Python:**
   - Logging en `prepare_data()` para ver qué datos se generan
   - Logging en `get_spec()` para ver qué spec se genera
   - Logging en `_sanitize_for_json()` para ver qué valores se serializan

2. **En JavaScript:**
   - Logging en `render()` para ver qué specs se reciben
   - Logging en cada renderer para ver qué datos se procesan
   - Logging de errores si se detectan valores inválidos

**Implementación:**
- Agregar `console.log()` en puntos clave del código JavaScript
- Agregar `print()` o logging en puntos clave del código Python
- Usar un flag de debug para activar/desactivar logging

---

### 4.2. Solución a Mediano Plazo: Mejorar Validación

**Descripción:**
Mejorar la validación de datos en Python y JavaScript:

1. **En Python:**
   - Validar que `prepare_data()` genere datos válidos (no vacíos, sin NaN, etc.)
   - Validar que `get_spec()` genere specs con la estructura correcta
   - Validar que `_sanitize_for_json()` serialice correctamente todos los valores

2. **En JavaScript:**
   - Validar que los specs tengan la estructura correcta antes de renderizar
   - Validar que los datos contengan valores válidos antes de usarlos
   - Mostrar errores visibles si se detectan problemas

**Implementación:**
- Agregar funciones de validación en `spec_utils.py`
- Agregar funciones de validación en `matrix.js`
- Mostrar mensajes de error visibles en el DOM

---

### 4.3. Solución a Largo Plazo: Refactorizar Pipeline

**Descripción:**
Refactorizar el pipeline de datos para hacerlo más robusto:

1. **Estandarizar Estructura de Specs:**
   - Definir una estructura estándar para todos los specs
   - Validar que todos los specs sigan esta estructura
   - Documentar la estructura esperada

2. **Mejorar Serialización:**
   - Mejorar `_sanitize_for_json()` para manejar todos los casos
   - Validar el JSON generado antes de enviarlo
   - Agregar fallbacks para valores problemáticos

3. **Mejorar Renderizado:**
   - Hacer los renderers más robustos ante datos inválidos
   - Agregar validación exhaustiva en cada renderer
   - Mostrar errores visibles y útiles

**Implementación:**
- Crear una clase base para specs con validación automática
- Refactorizar `_sanitize_for_json()` para ser más robusta
- Refactorizar renderers para ser más defensivos

---

## 5. Plan de Acción Recomendado

### Fase 1: Diagnóstico (Inmediato)
1. Agregar logging detallado en Python y JavaScript
2. Ejecutar los gráficos problemáticos y revisar los logs
3. Identificar el punto exacto donde falla el pipeline

### Fase 2: Correcciones Rápidas (Corto Plazo)
1. Corregir problemas de serialización JSON
2. Agregar validación de datos en los renderers
3. Mejorar manejo de errores para mostrar mensajes visibles

### Fase 3: Mejoras Estructurales (Mediano Plazo)
1. Estandarizar estructura de specs
2. Mejorar validación en Python
3. Refactorizar renderers para ser más robustos

### Fase 4: Optimización (Largo Plazo)
1. Optimizar serialización JSON
2. Agregar tests automatizados para cada gráfico
3. Documentar estructura de specs y pipeline completo

---

## 6. Conclusión

Los 5 gráficos analizados (Ridgeline Plot, Ribbon Plot, Histogram 2D, Polar Plot, Funnel Plot) no se visualizan debido a problemas en el pipeline de datos desde Python hasta JavaScript. Los problemas principales son:

1. **Serialización JSON**: Valores no serializables pueden llegar al frontend como `null` o `NaN`
2. **Validación de Datos**: Los renderers no validan exhaustivamente que los valores sean válidos
3. **Estructura del Spec**: Los specs pueden no tener exactamente la estructura esperada por los renderers
4. **Manejo de Errores**: Los errores no se muestran de forma visible, causando fallos silenciosos

Las soluciones propuestas incluyen agregar logging, mejorar validación, y refactorizar el pipeline para hacerlo más robusto. Se recomienda seguir el plan de acción en fases para diagnosticar y corregir los problemas de manera sistemática.

