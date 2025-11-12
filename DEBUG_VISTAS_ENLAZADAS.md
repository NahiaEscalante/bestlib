# Debug de Vistas Enlazadas

## Problemas Corregidos

He identificado y corregido varios problemas en el sistema de vistas enlazadas:

### 1. **Problema con `SelectionModel.update()`**
   - **Problema**: El método `update()` no siempre disparaba los callbacks cuando traitlets no detectaba cambios
   - **Solución**: Ahora `update()` llama manualmente a los callbacks incluso si traitlets no detecta el cambio

### 2. **Falta de mensajes de debug**
   - **Problema**: No había forma de saber si los eventos se estaban recibiendo o procesando
   - **Solución**: Agregué mensajes de debug detallados en cada paso del proceso

## Cómo Activar Debug

Para diagnosticar problemas con vistas enlazadas, activa el modo debug:

```python
from BESTLIB.matrix import MatrixLayout
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

# Activar debug
MatrixLayout.set_debug(True)

# Tu código normal
selection = SelectionModel()
layout = ReactiveMatrixLayout("SB", selection_model=selection)
layout.add_scatter('S', df, x_col='x', y_col='y', interactive=True)
layout.add_barchart('B', category_col='category', linked_to='S')
layout.display()
```

Con debug activado, verás mensajes como:
- `🔗 [ReactiveMatrixLayout] Registrando callback para bar chart 'B' enlazado a scatter 'S'`
- `✅ [ReactiveMatrixLayout] Evento recibido para scatter 'S': 5 items`
- `🔄 [ReactiveMatrixLayout] Callback ejecutado: Actualizando bar chart 'B' con 5 items seleccionados`

## Checklist de Verificación

Si las vistas enlazadas no funcionan, verifica:

### 1. Orden de creación
```python
# ✅ CORRECTO: Scatter primero, luego bar chart
layout.add_scatter('S', df, ...)
layout.add_barchart('B', category_col='cat', linked_to='S')

# ❌ INCORRECTO: Bar chart antes del scatter
layout.add_barchart('B', category_col='cat')  # Error: no hay scatter plot
layout.add_scatter('S', df, ...)
```

### 2. Nombre de columna correcto
```python
# Asegúrate de que la columna existe en tu DataFrame
layout.add_barchart('B', category_col='dept')  # 'dept' debe existir en df
```

### 3. Scatter plot con interactive=True
```python
# ✅ CORRECTO
layout.add_scatter('S', df, x_col='x', y_col='y', interactive=True)

# ❌ INCORRECTO: Sin interactive, no se pueden seleccionar datos
layout.add_scatter('S', df, x_col='x', y_col='y', interactive=False)
```

### 4. Verificar que el evento se envía
Abre la consola del navegador (F12) y busca mensajes de error o logs de `sendEvent`.

### 5. Verificar que el callback se registra
Con debug activado, deberías ver:
```
🔗 [ReactiveMatrixLayout] Registrando callback para bar chart 'B' enlazado a scatter 'S'
   - SelectionModel ID: 123456789
   - Callbacks actuales: 1
```

## Ejemplo Completo de Diagnóstico

```python
from BESTLIB.matrix import MatrixLayout
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Activar debug
MatrixLayout.set_debug(True)

# Crear datos de prueba
df = pd.DataFrame({
    'x': [1, 2, 3, 4, 5],
    'y': [2, 4, 6, 8, 10],
    'category': ['A', 'B', 'A', 'B', 'A']
})

# Crear layout
selection = SelectionModel()
layout = ReactiveMatrixLayout("SB", selection_model=selection)

# Agregar scatter plot PRIMERO
print("1. Agregando scatter plot...")
layout.add_scatter('S', df, x_col='x', y_col='y', category_col='category', interactive=True)

# Agregar bar chart DESPUÉS
print("2. Agregando bar chart enlazado...")
layout.add_barchart('B', category_col='category', linked_to='S')

# Mostrar
print("3. Mostrando layout...")
layout.display()

# Verificar que el callback está registrado
print(f"4. Callbacks registrados en scatter 'S': {len(layout._scatter_selection_models['S']._callbacks)}")
```

## Problemas Comunes

### Problema: "No hay scatter plots disponibles"
**Causa**: Intentaste agregar un bar chart antes de agregar un scatter plot.
**Solución**: Siempre agrega el scatter plot primero.

### Problema: El bar chart no se actualiza
**Posibles causas**:
1. El scatter plot no tiene `interactive=True`
2. La columna `category_col` no existe en el DataFrame
3. El evento no se está enviando desde JavaScript (revisa consola del navegador)
4. El callback no se está ejecutando (activa debug para verificar)

### Problema: "Scatter plot 'X' no existe"
**Causa**: Especificaste `linked_to='X'` pero no existe un scatter plot con letra 'X'.
**Solución**: Verifica que el scatter plot existe y usa la letra correcta.

## Si Aún No Funciona

1. Activa debug: `MatrixLayout.set_debug(True)`
2. Revisa los mensajes en la consola de Python
3. Revisa la consola del navegador (F12) para errores de JavaScript
4. Verifica que el comm está funcionando (deberías ver mensajes de "Comm abierto")
5. Prueba con datos simples primero (como el ejemplo de arriba)

