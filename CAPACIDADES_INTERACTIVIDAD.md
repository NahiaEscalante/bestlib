# Capacidades de Interactividad en BESTLIB

## 📊 Gráficas con Selección de Datos

Las siguientes gráficas permiten extraer datos mediante selección (brush o click):

### 1. **Scatter Plot** ⭐ (Vista Principal)
- **Tipo de selección**: Brush (arrastrar área) + Click (punto individual)
- **Implementación**: 
  - Brush selection con `d3.brush()` para seleccionar múltiples puntos arrastrando
  - Click individual para seleccionar/deseleccionar puntos
  - Soporte para Ctrl/Cmd para agregar a la selección
- **Evento enviado**: `sendEvent(divId, 'select', {...})` con índices y datos originales
- **Uso**: 
  ```python
  layout.add_scatter('S', df, x_col='x', y_col='y', interactive=True)
  ```

### 2. **Bar Chart**
- **Tipo de selección**: Click en barra individual
- **Implementación**: Click en cada barra envía evento de selección
- **Evento enviado**: `sendEvent(divId, 'select', {...})` con el item seleccionado
- **Requisito**: Debe tener `interactive=True` en el spec
- **Uso**:
  ```python
  MatrixLayout.map_barchart('B', data, category_col='cat', interactive=True)
  ```

### 3. **Grouped Bar Chart**
- **Tipo de selección**: Click en barra individual del grupo
- **Implementación**: Click en cada barra del grupo envía evento de selección
- **Evento enviado**: `sendEvent(divId, 'select', {...})` con grupo y serie
- **Requisito**: Debe tener `interactive=True` en el spec
- **Uso**:
  ```python
  MatrixLayout.map_grouped_barchart('G', data, group_col='group', series_col='series', interactive=True)
  ```

### 4. **Pie Chart**
- **Tipo de selección**: Click en segmento (sector)
- **Implementación**: Click en cada segmento del pie envía evento con la categoría
- **Evento enviado**: `sendEvent(divId, 'select', {...})` con la categoría seleccionada
- **Requisito**: Debe tener `interactive=True` en el spec
- **Uso**:
  ```python
  MatrixLayout.map_pie('P', data, category_col='cat', interactive=True)
  ```

### ❌ Gráficas SIN selección implementada:
- **Histogram**: Solo visualización, no tiene selección
- **Boxplot**: Solo visualización, no tiene selección
- **Heatmap**: Solo visualización, no tiene selección
- **Correlation Heatmap**: Solo visualización, no tiene selección
- **Line Chart**: Solo visualización, no tiene selección
- **Violin Plot**: Solo visualización, no tiene selección
- **RadViz**: Solo visualización (aunque los anchors son arrastrables, no hay selección de puntos)
- **Confusion Matrix**: Solo visualización, no tiene selección

---

## 🔗 Gráficas con Vistas Enlazadas (Linked Views)

Las siguientes gráficas pueden ser **vistas dependientes** que se actualizan automáticamente cuando se seleccionan datos en un **Scatter Plot** (vista principal):

### ✅ Todas estas gráficas pueden ser enlazadas:

1. **Bar Chart** (`add_barchart`)
   - Se actualiza con los datos seleccionados del scatter plot
   - Agrupa y cuenta por categoría de los datos seleccionados
   ```python
   layout.add_barchart('B', category_col='dept', linked_to='S')
   ```

2. **Grouped Bar Chart** (`add_grouped_barchart`)
   - Se actualiza con los datos seleccionados
   - Muestra agrupaciones múltiples de los datos seleccionados
   ```python
   layout.add_grouped_barchart('G', main_col='group', sub_col='series', linked_to='S')
   ```

3. **Histogram** (`add_histogram`)
   - Se actualiza con los datos seleccionados
   - Muestra distribución de una columna numérica de los datos seleccionados
   ```python
   layout.add_histogram('H', column='age', linked_to='S')
   ```

4. **Boxplot** (`add_boxplot`)
   - Se actualiza con los datos seleccionados
   - Muestra estadísticas de cuartiles de los datos seleccionados
   ```python
   layout.add_boxplot('B', column='salary', category_col='dept', linked_to='S')
   ```

5. **Heatmap** (`add_heatmap`)
   - Se actualiza con los datos seleccionados
   - Muestra matriz de valores de los datos seleccionados
   ```python
   layout.add_heatmap('H', x_col='x', y_col='y', value_col='value', linked_to='S')
   ```

6. **Correlation Heatmap** (`add_correlation_heatmap`)
   - Se actualiza con los datos seleccionados
   - Muestra matriz de correlación de los datos seleccionados
   ```python
   layout.add_correlation_heatmap('C', linked_to='S')
   ```

7. **Line Chart** (`add_line`)
   - Se actualiza con los datos seleccionados
   - Muestra series temporales de los datos seleccionados
   ```python
   layout.add_line('L', x_col='date', y_col='value', series_col='series', linked_to='S')
   ```

8. **Pie Chart** (`add_pie`)
   - Se actualiza con los datos seleccionados
   - Muestra distribución proporcional de los datos seleccionados
   ```python
   layout.add_pie('P', category_col='category', value_col='value', linked_to='S')
   ```

9. **Violin Plot** (`add_violin`)
   - Se actualiza con los datos seleccionados
   - Muestra distribución de densidad de los datos seleccionados
   ```python
   layout.add_violin('V', value_col='value', category_col='category', linked_to='S')
   ```

10. **RadViz** (`add_radviz`)
    - Se actualiza con los datos seleccionados
    - Muestra proyección multidimensional de los datos seleccionados
    ```python
    layout.add_radviz('R', features=['f1', 'f2', 'f3'], class_col='class', linked_to='S')
    ```

11. **Confusion Matrix** (`add_confusion_matrix`)
    - Se actualiza con los datos seleccionados
    - Muestra matriz de confusión de los datos seleccionados
    ```python
    layout.add_confusion_matrix('C', y_true_col='true', y_pred_col='pred', linked_to='S')
    ```

### ⚠️ Vista Principal (Solo Scatter Plot)

**Solo el Scatter Plot puede ser la vista principal** que genera selecciones:
- Es la única gráfica que tiene implementado brush selection
- Todas las demás gráficas dependen de la selección del scatter plot
- Puedes tener múltiples scatter plots, cada uno controlando diferentes vistas enlazadas

```python
# Ejemplo completo
from BESTLIB.reactive import ReactiveMatrixLayout

layout = ReactiveMatrixLayout("SBP", selection_model=selection)

# Vista principal (genera selecciones)
layout.add_scatter('S', df, x_col='x', y_col='y', interactive=True)

# Vistas enlazadas (se actualizan automáticamente)
layout.add_barchart('B', category_col='cat', linked_to='S')
layout.add_pie('P', category_col='cat', linked_to='S')

layout.display()
```

---

## 📝 Resumen Ejecutivo

### Selección de Datos:
- ✅ **Scatter Plot**: Brush + Click
- ✅ **Bar Chart**: Click
- ✅ **Grouped Bar Chart**: Click
- ✅ **Pie Chart**: Click
- ❌ **Resto de gráficas**: Sin selección

### Vistas Enlazadas:
- ✅ **Todas las gráficas** pueden ser vistas enlazadas (dependientes)
- ⭐ **Solo Scatter Plot** puede ser vista principal (genera selecciones)
- 🔄 Las vistas enlazadas se actualizan automáticamente cuando cambia la selección en el scatter plot

### Acceso a Datos Seleccionados:
```python
from BESTLIB.reactive import SelectionModel

selection = SelectionModel()
layout = ReactiveMatrixLayout("SB", selection_model=selection)
layout.add_scatter('S', df, ...)
layout.display()

# Obtener datos seleccionados
selected_data = selection.get_items()  # Lista de diccionarios
selected_count = selection.get_count()  # Número de elementos
```

