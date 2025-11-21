# Fix BESTLIB Selection + Brushing + Linking (Python ↔ JS sync)

## Problemas Corregidos

### 1. ✅ `initial_data` UnboundLocalError en `add_histogram`

**Problema**: `initial_data` no estaba siempre definido antes de los returns tempranos, causando `UnboundLocalError`.

**Solución**: 
- Inicializar `initial_data = self._data` al principio de `add_histogram()` (línea ~1143)
- Asegurar que todos los returns tempranos usen `initial_data` en lugar de `self._data`
- En `add_boxplot()`, cambiar `data_to_use = initial_data if 'initial_data' in locals() else self._data` a `data_to_use = initial_data` ya que `initial_data` siempre está definido

### 2. ✅ Eventos select/brush se registran correctamente

**Problema**: Los handlers de eventos se registraban pero podían no ejecutarse correctamente.

**Solución**:
- Los handlers ya se registraban correctamente con `self._layout.on('select', handler)`
- Asegurar que los handlers usen `set_selection()` para guardar en variables Python
- Los handlers de `scatter_handler`, `histogram_handler`, y `pie_handler` ahora usan `self.set_selection()` consistentemente

### 3. ✅ Gráficos vinculados usan datos filtrados

**Problema**: Los gráficos vinculados no se inicializaban con datos filtrados si ya había una selección activa.

**Solución**:
- En `add_histogram()`: Verificar si hay una selección activa en la vista principal antes de crear el histograma
- Si hay selección activa, procesar los items y crear un DataFrame filtrado para `initial_data`
- En `add_boxplot()`: Similar verificación y procesamiento de selección activa
- Los gráficos vinculados ahora se inicializan con datos filtrados si hay una selección activa

### 4. ✅ Python puede acceder a selecciones

**Problema**: Las selecciones no se guardaban correctamente en variables Python.

**Solución**:
- Todos los handlers (`scatter_handler`, `histogram_handler`, `pie_handler`) ahora usan `self.set_selection(selection_var, items_df)` para guardar en variables Python
- `set_selection()` guarda en `__main__` para que las variables sean accesibles globalmente
- `get_selection()` permite recuperar selecciones guardadas

## Cambios Realizados

### `BESTLIB/layouts/reactive.py`

1. **`add_histogram()` (línea ~1118)**:
   - Inicializar `initial_data = self._data` al principio
   - Verificar selección activa en vista principal antes de crear histograma
   - Procesar items y crear DataFrame filtrado si hay selección
   - Usar `initial_data` en todos los returns tempranos

2. **`add_boxplot()` (línea ~1680)**:
   - Cambiar `data_to_use = initial_data if 'initial_data' in locals() else self._data` a `data_to_use = initial_data`
   - `initial_data` siempre está definido (se inicializa en línea ~2142)

3. **`scatter_handler()` (línea ~236)**:
   - Agregar llamada a `self.set_selection()` si hay `selection_var` para este scatter

4. **`histogram_handler()` (línea ~1196)**:
   - Cambiar `setattr(__main__, selection_var, ...)` a `self.set_selection(selection_var, ...)`

5. **`pie_handler()` (línea ~2531)**:
   - Ya usa `self.set_selection()` correctamente (verificado)

## Flujo de Eventos

1. **JavaScript → Python**:
   - Scatter plot envía evento 'select' con `__scatter_letter__` o `__view_letter__`
   - `CommManager._handle_message()` recibe el mensaje
   - Busca instancia por `div_id` y emite evento al `EventManager` de `MatrixLayout`
   - `EventManager.emit()` ejecuta todos los handlers registrados

2. **Handlers en ReactiveMatrixLayout**:
   - `scatter_handler`: Filtra por `__scatter_letter__`, actualiza `SelectionModel`, guarda en variable Python
   - `histogram_handler`: Filtra por `__view_letter__`, actualiza `SelectionModel`, guarda en variable Python
   - `pie_handler`: Filtra por `__view_letter__`, actualiza `SelectionModel`, guarda en variable Python

3. **Actualización de Gráficos Vinculados**:
   - Cuando `SelectionModel.update()` se llama, dispara callbacks registrados (`update_histogram`, `update_boxplot`)
   - Los callbacks procesan los items, crean DataFrame filtrado, y actualizan el gráfico con JavaScript

## Uso

```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear layout
layout = ReactiveMatrixLayout("ASH", selection_model=SelectionModel())
layout.set_data(df)

# Scatter plot principal
layout.add_scatter('A', x_col='sepal_length', y_col='petal_length', interactive=True)

# Histogram vinculado
layout.add_histogram('H', column='sepal_width', linked_to='A')

# Boxplot vinculado
layout.add_boxplot('X', column='petal_width', linked_to='A')

# Pie chart con variable de selección
layout.add_pie('P', category_col='species', interactive=True, selection_var='selected_pie_category')

# Mostrar
layout.display()

# Más tarde, acceder a selecciones
selected = layout.get_selection('selected_pie_category')
# O directamente desde __main__
import __main__
selected = getattr(__main__, 'selected_pie_category', [])
```

## Verificación

- ✅ `initial_data` siempre está definido en `add_histogram` y `add_boxplot`
- ✅ Handlers se registran correctamente con `self._layout.on('select', handler)`
- ✅ Gráficos vinculados se inicializan con datos filtrados si hay selección activa
- ✅ Selecciones se guardan en variables Python usando `set_selection()`
- ✅ Python puede acceder a selecciones usando `get_selection()` o directamente desde `__main__`

