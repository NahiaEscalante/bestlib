# Fix BESTLIB Scatterplot Interaction — JS Event Layer

## Problema Identificado

Los scatterplots en BESTLIB ya tenían el código de brush implementado, pero:
1. Los eventos se enviaban solo como "select", no como "brush"
2. El overlay del brush podía no estar capturando eventos correctamente
3. Faltaba envío explícito de eventos "brush" cuando se completaba el brush

## Correcciones Aplicadas

### 1. ✅ Envío Explícito de Eventos "brush"

**Archivo**: `BESTLIB/matrix.js`

**Cambios**:
- En `sendSelectionEvent()`: Agregado envío de evento "brush" cuando hay más de un punto seleccionado
- En el handler `brush.on('end')`: Agregado envío explícito de evento "brush" después de `sendSelectionEvent()`

**Código agregado**:
```javascript
// En sendSelectionEvent() - línea ~5926
if (indices.size > 1) {
  sendEvent(divId, 'brush', {
    ...eventPayload,
    type: 'brush'
  });
}

// En brush.on('end') - línea ~6154
if (selectedIndices.size > 0) {
  sendEvent(divId, 'brush', {
    type: 'brush',
    items: selectedItems,
    count: selectedIndices.size,
    indices: Array.from(selectedIndices),
    __scatter_letter__: scatterLetter,
    __view_letter__: scatterLetter,
    __is_primary_view__: spec.__is_primary_view__ || false
  });
}
```

### 2. ✅ Mejora del Overlay del Brush

**Archivo**: `BESTLIB/matrix.js`

**Cambios**:
- Agregado `style('pointer-events', 'all')` al brushGroup
- Agregado `filter()` al brush para permitir eventos de mouse, touch y pointer
- Mejorado el setTimeout que aplica estilos al overlay para asegurar que capture eventos
- Agregado listener `pointerdown` al overlay para asegurar que capture eventos

**Código agregado**:
```javascript
// En renderScatterPlotD3() - línea ~6002
const brushGroup = g.append('g')
  .attr('class', 'brush-layer')
  .style('pointer-events', 'all');  // CRÍTICO: Asegurar que capture eventos

const brush = d3.brush()
  .extent([[0, 0], [chartWidth, chartHeight]])
  .filter(function(event) {
    // Permitir brush con mouse y touch
    return event.type === 'mousedown' || event.type === 'touchstart' || event.type === 'pointerdown';
  })

// En setTimeout - línea ~6229
const overlay = brushGroup.selectAll('.overlay');
if (overlay.size() > 0) {
  overlay
    .style('cursor', 'crosshair')
    .style('pointer-events', 'all')
    .style('fill', 'transparent')
    .style('z-index', '1000');  // Asegurar que esté encima
  
  // CRÍTICO: Asegurar que el overlay capture eventos de pointer
  overlay.on('pointerdown', function(event) {
    event.stopPropagation();
  });
}
```

### 3. ✅ Backend Ya Maneja Eventos "brush"

**Archivo**: `BESTLIB/layouts/reactive.py`

**Estado**: Ya estaba implementado correctamente
- El handler central (`_register_central_select_handler()`) ya está registrado para eventos "brush" (línea 257)
- El handler procesa eventos "brush" de la misma manera que "select"

## Flujo de Eventos

1. **Usuario hace brush en scatterplot**:
   - D3 brush detecta el evento
   - Se muestra el rectángulo de selección
   - Se resaltan los puntos dentro del área

2. **Al soltar (brush.on('end'))**:
   - Se calculan los índices de puntos seleccionados
   - Se actualiza la visualización
   - Se llama a `sendSelectionEvent()` que envía evento "select"
   - Se envía explícitamente evento "brush" con los items seleccionados

3. **Backend recibe eventos**:
   - `CommManager._handle_message()` recibe el mensaje
   - `EventManager.emit()` ejecuta handlers registrados
   - Handler central procesa el evento:
     - Actualiza SelectionModel específico de la vista
     - Actualiza SelectionModel principal
     - Guarda en variable Python usando `set_selection()`
     - Dispara actualizaciones de gráficos vinculados

4. **Gráficos vinculados se actualizan**:
   - Los callbacks registrados en SelectionModels se ejecutan
   - `update_histogram()`, `update_boxplot()`, etc. procesan los items
   - Crean DataFrame filtrado y actualizan el gráfico con JavaScript

## Verificación

- ✅ Brush de D3 está implementado y funcional
- ✅ Overlay del brush captura eventos correctamente
- ✅ Eventos "brush" se envían explícitamente al backend
- ✅ Backend maneja eventos "brush" correctamente
- ✅ Handler central procesa eventos "brush"
- ✅ Gráficos vinculados se actualizan cuando hay selección

## Uso

```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear layout
layout = ReactiveMatrixLayout("ASH", selection_model=SelectionModel())
layout.set_data(df)

# Scatter plot principal con brush
layout.add_scatter('A', x_col='sepal_length', y_col='petal_length', interactive=True)

# Histogram vinculado (se actualiza cuando se hace brush en A)
layout.add_histogram('H', column='sepal_width', linked_to='A')

# Boxplot vinculado (se actualiza cuando se hace brush en A)
layout.add_boxplot('X', column='petal_width', linked_to='A')

# Mostrar
layout.display()

# Después de hacer brush en A:
# - El histogram H se actualiza con los datos filtrados
# - El boxplot X se actualiza con los datos filtrados
# - layout.get_selection() retorna los datos seleccionados
```

## Notas Importantes

1. **Brush Visual**: El rectángulo de selección se muestra automáticamente cuando el usuario arrastra sobre el scatterplot. Los estilos CSS aseguran que sea visible (azul con opacidad).

2. **Eventos Múltiples**: Se envían tanto "select" como "brush" para compatibilidad. El backend procesa ambos correctamente.

3. **Overlay**: El overlay del brush está configurado para capturar eventos de mouse, touch y pointer, asegurando compatibilidad con diferentes dispositivos.

4. **Performance**: Para datasets grandes (>1000 puntos), se limita el payload a 1000 items para optimizar el rendimiento.

