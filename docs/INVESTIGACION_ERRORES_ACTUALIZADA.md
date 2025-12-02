# Investigación de Errores Actualizada en BESTLIB

## Resumen Ejecutivo

Este documento presenta una investigación detallada de los nuevos errores encontrados después de realizar cambios adicionales en la librería BESTLIB. Los errores se clasifican en tres categorías principales:

1. **Errores de visualización** (gráficos que no se muestran correctamente)
2. **Errores de validación de spec** (ChartError por campos faltantes)
3. **Errores de conversión de tipos** (TypeError con Timestamp)

---

## 1. Errores de Visualización

### 1.1. Grouped Bar Chart: Muestra `[object Object]`

**Gráfico afectado:**
- Grouped Bar Chart

**Síntoma:**
- El código se ejecuta sin errores de Python
- El gráfico muestra `[object Object]` en lugar del gráfico visualizado
- El renderer JavaScript existe (`renderGroupedBarD3`)

**Ubicación del código:**
- `BESTLIB/charts/grouped_bar.py`: Clase `GroupedBarChart`
- `BESTLIB/matrix.js:8683`: Función `renderGroupedBarD3`
- `BESTLIB/layouts/reactive.py:1061`: Método `add_grouped_barchart`

**Análisis:**

1. **Estructura del spec generado:**
   - `GroupedBarChart.get_spec()` (línea 20-41) genera un spec con:
     - `'type': 'grouped_bar'`
     - `'data': flat_data` (datos planos para compatibilidad)
     - `'rows': rows`
     - `'groups': groups`
     - `'series': series`
     - `'grouped': True`

2. **Estructura esperada por el renderer:**
   - `renderGroupedBarD3` (línea 8683-8856) espera:
     - `spec.rows` (array de strings)
     - `spec.groups` (array de strings)
     - `spec.series` (array de arrays de números)

3. **Problema identificado:**
   - El spec se está generando correctamente con todos los campos necesarios
   - El renderer JavaScript existe y está implementado
   - El problema probablemente está en la serialización del spec al frontend o en cómo se está pasando el objeto al renderer

**Supuestos sobre la causa:**

1. **Serialización incorrecta del spec:**
   - El spec puede estar siendo serializado incorrectamente cuando se pasa al frontend
   - El objeto JavaScript puede no estar siendo parseado correctamente
   - Posible problema con campos anidados o con el campo `'grouped': True`

2. **Problema con el campo `'data'` adicional:**
   - El spec incluye `'data': flat_data` además de `'rows'`, `'groups'`, `'series'`
   - Esto podría estar causando confusión en el renderer o en la serialización
   - El renderer no usa el campo `'data'`, solo `'rows'`, `'groups'`, `'series'`

3. **Problema con la validación del spec:**
   - `validate_spec()` permite `'grouped_bar'` con campos alternativos (`'rows'`, `'series'`, `'data'`)
   - El spec pasa la validación, pero puede haber un problema en cómo se registra o se pasa al frontend

**Recomendaciones:**

1. Verificar cómo se serializa el spec al frontend (JSON.stringify)
2. Revisar si el campo `'grouped': True` está causando problemas
3. Verificar que el spec se esté pasando correctamente al renderer JavaScript
4. Considerar remover el campo `'data'` del spec si no es necesario para el renderer

---

### 1.2. Histogram 2D, Polar Plot, Funnel Plot: No se visualizan

**Gráficos afectados:**
- Histogram 2D
- Polar Plot
- Funnel Plot

**Síntoma:**
- El código se ejecuta sin errores de Python
- Los gráficos muestran solo una letra "P" o espacio en blanco
- Los renderers JavaScript existen (`renderHist2dD3`, `renderPolarD3`, `renderFunnelD3`)

**Ubicación del código:**
- `BESTLIB/charts/hist2d.py`: Clase `Hist2dChart`
- `BESTLIB/charts/polar.py`: Clase `PolarChart`
- `BESTLIB/charts/funnel.py`: Clase `FunnelChart`
- `BESTLIB/matrix.js:8233`, `8344`, `8499`: Funciones renderer

**Análisis:**

1. **Estructura del spec generado:**
   - Todos los charts generan specs con `'data'` (array de objetos)
   - `Hist2dChart.get_spec()` (línea 160-162): `'data': hist2d_data['data']`
   - `PolarChart.get_spec()` (línea 154-156): `'data': polar_data['data']`
   - `FunnelChart.get_spec()` (línea 151-153): `'data': funnel_data['data']`

2. **Estructura esperada por los renderers:**
   - `renderHist2dD3` (línea 8233-8339) espera `spec.data` (array)
   - `renderPolarD3` (línea 8344-8494) espera `spec.data` (array)
   - `renderFunnelD3` (línea 8499-8678) espera `spec.data` (array)

3. **Validación en los renderers:**
   - Todos los renderers verifican si `spec.data` está vacío o no existe
   - Si está vacío, muestran un mensaje de error en la consola y un div con error
   - Si no hay datos, el renderer retorna temprano

**Problema identificado:**

1. **Los renderers verifican datos:**
   - `renderHist2dD3` (línea 8234-8243): Verifica `spec.data || []` y muestra error si está vacío
   - `renderPolarD3` (línea 8345-8354): Verifica `spec.data || []` y muestra error si está vacío
   - `renderFunnelD3` (línea 8500-8509): Verifica `spec.data || []` y muestra error si está vacío

2. **El problema probablemente es:**
   - Los datos están llegando vacíos al frontend
   - El spec se está generando correctamente en Python, pero se pierde en la serialización
   - El spec puede estar siendo validado incorrectamente antes de llegar al renderer

**Supuestos sobre la causa:**

1. **Datos vacíos en el spec:**
   - Los datos pueden estar llegando como array vacío `[]` al frontend
   - El problema puede estar en `prepare_data()` que retorna `{'data': []}` en algunos casos
   - Puede haber un problema con la conversión de tipos o con la preparación de datos

2. **Problema con la serialización:**
   - El spec puede estar siendo serializado incorrectamente
   - Los datos pueden estar siendo filtrados o perdidos durante la serialización
   - Puede haber un problema con campos anidados o con tipos de datos no serializables

3. **Problema con la validación del spec:**
   - `validate_spec()` requiere `'data'` para estos tipos de gráficos
   - El spec pasa la validación, pero los datos pueden estar vacíos
   - El renderer verifica si los datos están vacíos, pero puede haber un problema antes de llegar al renderer

**Recomendaciones:**

1. Verificar que `prepare_data()` esté generando datos no vacíos
2. Revisar la serialización del spec al frontend
3. Agregar logging en el frontend para ver qué datos están llegando
4. Verificar que el spec se esté pasando correctamente al renderer JavaScript

---

## 2. Errores de Validación de Spec

### 2.1. Ridgeline Plot: ChartError "El spec debe incluir 'data'"

**Gráfico afectado:**
- Ridgeline Plot (Joy Plot)

**Error completo:**
```
ChartError: El spec debe incluir 'data'
```

**Ubicación del error:**
- `BESTLIB/charts/spec_utils.py:34-35` en la función `validate_spec()`
- `BESTLIB/charts/ridgeline.py:182-241` en el método `get_spec()`

**Análisis:**

1. **Estructura del spec generado:**
   - `RidgelineChart.get_spec()` (línea 182-241) genera un spec con:
     - `'type': 'ridgeline'`
     - `'series': result` (dict con series de KDE por categoría)
     - NO incluye `'data'`

2. **Validación del spec:**
   - `validate_spec()` (línea 21-35) tiene una lista de tipos con campos alternativos:
     ```python
     alternative_fields = {
         'heatmap': ['cells', 'data'],
         'line': ['series', 'data'],
         'line_plot': ['series', 'data'],
         'grouped_bar': ['rows', 'series', 'data'],
         'step_plot': ['series', 'data'],
     }
     ```
   - `'ridgeline'` NO está en esta lista
   - Por lo tanto, `validate_spec()` requiere que el spec tenga `'data'`

3. **Estructura esperada por el renderer:**
   - `renderRidgelineD3` (línea 7903-8015) espera `spec.series` (dict)
   - El renderer NO usa `'data'`, solo `'series'`

**Problema identificado:**

- `RidgelineChart.get_spec()` genera un spec con `'series'` pero NO `'data'`
- `validate_spec()` NO reconoce `'ridgeline'` como un tipo con campos alternativos
- Por lo tanto, `validate_spec()` falla porque el spec no tiene `'data'`

**Supuestos sobre la causa:**

1. **Falta de registro en `validate_spec()`:**
   - `'ridgeline'` debería estar en la lista de tipos con campos alternativos
   - Debería permitir `'series'` o `'data'` como campos válidos
   - Similar a `'line'` y `'line_plot'` que usan `'series'`

2. **Inconsistencia en el diseño:**
   - Algunos gráficos usan `'series'` (line, line_plot, step_plot, ridgeline)
   - Otros usan `'data'` (scatter, bar, histogram)
   - `validate_spec()` debería reconocer todos los tipos que usan `'series'`

**Recomendaciones:**

1. Agregar `'ridgeline'` a la lista de tipos con campos alternativos en `validate_spec()`
2. Permitir `'series'` o `'data'` como campos válidos para `'ridgeline'`
3. Verificar que otros gráficos que usan `'series'` también estén registrados

---

## 3. Errores de Conversión de Tipos

### 3.1. Ribbon Plot: TypeError con Timestamp

**Gráfico afectado:**
- Ribbon Plot

**Error completo:**
```
TypeError: float() argument must be a string or a real number, not 'Timestamp'
```

**Ubicación del error:**
- `BESTLIB/charts/ribbon.py:91` en el método `prepare_data()`

**Análisis:**

1. **Código problemático:**
   ```python
   for _, row in data_sorted.iterrows():
       ribbon_data.append({
           'x': float(row[x_col]),  # Línea 91
           'y1': float(row[y1_col]),  # Línea 92
           'y2': float(row[y2_col])  # Línea 93
       })
   ```

2. **Problema:**
   - `float()` no puede convertir objetos `Timestamp` directamente
   - Si `x_col` contiene fechas (`pd.Timestamp`), la conversión falla
   - Similar al error encontrado en `Line Chart` y `Line Plot`

3. **Comparación con otros gráficos:**
   - `prepare_line_data()` en `BESTLIB/data/preparators.py:401` tiene el mismo problema
   - Otros gráficos que usan fechas pueden tener el mismo problema

**Supuestos sobre la causa:**

1. **Falta de manejo de tipos temporales:**
   - `prepare_data()` asume que todos los valores son numéricos o convertibles a `float`
   - No maneja tipos temporales como `pd.Timestamp` o `datetime`
   - Debería convertir fechas a timestamps numéricos antes de usar `float()`

2. **Inconsistencia en el manejo de fechas:**
   - Algunos gráficos pueden manejar fechas correctamente
   - Otros gráficos fallan con el mismo error
   - Debería haber una función utilitaria para convertir fechas a números

**Recomendaciones:**

1. Agregar manejo de tipos temporales en `prepare_data()` de `RibbonChart`
2. Convertir `pd.Timestamp` a timestamp numérico usando `.timestamp()` o `.value`
3. Crear una función utilitaria para convertir fechas a números que pueda ser reutilizada
4. Verificar otros gráficos que puedan tener el mismo problema

---

## 4. Resumen de Errores

| Gráfico | Tipo de Error | Causa Probable | Prioridad |
|---------|---------------|----------------|-----------|
| Grouped Bar Chart | Visualización (`[object Object]`) | Problema de serialización del spec | Alta |
| Histogram 2D | Visualización (no se muestra) | Datos vacíos o problema de serialización | Alta |
| Polar Plot | Visualización (no se muestra) | Datos vacíos o problema de serialización | Alta |
| Funnel Plot | Visualización (no se muestra) | Datos vacíos o problema de serialización | Alta |
| Ridgeline Plot | ChartError (spec sin 'data') | Falta registro en `validate_spec()` | Media |
| Ribbon Plot | TypeError (Timestamp) | Falta manejo de tipos temporales | Media |

---

## 5. Recomendaciones Generales

### 5.1. Validación de Specs

1. **Actualizar `validate_spec()`:**
   - Agregar `'ridgeline'` a la lista de tipos con campos alternativos
   - Verificar que todos los gráficos que usan `'series'` estén registrados
   - Documentar qué campos alternativos usa cada tipo de gráfico

### 5.2. Manejo de Tipos Temporales

1. **Crear función utilitaria:**
   - Función para convertir fechas a timestamps numéricos
   - Reutilizable en todos los gráficos que necesiten manejar fechas
   - Ubicación: `BESTLIB/data/transformers.py` o similar

2. **Actualizar gráficos afectados:**
   - `RibbonChart.prepare_data()`
   - `LineChart` (si aún tiene el problema)
   - Cualquier otro gráfico que use fechas

### 5.3. Serialización de Specs

1. **Verificar serialización al frontend:**
   - Asegurar que todos los campos del spec se serialicen correctamente
   - Verificar que no se pierdan datos durante la serialización
   - Agregar logging para debuggear problemas de serialización

2. **Revisar estructura de specs:**
   - Verificar que los specs tengan la estructura correcta
   - Remover campos innecesarios que puedan causar problemas
   - Documentar qué campos son requeridos por cada renderer

### 5.4. Testing

1. **Agregar tests para:**
   - Validación de specs con diferentes estructuras
   - Manejo de tipos temporales
   - Serialización de specs al frontend
   - Renderizado de gráficos con datos vacíos

---

## 6. Conclusión

Los errores encontrados se pueden clasificar en tres categorías principales:

1. **Problemas de visualización:** Grouped Bar Chart, Histogram 2D, Polar Plot, Funnel Plot
2. **Problemas de validación:** Ridgeline Plot
3. **Problemas de conversión de tipos:** Ribbon Plot

La mayoría de los problemas parecen estar relacionados con:
- Serialización incorrecta del spec al frontend
- Falta de registro de tipos alternativos en `validate_spec()`
- Falta de manejo de tipos temporales en la preparación de datos

Se recomienda abordar estos problemas de manera sistemática, comenzando por los errores de validación y conversión de tipos, y luego investigando más a fondo los problemas de visualización.

