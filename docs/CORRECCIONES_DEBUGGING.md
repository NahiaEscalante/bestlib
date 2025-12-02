# Correcciones Aplicadas + Sistema de Debugging

## Fecha: Diciembre 2025

---

## ✅ CORRECCIONES COMPLETADAS

### 1. Error 3: ImportError en Violin Plot ✅

**Problema:**
```python
ImportError: cannot import name 'process_figsize_in_kwargs' from 'BESTLIB.charts.spec_utils'
```

**Solución Aplicada:**
Corregido el import en `BESTLIB/charts/violin.py`:

```python
# ANTES (línea 153):
from ..charts.spec_utils import process_figsize_in_kwargs

# DESPUÉS:
from ..utils.figsize import process_figsize_in_kwargs
```

**Estado:** ✅ COMPLETADO

---

### 2. Sistema de Debugging Agregado 🔍

Para investigar los Errores 1, 4 y 5 (boxplots y barcharts que no se actualizan), he agregado logging detallado en puntos clave del flujo de eventos:

#### Logging agregado en:

1. **`BESTLIB/layouts/reactive.py` - `scatter_handler` (línea ~307):**
   ```python
   print(f"🔵 [scatter_handler] Evento recibido para scatter '{scatter_letter_capture}'")
   print(f"   - Payload keys: {list(payload.keys())}")
   print(f"   - Items count: {len(items)}")
   print(f"   - Event letter: {event_scatter_letter}")
   print(f"   ✅ Evento aceptado, actualizando SelectionModel ID: {id(scatter_selection_capture)}")
   print(f"   - Callbacks registrados en SelectionModel: {len(scatter_selection_capture._callbacks)}")
   print(f"   - SelectionModel.update() completado")
   ```

2. **`BESTLIB/layouts/reactive.py` - `update_boxplot` (línea ~2178):**
   ```python
   print(f"🟢 [update_boxplot] Callback ejecutado para boxplot '{letter}'")
   print(f"   - Items count: {count}")
   print(f"   - Primary letter: {primary_letter}")
   print(f"   - SelectionModel ID: {id(primary_selection)}")
   ```

3. **`BESTLIB/reactive.py` - `ReactiveData.update` (línea ~208):**
   ```python
   print(f"🟡 [ReactiveData.update] Actualizando ID: {id(self)}")
   print(f"   - Items type: {type(items)}")
   print(f"   - Items count: {len(items) if hasattr(items, '__len__') else '?'}")
   print(f"   - Callbacks registrados: {len(self._callbacks)}")
   print(f"   - Nuevo count: {new_count}")
   ```

---

## 🧪 CÓMO USAR EL SISTEMA DE DEBUGGING

### Paso 1: Ejecutar un ejemplo problemático

Por ejemplo, el Ejemplo 1 (Scatter + Boxplot):

```python
from BESTLIB.layouts.reactive import ReactiveMatrixLayout
import pandas as pd
import numpy as np

# Crear datos
np.random.seed(42)
df_iris = pd.DataFrame({
    'petal_length': np.concatenate([
        np.random.normal(1.5, 0.2, 50),
        np.random.normal(4.5, 0.5, 50),
        np.random.normal(5.5, 0.6, 50)
    ]),
    'petal_width': np.concatenate([
        np.random.normal(0.3, 0.1, 50),
        np.random.normal(1.3, 0.2, 50),
        np.random.normal(2.0, 0.3, 50)
    ]),
    'species': ['setosa'] * 50 + ['versicolor'] * 50 + ['virginica'] * 50
})

# Crear layout
demo1 = ReactiveMatrixLayout("SX")
demo1.set_data(df_iris)

demo1.add_scatter(
    'S',
    x_col='petal_length',
    y_col='petal_width',
    category_col='species',
    interactive=True,
    title='SCATTER: Arrastra para seleccionar'
)

demo1.add_boxplot(
    'X',
    column='petal_length',
    category_col='species',
    linked_to='S',
    title='BOXPLOT: Actualizado dinámicamente'
)

demo1.display()
```

### Paso 2: Hacer una selección con brush en el scatter

Arrastra sobre algunos puntos en el scatter plot.

### Paso 3: Observar los mensajes de log

Deberías ver una secuencia como esta:

```
🔵 [scatter_handler] Evento recibido para scatter 'S'
   - Payload keys: ['type', 'items', 'count', '__view_letter__', '__scatter_letter__', ...]
   - Items count: 25
   - Event letter: S
   ✅ Evento aceptado, actualizando SelectionModel ID: 140123456789
   - Callbacks registrados en SelectionModel: 1
🟡 [ReactiveData.update] Actualizando ID: 140123456789
   - Items type: <class 'list'>
   - Items count: 25
   - Callbacks registrados: 1
   - Nuevo count: 25
🟢 [update_boxplot] Callback ejecutado para boxplot 'X'
   - Items count: 25
   - Primary letter: S
   - SelectionModel ID: 140123456789
   ✅ Boxplot 'X' actualizado en DOM
```

### Paso 4: Diagnosticar el problema

**Si NO ves ningún mensaje:**
- El evento de JavaScript NO está llegando a Python
- Problema: `sendSelectionEvent` en `matrix.js` no está funcionando
- Solución: Verificar que el comm esté registrado correctamente

**Si ves 🔵 pero NO ves 🟡:**
- El evento llega a `scatter_handler` pero NO llama a `SelectionModel.update()`
- Problema: El `scatter_selection_capture` puede ser None o incorrecto
- Solución: Verificar que el SelectionModel se crea correctamente

**Si ves 🟡 pero NO ves 🟢:**
- `SelectionModel.update()` se ejecuta pero NO llama a los callbacks
- Problema: Los callbacks no están registrados o se registraron en un SelectionModel diferente
- Solución: Verificar que `id(scatter_selection_capture)` == `id(primary_selection)`

**Si ves 🟢:**
- El callback se ejecuta correctamente
- Si el boxplot NO se actualiza visualmente, el problema está en el JavaScript generado
- Solución: Verificar que el JavaScript de actualización del DOM sea correcto

---

## 🔍 DIAGNÓSTICO ESPERADO

### Escenario A: Todo funciona correctamente

```
🔵 [scatter_handler] Evento recibido para scatter 'S'
   ✅ Evento aceptado, actualizando SelectionModel ID: 140123456789
   - Callbacks registrados en SelectionModel: 1
🟡 [ReactiveData.update] Actualizando ID: 140123456789
   - Callbacks registrados: 1
🟢 [update_boxplot] Callback ejecutado para boxplot 'X'
   ✅ Boxplot 'X' actualizado en DOM
```

**Resultado:** Boxplot se actualiza visualmente ✅

---

### Escenario B: Evento no llega a Python

```
(No hay mensajes)
```

**Diagnóstico:** El JavaScript no está enviando eventos o el comm no está registrado.

**Solución:**
1. Verificar que `sendEvent` en `matrix.js` está funcionando
2. Agregar `console.log` en JavaScript:
   ```javascript
   console.log('🔴 [Brush End] Enviando evento de selección');
   sendSelectionEvent(selectedIndices);
   ```

---

### Escenario C: Evento llega pero no actualiza SelectionModel

```
🔵 [scatter_handler] Evento recibido para scatter 'S'
   ✅ Evento aceptado, actualizando SelectionModel ID: 140123456789
   - Callbacks registrados en SelectionModel: 0  ← ⚠️ PROBLEMA
(No hay más mensajes)
```

**Diagnóstico:** El SelectionModel NO tiene callbacks registrados.

**Solución:**
1. Verificar que `add_boxplot` se llama DESPUÉS de `add_scatter`
2. Verificar que `linked_to='S'` coincide con la letra del scatter
3. Agregar print en `add_boxplot`:
   ```python
   print(f"Registrando callback en SelectionModel ID: {id(primary_selection)}")
   primary_selection.on_change(update_boxplot)
   print(f"Callbacks ahora: {len(primary_selection._callbacks)}")
   ```

---

### Escenario D: SelectionModels diferentes

```
🔵 [scatter_handler] Evento recibido para scatter 'S'
   ✅ Evento aceptado, actualizando SelectionModel ID: 140111111111
   - Callbacks registrados en SelectionModel: 0
🟡 [ReactiveData.update] Actualizando ID: 140111111111
   - Callbacks registrados: 0
(No se ejecuta update_boxplot)

# Pero en add_boxplot se registró en:
Registrando callback en SelectionModel ID: 140222222222  ← ⚠️ DIFERENTE
```

**Diagnóstico:** Los callbacks están registrados en un SelectionModel DIFERENTE al que se actualiza.

**Solución:**
1. Asegurar que `scatter_selection_capture` y `primary_selection` sean el MISMO objeto
2. Verificar que `self._primary_view_models[letter]` guarda el mismo SelectionModel que se crea en `add_scatter`

---

## 📝 PRÓXIMOS PASOS

### Para el usuario:

1. **Ejecutar los ejemplos con el logging activado**
2. **Copiar y pegar TODOS los mensajes de log** en un archivo de texto
3. **Compartir los logs** para que pueda diagnosticar el problema exacto
4. **Indicar qué escenario (A, B, C o D) se parece más** a lo que ves

### Para el desarrollador (yo):

Según los logs, aplicaré una de estas soluciones:

- **Escenario B:** Arreglar `sendEvent` en JavaScript
- **Escenario C:** Arreglar el orden de registro de callbacks
- **Escenario D:** Unificar los SelectionModels

---

## 🎯 OBJETIVO

Con este sistema de debugging, podremos identificar EXACTAMENTE dónde se rompe el flujo de eventos y aplicar la corrección precisa.

**No más adivinanzas - debugging basado en datos reales.**

