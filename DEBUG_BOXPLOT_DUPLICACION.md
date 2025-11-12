# 🐛 Debug: Duplicación de Matriz con Boxplot

## Problema Reportado

Cuando se hace brush selection en el scatter plot 'A' en un layout grande (3x3), el boxplot 'X' debería actualizarse, pero en lugar de eso, la matriz de gráficos empieza a crecer (duplicación).

**Funciona correctamente** en layouts pequeños (2x2).

## Cambios Realizados

### 1. Eliminada actualización del mapping global en callback
- **Línea 1699-1703**: Eliminada la actualización de `MatrixLayout._map[letter]` en el callback `update_boxplot`
- **Razón**: Actualizar el mapping global puede causar que el sistema detecte cambios y re-renderice todo el layout

### 2. Mejoras en JavaScript de actualización
- **Flag de actualización**: Agregado `window._bestlib_updating_boxplot_{letter}` para evitar actualizaciones simultáneas
- **Desconexión de ResizeObserver**: Desconectado antes de actualizar la celda para evitar re-renders
- **Limpieza selectiva**: Solo se remueve el SVG, no se usa `innerHTML = ''`
- **Marcado de celda**: Se marca `_chartSpec = null` para evitar que ResizeObserver intente re-renderizar

## Posibles Causas Adicionales

### 1. ResizeObserver
El `ResizeObserver` en `matrix.js` (línea 385) podría estar detectando cambios cuando se modifica el contenido de la celda y causando re-renders.

**Solución aplicada**: Desconectar el ResizeObserver antes de actualizar.

### 2. Múltiples callbacks
Si hay múltiples callbacks registrados para el mismo evento, podrían estar ejecutándose múltiples veces.

**Verificar**: 
```python
MatrixLayout.set_debug(True)
# Luego ejecutar el código y ver cuántos callbacks se ejecutan
```

### 3. JavaScript ejecutándose múltiples veces
El JavaScript podría estar ejecutándose múltiples veces si hay algún problema con el sistema de eventos.

**Verificar**: Agregar `console.log` en el JavaScript para ver cuántas veces se ejecuta.

### 4. Problema con `display(Javascript(...))`
El método `display(Javascript(...))` podría estar causando que se re-ejecute el render completo.

**Verificar**: Ver si hay algún listener que detecte cuando se ejecuta JavaScript.

## Pasos para Diagnosticar

1. **Activar modo debug**:
```python
from BESTLIB.matrix import MatrixLayout
MatrixLayout.set_debug(True)
```

2. **Ejecutar el código problemático** y observar:
   - ¿Cuántas veces se ejecuta el callback `update_boxplot`?
   - ¿Hay mensajes de error en la consola del navegador?
   - ¿Se está llamando a `render()` múltiples veces?

3. **Verificar en la consola del navegador**:
   - Abrir DevTools (F12)
   - Ir a la pestaña Console
   - Buscar mensajes de error o warnings
   - Verificar si hay múltiples llamadas a `render()`

4. **Verificar el DOM**:
   - Inspeccionar el elemento del layout
   - Ver si hay múltiples contenedores con el mismo `div_id`
   - Verificar si hay múltiples celdas con la misma letra

## Código de Prueba

```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
from BESTLIB.matrix import MatrixLayout
import pandas as pd

# Activar debug
MatrixLayout.set_debug(True)

# Cargar datos
df = pd.read_csv('examples/iris.csv')

# Crear layout
layout_completo = ReactiveMatrixLayout("""
AHB
XPV
CYR
""", selection_model=SelectionModel())

layout_completo.set_data(df)

# Scatter plot
layout_completo.add_scatter(
    'A',
    x_col='sepal_length',
    y_col='sepal_width',
    color_col='species',
    xLabel='Sepal Length', 
    yLabel='Sepal Width'
)

# Histogram
layout_completo.add_histogram(
    'H', 
    column='sepal_length', 
    bins=15,
    xLabel='Sepal Length', 
    yLabel='Frequency'
)

# Bar chart
layout_completo.add_barchart(
    'B', 
    category_col='species',
    xLabel='Species', 
    yLabel='Count'
)

# Boxplot (el problemático)
layout_completo.add_boxplot(
    'X', 
    column='petal_length', 
    category_col='species',
    xLabel='Species', 
    yLabel='Petal Length',
    linked_to='A'
)

# Resto de gráficos...
layout_completo.add_pie('P', category_col='species')
layout_completo.add_violin('V', value_col='sepal_width', category_col='species', bins=20, xLabel='Species', yLabel='Sepal Width')
layout_completo.add_star_coordinates('C', features=['sepal_length', 'sepal_width', 'petal_length', 'petal_width'], class_col='species')
layout_completo.add_parallel_coordinates('Y', dimensions=['sepal_length', 'sepal_width', 'petal_length', 'petal_width'], category_col='species')
layout_completo.add_radviz('R', features=['sepal_length', 'sepal_width', 'petal_length', 'petal_width'], class_col='species')

# Mostrar
layout_completo.display()

# Ahora hacer brush selection en 'A' y observar los mensajes de debug
```

## Próximos Pasos

Si el problema persiste después de estos cambios:

1. **Verificar si hay otros gráficos que también actualizan el mapping** en callbacks
2. **Revisar si hay algún problema con el sistema de eventos** que cause múltiples ejecuciones
3. **Verificar si el problema está en cómo se ejecuta el JavaScript** desde Python
4. **Considerar usar un enfoque diferente** para actualizar gráficos enlazados (por ejemplo, usar un sistema de eventos más robusto)

## Notas

- El problema solo ocurre en layouts grandes (3x3), no en layouts pequeños (2x2)
- Esto sugiere que podría haber un problema con cómo se manejan múltiples gráficos simultáneamente
- Podría ser un problema de timing o de orden de ejecución

