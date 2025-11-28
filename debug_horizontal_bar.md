# Debug Horizontal Bar Chart

## Problema
El gráfico `horizontal_bar` no se renderiza, muestra `[object Object]` en lugar del gráfico.

## Pasos para depurar

1. **Abre la consola del navegador** (F12 en Chrome/Firefox, o Cmd+Option+I en Mac)

2. **Ejecuta el código** y revisa los mensajes de consola:
   - Deberías ver: `renderChartD3: Tipo de gráfico detectado`
   - Deberías ver: `renderChartD3: Llamando renderHorizontalBarD3`
   - Deberías ver: `renderHorizontalBarD3: Iniciando renderizado`
   - Deberías ver: `renderHorizontalBarD3: Datos encontrados`
   - Deberías ver: `renderHorizontalBarD3: Renderizado completado exitosamente`

3. **Si hay errores en la consola**, compártelos para poder corregirlos.

4. **Verifica que el JavaScript se haya cargado**:
   - En la consola, escribe: `typeof renderHorizontalBarD3`
   - Debería mostrar: `"function"`

5. **Si el JavaScript no se ha cargado**, necesitas:
   - Reiniciar el kernel/runtime de Jupyter/Colab
   - Asegurarte de que el archivo `matrix.js` se haya actualizado

## Código de prueba

```python
import pandas as pd
from BESTLIB.matrix import MatrixLayout

# Crear datos
df = pd.DataFrame({
    'sepal_length': [5.1, 4.9, 4.7, 4.6, 5.0],
    'sepal_width': [3.5, 3.0, 3.2, 3.1, 3.6]
})

# Limpiar mapping
MatrixLayout._map = {}

# Crear layout
layout = MatrixLayout("L")

# Agregar gráfico
MatrixLayout.map_horizontal_bar(
    "L",
    df,
    category_col="sepal_width",
    value_col="sepal_length",
    strokeWidth=2,
    markers=True
)

# Verificar el spec antes de mostrar
print("Spec creado:", MatrixLayout._map.get('L'))

# Mostrar
layout.display()
```

## Posibles causas

1. **JavaScript no actualizado**: El archivo `matrix.js` no se ha recargado. Solución: Reiniciar kernel/runtime.

2. **Error de JavaScript**: Hay un error que impide la ejecución. Solución: Revisar consola del navegador.

3. **Datos vacíos**: Los datos no se están procesando correctamente. Solución: Verificar el spec con `print(MatrixLayout._map.get('L'))`.

4. **D3 no disponible**: D3.js no se ha cargado. Solución: Verificar que D3 se cargue antes del renderizado.

