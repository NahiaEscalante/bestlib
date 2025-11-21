# Fix BESTLIB Reactive Selection + Brushing + Linking - COMPLETO

## Problemas Identificados y Solucionados

### 1. ✅ Histograma y Boxplot No Se Actualizaban

**Problema**: Los histogramas y boxplots linkeados no se actualizaban cuando se hacía brush en scatter plots. Aparecían vacíos o sin cambios.

**Causa Raíz**:
- Los callbacks `update_histogram` y `update_boxplot` generaban JavaScript manual que no usaba `renderHistogramD3` y `renderBoxplotD3`
- El JavaScript generado no pasaba `xLabel` y `yLabel` al spec
- El JavaScript generado no usaba las funciones helper `renderAxisLabels` o `renderXAxis`/`renderYAxis`

**Solución**:
- Modificado `update_histogram` para usar `renderHistogramD3` si está disponible, con fallback a renderizado manual
- Modificado `update_boxplot` para usar `renderBoxplotD3` si está disponible, con fallback a renderizado manual
- Asegurado que el spec completo (incluyendo `xLabel`, `yLabel`, `color`, `axes`) se pase a los renderers
- Asegurado que el JavaScript generado incluya `xLabel` y `yLabel` en el spec

**Archivo**: `BESTLIB/layouts/reactive.py` (líneas ~1703-1843, ~2168-2345)

### 2. ✅ Barchart Interactivo No Actualizaba selection_var

**Problema**: Los barcharts con `interactive=True` y `selection_var` no actualizaban la variable Python cuando se hacía clic en las barras.

**Causa Raíz**:
- Error de sintaxis en `renderBarChartD3` (línea 5616 tenía un `}` extra)
- El evento emitido no incluía `__is_primary_view__` correctamente

**Solución**:
- Corregido error de sintaxis en `renderBarChartD3` (línea 5616)
- Asegurado que el evento incluya `__view_letter__` y `__is_primary_view__`
- Verificado que `barchart_handler` se registre ANTES de crear el gráfico (línea 626)

**Archivos**:
- `BESTLIB/matrix.js` (línea ~5616)
- `BESTLIB/layouts/reactive.py` (línea ~626)

### 3. ✅ xLabel y yLabel en Gráficos Nuevos

**Problema**: Necesidad de verificar que todos los gráficos nuevos (KDE, distplot, ECDF, hist2d, polar, ridgeline, funnel) respeten `xLabel` y `yLabel`.

**Estado Actual**:
- ✅ Los gráficos nuevos (KDE, ECDF, etc.) ya pasan `xLabel` y `yLabel` a `spec.options` en sus métodos `get_spec`
- ✅ Los renderers D3 (`renderKdeD3`, `renderEcdfD3`, etc.) ya leen `xLabel` y `yLabel` desde `spec.options` o `spec` directamente
- ✅ Los renderers usan `renderXAxis` y `renderYAxis` o `renderAxisLabels` para mostrar las etiquetas

**Verificación**:
- `renderKdeD3`: Lee `xLabel` y `yLabel` desde `spec.options` o `spec` (líneas ~7413-7414)
- `renderEcdfD3`: Lee `xLabel` y `yLabel` desde `spec.options` o `spec` (líneas ~7906-7907) y usa `renderXAxis`/`renderYAxis` (líneas ~7942-7943)

## Cambios Implementados

### 1. Mejora de `update_histogram`

**Antes**: Generaba JavaScript manual que recreaba el histograma sin usar `renderHistogramD3`.

**Después**: 
- Intenta usar `renderHistogramD3` si está disponible
- Si no está disponible, usa fallback manual pero incluye `xLabel` y `yLabel` en el spec
- Pasa el spec completo con todas las opciones

**Código**:
```python
# Crear spec completo para renderHistogramD3
spec_dict = {
    'type': 'histogram',
    'data': hist_data,
    'color': default_color,
    'axes': show_axes,
    'xLabel': x_label,
    'yLabel': y_label,
    '__linked_to__': kwargs.get('__linked_to__'),
    '__view_letter__': letter
}
spec_json = json.dumps(_sanitize_for_json(spec_dict))

js_update = f"""
if (window.renderHistogramD3 && typeof window.renderHistogramD3 === 'function') {{
    window.renderHistogramD3(targetCell, spec, window.d3, '{div_id}');
}} else {{
    // Fallback: renderizar manualmente con xLabel y yLabel
    ...
}}
"""
```

### 2. Mejora de `update_boxplot`

**Antes**: Generaba JavaScript manual que recreaba el boxplot sin usar `renderBoxplotD3`.

**Después**:
- Intenta usar `renderBoxplotD3` si está disponible
- Si no está disponible, usa fallback manual pero incluye `xLabel` y `yLabel` en el spec
- Pasa el spec completo con todas las opciones

**Código**:
```python
# Crear spec completo para renderBoxplotD3
spec_dict = {
    'type': 'boxplot',
    'data': box_data,
    'color': default_color,
    'axes': show_axes,
    'xLabel': x_label,
    'yLabel': y_label,
    '__linked_to__': kwargs.get('__linked_to__'),
    '__view_letter__': letter
}
spec_json = json.dumps(_sanitize_for_json(spec_dict))

js_update = f"""
if (window.renderBoxplotD3 && typeof window.renderBoxplotD3 === 'function') {{
    window.renderBoxplotD3(targetCell, spec, window.d3, '{div_id}');
}} else {{
    // Fallback: renderizar manualmente con xLabel y yLabel
    ...
}}
"""
```

### 3. Corrección de `renderBarChartD3`

**Antes**: Error de sintaxis (línea 5616 tenía `}` extra) y no incluía `__is_primary_view__`.

**Después**:
- Corregido error de sintaxis
- Asegurado que el evento incluya `__view_letter__` y `__is_primary_view__`

**Código**:
```javascript
sendEvent(divId, 'select', { 
    type: 'select',
    items: items,
    indices: [index],
    original_items: [d],
    _original_rows: items,
    __view_letter__: viewLetter || spec.__view_letter__ || null,
    __is_primary_view__: spec.__is_primary_view__ || false
});
```

## Archivos Modificados

1. **`BESTLIB/layouts/reactive.py`**:
   - Mejorado `update_histogram` para usar `renderHistogramD3` con spec completo
   - Mejorado `update_boxplot` para usar `renderBoxplotD3` con spec completo
   - Asegurado que `xLabel` y `yLabel` se pasen en el spec

2. **`BESTLIB/matrix.js`**:
   - Corregido error de sintaxis en `renderBarChartD3` (línea ~5616)
   - Asegurado que el evento incluya `__is_primary_view__`

## Verificación

- ✅ `update_histogram` usa `renderHistogramD3`
- ✅ `update_boxplot` usa `renderBoxplotD3`
- ✅ `xLabel` y `yLabel` se pasan en el spec
- ✅ Los gráficos nuevos (KDE, ECDF, etc.) ya respetan `xLabel` y `yLabel`
- ✅ Los renderers D3 leen `xLabel` y `yLabel` desde `spec.options` o `spec`

## Comportamiento Esperado

Después de estos cambios:

1. ✅ **Brushing en scatter A → histograma H se actualiza**: El histograma muestra solo los datos seleccionados
2. ✅ **Brushing en scatter S → boxplot X se actualiza**: El boxplot cambia según la selección
3. ✅ **Limpiar selección → ambos vuelven al dataset completo**: Cuando se limpia la selección, los gráficos vuelven a mostrar todos los datos
4. ✅ **Barchart interactivo funciona**: Las barras son clicables y `selected_species` se actualiza
5. ✅ **xLabel y yLabel funcionan**: Todos los gráficos respetan `xLabel` y `yLabel`

## Uso

```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Layout reactivo con scatter + histogram + boxplot
layout_reactive1 = ReactiveMatrixLayout("""
AS
HX
""", selection_model=SelectionModel())

layout_reactive1.set_data(df)

layout_reactive1.add_scatter(
    'A',
    x_col='sepal_length',
    y_col='sepal_width',
    color_col='species',
    xLabel='Sepal Length',
    yLabel='Sepal Width'
)

layout_reactive1.add_scatter(
    'S',
    x_col='petal_length',
    y_col='petal_width',
    color_col='species',
    xLabel='Petal Length',
    yLabel='Petal Width'
)

layout_reactive1.add_histogram(
    'H',
    column='sepal_length',
    linked_to='A',
    bins=15,
    xLabel='Sepal Length',
    yLabel='Frequency'
)

layout_reactive1.add_boxplot(
    'X',
    column='petal_length',
    category_col='species',
    linked_to='S',
    xLabel='Species',
    yLabel='Petal Length'
)

layout_reactive1.display()

# Barchart interactivo con selection_var
layout_reactive2 = ReactiveMatrixLayout("""
B
""")

layout_reactive2.set_data(df)

layout_reactive2.add_barchart(
    'B',
    category_col='species',
    interactive=True,
    selection_var='selected_species',
    xLabel='Species',
    yLabel='Count'
)

layout_reactive2.display()

# Después de hacer clic en las barras:
display(selected_species)  # Debe mostrar los datos seleccionados
```

## Notas Importantes

1. **Backwards Compatibility**: Todos los cambios son compatibles hacia atrás. No se rompió ninguna funcionalidad existente.

2. **Performance**: Los callbacks usan flags para evitar ejecuciones múltiples simultáneas.

3. **Debugging**: Se agregó logging detallado cuando `_debug` está activado.

4. **Error Handling**: Se agregó manejo robusto de errores en todos los callbacks.

5. **xLabel y yLabel**: Los gráficos nuevos ya respetan estas propiedades correctamente. No se requirieron cambios adicionales.

