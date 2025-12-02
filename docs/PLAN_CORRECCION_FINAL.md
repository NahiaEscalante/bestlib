# Plan de Corrección Final - Errores Restantes

## Análisis Profundo de Errores

### Error 1 y 5: Boxplot NO se actualiza (PROBLEMA CRÍTICO)

**Síntoma:**
- Callback `update_boxplot` se registra correctamente
- SelectionModel tiene el callback en `_callbacks`
- Pero el callback NUNCA se ejecuta cuando hay selección en scatter

**Causa Raíz Identificada:**

1. **Problema de enrutamiento de eventos:**
   - El scatter plot envía eventos con `__scatter_letter__` en el payload
   - El `scatter_handler` en `add_scatter` filtra por `__scatter_letter__`
   - Luego llama a `scatter_selection_capture.update(data_to_update)`
   - PERO: `scatter_selection_capture` es el SelectionModel del scatter
   - Los callbacks de boxplot están registrados en `primary_selection`
   - Si `scatter_selection_capture` != `primary_selection`, los callbacks no se ejecutan

2. **Verificación:**
   ```python
   # En add_scatter (línea 340):
   scatter_selection_capture.update(data_to_update)  # ← Actualiza el SelectionModel del scatter
   
   # En add_boxplot (línea 2368):
   primary_selection.on_change(update_boxplot)  # ← Registra callback en primary_selection
   
   # Si scatter_selection_capture != primary_selection, el callback nunca se ejecuta
   ```

3. **Confirmación del problema:**
   - `add_scatter` crea `scatter_selection = SelectionModel()` (línea ~300)
   - Lo guarda en `self._scatter_selection_models[letter]` (línea ~295)
   - También lo guarda en `self._primary_view_models[letter]` (línea ~296)
   - `add_boxplot` busca en `self._primary_view_models[linked_to]` (línea ~2120)
   - DEBERÍA encontrar el mismo SelectionModel, PERO...
   - El closure `scatter_handler` captura `scatter_selection_capture` que es una COPIA local
   - Cuando se llama `.update()` en el closure, actualiza el SelectionModel correcto
   - PERO el problema es que el JavaScript NO está enviando eventos correctamente

4. **Problema real: JavaScript NO envía eventos de selección**
   - El scatter plot en `matrix.js` tiene código para brush selection
   - Llama a `sendSelectionEvent(selectedIndices)` (línea 6148)
   - PERO `sendSelectionEvent` puede no estar definido o no estar funcionando
   - Necesito verificar si `sendSelectionEvent` está correctamente implementado

**Solución:**

1. Verificar que `sendSelectionEvent` esté definido y funcional en `matrix.js`
2. Asegurar que el evento llegue al handler de Python
3. Agregar logging detallado para depurar el flujo

---

### Error 3: ImportError en Violin Plot

**Síntoma:**
```python
ImportError: cannot import name 'process_figsize_in_kwargs' from 'BESTLIB.charts.spec_utils'
```

**Causa:**
- `violin.py` intenta importar desde `..charts.spec_utils`
- Pero `process_figsize_in_kwargs` está en `..utils.figsize`

**Solución:**
Cambiar el import en `violin.py`:

```python
# ANTES
from ..charts.spec_utils import process_figsize_in_kwargs

# DESPUÉS
from ..utils.figsize import process_figsize_in_kwargs
```

---

### Error 4: Barcharts en matriz 2x2 no responden a selección

**Síntoma:**
- Los barcharts se muestran inicialmente (✅ Error 4 corregido)
- Pero NO se actualizan cuando hay selección en scatter

**Causa:**
Mismo problema que Error 1/5 - los eventos de selección no llegan o no se procesan correctamente.

**Solución:**
Misma que Error 1/5.

---

## Plan de Acción

### Paso 1: Corregir Error 3 (Violin Import) - SIMPLE

```python
# Archivo: BESTLIB/charts/violin.py
# Línea 153

# ANTES:
from ..charts.spec_utils import process_figsize_in_kwargs

# DESPUÉS:
from ..utils.figsize import process_figsize_in_kwargs
```

---

### Paso 2: Investigar flujo de eventos de selección - CRÍTICO

**Objetivo:** Entender por qué los eventos de selección no llegan a los callbacks.

**Pasos:**

1. **Verificar que `sendSelectionEvent` existe en `matrix.js`:**
   - Buscar la definición de `sendSelectionEvent`
   - Verificar que esté accesible desde `renderScatterPlotD3`

2. **Agregar logging en Python:**
   - En `scatter_handler`: print cuando se recibe evento
   - En `update_boxplot`: print cuando se ejecuta
   - En `SelectionModel.update`: print cuando se llama

3. **Agregar logging en JavaScript:**
   - En `sendSelectionEvent`: console.log antes de enviar
   - En brush end: console.log con selectedIndices

4. **Verificar el flujo completo:**
   ```
   JavaScript (brush) → sendSelectionEvent → 
   Python (scatter_handler) → scatter_selection.update() → 
   callbacks registrados → update_boxplot
   ```

---

### Paso 3: Corregir problema de eventos (según hallazgos)

**Opción A: Si `sendSelectionEvent` no está definido:**

Definir `sendSelectionEvent` en `matrix.js`:

```javascript
function sendSelectionEvent(selectedIndices, spec, divId) {
    const items = Array.from(selectedIndices).map(i => spec.data[i]);
    
    // Obtener el comm de Python
    const comm = window._bestlib_comms && window._bestlib_comms[divId];
    if (comm) {
        comm.send({
            type: 'select',
            items: items,
            count: items.length,
            __scatter_letter__: spec.__scatter_letter__ || spec.__view_letter__
        });
    }
}
```

**Opción B: Si el problema es el enrutamiento:**

Asegurar que `scatter_handler` actualice TODOS los SelectionModels relevantes:

```python
def scatter_handler(payload):
    # ... código existente ...
    
    # Actualizar el SelectionModel específico
    scatter_selection_capture.update(data_to_update)
    
    # TAMBIÉN actualizar en _primary_view_models si existe
    if letter in self._primary_view_models:
        self._primary_view_models[letter].update(data_to_update)
```

**Opción C: Si el problema es que no se llama `.update()`:**

Verificar que `scatter_selection_capture` sea el mismo objeto que `primary_selection`:

```python
# En add_scatter:
scatter_selection = SelectionModel()
self._scatter_selection_models[letter] = scatter_selection
self._primary_view_models[letter] = scatter_selection  # ← MISMO objeto

# En add_boxplot:
primary_selection = self._primary_view_models[linked_to]  # ← Debería ser el MISMO

# Verificar con:
assert id(scatter_selection) == id(primary_selection)
```

---

### Paso 4: Simplificar el sistema de eventos (si es necesario)

Si el problema persiste, considerar:

1. **Eliminar la indirección de `scatter_handler`:**
   - Registrar los callbacks directamente en el comm de JavaScript
   - Evitar múltiples capas de handlers

2. **Usar un único SelectionModel global:**
   - En lugar de uno por scatter, usar `self.selection_model`
   - Simplifica el enrutamiento

3. **Forzar actualización manual:**
   - En lugar de esperar eventos, actualizar manualmente después de cada selección
   - Menos elegante pero más robusto

---

## Debugging Inmediato

### Agregar prints de debug en lugares clave:

```python
# En BESTLIB/layouts/reactive.py

# 1. En scatter_handler (línea ~307):
def scatter_handler(payload):
    print(f"🔵 [scatter_handler] Evento recibido para scatter '{letter}'")
    print(f"   - Payload keys: {list(payload.keys())}")
    print(f"   - Items count: {len(payload.get('items', []))}")
    # ... resto del código ...
    print(f"   - Actualizando SelectionModel ID: {id(scatter_selection_capture)}")
    scatter_selection_capture.update(data_to_update)
    print(f"   - SelectionModel actualizado, callbacks: {len(scatter_selection_capture._callbacks)}")

# 2. En update_boxplot (línea ~2178):
def update_boxplot(items, count):
    print(f"🟢 [update_boxplot] Callback ejecutado para boxplot '{letter}'")
    print(f"   - Items count: {count}")
    print(f"   - SelectionModel ID: {id(primary_selection)}")
    # ... resto del código ...

# 3. En SelectionModel.update (BESTLIB/reactive.py, línea ~150):
def update(self, items):
    print(f"🟡 [SelectionModel.update] Actualizando con {len(items) if hasattr(items, '__len__') else '?'} items")
    print(f"   - SelectionModel ID: {id(self)}")
    print(f"   - Callbacks registrados: {len(self._callbacks)}")
    # ... resto del código ...
    print(f"   - Ejecutando {len(self._callbacks)} callbacks...")
```

### Agregar console.log en JavaScript:

```javascript
// En matrix.js, en brush end:
.on('end', (event) => {
    console.log('🔴 [Brush End] Selección finalizada');
    console.log('   - Selected indices:', Array.from(selectedIndices));
    console.log('   - Spec letter:', spec.__scatter_letter__ || spec.__view_letter__);
    
    sendSelectionEvent(selectedIndices);
    console.log('   - Evento enviado');
});
```

---

## Orden de Ejecución

1. ✅ **Paso 1:** Corregir import de violin (5 minutos)
2. 🔍 **Paso 2:** Agregar logging detallado (15 minutos)
3. 🧪 **Paso 3:** Ejecutar ejemplo 1 y observar logs (10 minutos)
4. 🔧 **Paso 4:** Aplicar corrección según hallazgos (30-60 minutos)
5. ✅ **Paso 5:** Verificar todos los ejemplos (15 minutos)

**Tiempo total estimado:** 1.5 - 2 horas

