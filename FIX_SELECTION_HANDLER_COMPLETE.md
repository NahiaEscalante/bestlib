# Fix BESTLIB: Missing "select" Handler + Python-Sync + Linked Updates

## Problemas Corregidos

### 1. ✅ Handler Centralizado para Eventos "select" y "brush"

**Problema**: Los eventos "select" y "brush" llegaban al backend pero no se enrutaban al SelectionModel, causando que:
- Las variables de selección nunca se actualizaran
- `get_selection()` siempre retornara vacío
- Los gráficos vinculados no se actualizaran

**Solución**: 
- Implementado `_register_central_select_handler()` que se registra en `__init__` de `ReactiveMatrixLayout`
- Este handler captura TODOS los eventos "select" y "brush" que llegan al backend
- El handler:
  1. Extrae `__view_letter__` o `__scatter_letter__` del payload
  2. Actualiza el SelectionModel específico de la vista (si existe)
  3. Actualiza el SelectionModel principal
  4. Guarda en variable Python usando `set_selection()` si existe `selection_var`
  5. Dispara actualizaciones de gráficos vinculados

### 2. ✅ Sincronización Python ↔ JS

**Problema**: `get_selection()` no retornaba DataFrames correctamente y las variables no se actualizaban.

**Solución**:
- Mejorado `get_selection()` para:
  - Buscar variables en `__main__`
  - Convertir items a DataFrame usando `_items_to_dataframe()`
  - Retornar DataFrame vacío si no hay selección
  - Buscar en `_selection_variables` para encontrar la letra correspondiente
  - Retornar selección del modelo principal si no se especifica variable

### 3. ✅ Actualización de Gráficos Vinculados

**Problema**: Los gráficos vinculados no se actualizaban cuando había una selección.

**Solución**:
- Implementado `_trigger_linked_updates()` que busca todos los gráficos vinculados a una vista principal
- Los gráficos vinculados ya tienen callbacks registrados en los SelectionModels, pero ahora se verifica que estén activos
- El handler central dispara actualizaciones cuando detecta una selección

### 4. ✅ Histogram Init Bug

**Problema**: `add_histogram()` crasheaba con `UnboundLocalError: initial_data not defined`.

**Solución** (ya aplicada en fix anterior):
- `initial_data` se inicializa al principio de `add_histogram()` con `initial_data = self._data`
- Se verifica si hay una selección activa antes de crear el histograma
- Si hay selección activa, se procesa y se crea un DataFrame filtrado

## Cambios Realizados

### `BESTLIB/layouts/reactive.py`

1. **`__init__()` (línea ~193)**:
   - Agregada llamada a `self._register_central_select_handler()` al final de la inicialización

2. **`_register_central_select_handler()` (línea ~195)**:
   - Nuevo método que registra un handler genérico centralizado
   - Handler procesa eventos "select" y "brush"
   - Actualiza SelectionModels y variables Python
   - Dispara actualizaciones de gráficos vinculados

3. **`_trigger_linked_updates()` (línea ~262)**:
   - Nuevo método que busca y dispara actualizaciones de gráficos vinculados
   - Busca en `_linked_charts` para encontrar gráficos vinculados a una vista principal

4. **`get_selection()` (línea ~3642)**:
   - Mejorado para retornar DataFrames correctamente
   - Usa `_items_to_dataframe()` para convertir items
   - Busca en `_selection_variables` para encontrar la letra correspondiente
   - Retorna DataFrame vacío si no hay selección

## Flujo de Eventos

1. **JavaScript → Python**:
   - Usuario hace click/brush en un gráfico
   - JavaScript envía evento 'select' con `__view_letter__` o `__scatter_letter__`
   - `CommManager._handle_message()` recibe el mensaje
   - Busca instancia por `div_id` y emite evento al `EventManager` de `MatrixLayout`

2. **EventManager → Handlers**:
   - `EventManager.emit()` ejecuta todos los handlers registrados en orden
   - Handlers específicos (pie_handler, scatter_handler, etc.) se ejecutan primero
   - Handler central se ejecuta después (o como fallback si no hay handlers específicos)

3. **Handler Central**:
   - Extrae `view_letter` del payload
   - Actualiza SelectionModel específico de la vista
   - Actualiza SelectionModel principal
   - Guarda en variable Python usando `set_selection()`
   - Dispara actualizaciones de gráficos vinculados

4. **Actualización de Gráficos Vinculados**:
   - Los callbacks registrados en SelectionModels se ejecutan automáticamente
   - `update_histogram()`, `update_boxplot()`, etc. procesan los items
   - Crean DataFrame filtrado y actualizan el gráfico con JavaScript

## Uso

```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear layout
layout = ReactiveMatrixLayout("P", selection_model=SelectionModel())
layout.set_data(df)

# Pie chart con variable de selección
layout.add_pie(
    'P',
    category_col='species',
    interactive=True,
    selection_var='selected_pie_category'
)

# Mostrar
layout.display()

# Más tarde, acceder a selecciones
selected = layout.get_selection('selected_pie_category')
print(pd.DataFrame(selected))  # Debe mostrar las filas seleccionadas

# O directamente desde __main__
import __main__
selected = getattr(__main__, 'selected_pie_category', pd.DataFrame())
print(selected)
```

## Verificación

- ✅ Handler central se registra en `__init__` de `ReactiveMatrixLayout`
- ✅ Handler central captura eventos "select" y "brush"
- ✅ Handler central actualiza SelectionModels y variables Python
- ✅ `get_selection()` retorna DataFrames correctamente
- ✅ Gráficos vinculados se actualizan cuando hay selección
- ✅ Histogram init bug está corregido

## Notas Importantes

1. **Orden de Ejecución**: El handler central se registra en `__init__`, pero los handlers específicos se registran después (en `add_pie()`, `add_scatter()`, etc.). EventManager ejecuta todos los handlers en orden, así que:
   - Handlers específicos se ejecutan primero (si coinciden con el evento)
   - Handler central se ejecuta después (como fallback o procesamiento adicional)

2. **Compatibilidad**: El handler central es compatible con handlers específicos existentes. Si un handler específico procesa el evento, el handler central también se ejecuta para asegurar que las variables y SelectionModels se actualicen.

3. **Debug**: Activar debug con `ReactiveMatrixLayout.set_debug(True)` o `MatrixLayout.set_debug(True)` para ver mensajes detallados del handler central.

