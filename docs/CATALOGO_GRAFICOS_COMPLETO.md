# 📊 Catálogo Completo de Gráficos de BESTLIB

Este documento proporciona una descripción detallada de todos los gráficos disponibles en BESTLIB, incluyendo sus funcionalidades, capacidades de selección y soporte para vistas enlazadas.

---

## 📋 Índice

1. [Gráficos con Selección](#gráficos-con-selección)
2. [Gráficos sin Selección](#gráficos-sin-selección)
3. [Soporte para Linked Views](#soporte-para-linked-views)
4. [Resumen Ejecutivo](#resumen-ejecutivo)

---

## 🎯 Gráficos con Selección

Los siguientes gráficos permiten seleccionar datos mediante interacción del usuario:

### 1. **Scatter Plot** ⭐ (Vista Principal)

**Tipo de gráfico:** `scatter`  
**Clase:** `ScatterChart`

**Descripción:**
Gráfico de dispersión que muestra la relación entre dos variables numéricas. Cada punto representa una observación en el dataset.

**Parámetros principales:**
- `x_col`: Columna para eje X (requerido)
- `y_col`: Columna para eje Y (requerido)
- `category_col`: Columna de categorías (opcional, para colorear puntos)
- `size_col`: Columna para tamaño de puntos (opcional)
- `color_col`: Columna para color de puntos (opcional)
- `interactive`: Habilita selección (default: True)
- `tooltip`: Habilita/deshabilita tooltip de hover (default: True)

**Selección e interactividad de hover:**
- ✅ **SÍ SOPORTA SELECCIÓN**
- **Tipo de selección:**
  - **Brush Selection**: Arrastrar un rectángulo para seleccionar múltiples puntos
  - **Click Individual**: Click en puntos individuales para seleccionar/deseleccionar
  - **Multi-selección**: Mantener Ctrl/Cmd mientras haces click para agregar a la selección
- **Implementación:** Usa `d3.brush()` para selección rectangular y eventos de click
- **Hover/tooltip:** Al pasar el ratón por encima de un punto se muestra un tooltip con (x, y, categoría) y el punto se resalta visualmente (tamaño/color/opacidad).
- **Evento enviado:** `sendEvent(divId, 'select', {items: [...], __scatter_letter__: 'S'})`
- **Uso:**
  ```python
  layout.add_scatter('S', df, x_col='edad', y_col='salario', 
                     category_col='dept', interactive=True)
  ```

**Linked Views:**
- ✅ **Puede ser vista principal** (genera selecciones)
- ✅ **Puede ser vista enlazada** (se actualiza con selecciones de otra vista)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear datos de ejemplo
df = pd.DataFrame({
    'edad': [25, 30, 35, 40, 45, 50],
    'salario': [50000, 60000, 70000, 80000, 90000, 100000],
    'dept': ['IT', 'HR', 'IT', 'Finance', 'HR', 'IT']
})

# Crear modelo de selección
selection = SelectionModel()

# Crear layout
layout = ReactiveMatrixLayout("S", selection_model=selection)

# Agregar scatter plot
layout.add_scatter(
    'S',
    df,
    x_col='edad',
    y_col='salario',
    category_col='dept',
    interactive=True,
    colorMap={
        'IT': '#e74c3c',
        'HR': '#3498db',
        'Finance': '#2ecc71'
    },
    pointRadius=5,
    xLabel='Edad',
    yLabel='Salario'
)

layout.display()

# Acceder a datos seleccionados
selected = selection.get_items()
print(f"Elementos seleccionados: {len(selected)}")
```

---

### 2. **Bar Chart**

**Tipo de gráfico:** `bar`  
**Clase:** `BarChart`

**Descripción:**
Gráfico de barras verticales que muestra valores por categoría. Útil para comparar cantidades entre diferentes categorías.

**Parámetros principales:**
- `category_col`: Columna de categorías (requerido)
- `value_col`: Columna de valores (opcional, si no se especifica cuenta ocurrencias)
- `color`: Color único para todas las barras (opcional)
- `colorMap`: Diccionario {categoría: color} para colorear por categoría (opcional)
- `interactive`: Habilita selección (opcional)

**Selección:**
- ✅ **SÍ SOPORTA SELECCIÓN**
- **Tipo de selección:**
  - **Click en barra**: Click en una barra individual para seleccionarla
  - **Evento enviado:** `sendEvent(divId, 'select', {items: [...], __view_letter__: 'B'})`
- **Requisito:** Debe tener `interactive=True` en el spec
- **Uso:**
  ```python
  layout.add_barchart('B', category_col='dept', interactive=True, 
                      selection_var='selected_bars')
  ```

**Linked Views:**
- ✅ **Puede ser vista principal** (si `interactive=True` y `linked_to=None`)
- ✅ **Puede ser vista enlazada** (si `linked_to='S'` se actualiza con selecciones del scatter)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear datos de ejemplo
df = pd.DataFrame({
    'dept': ['IT', 'HR', 'Finance', 'IT', 'HR', 'Sales'],
    'ventas': [100000, 80000, 120000, 95000, 75000, 110000]
})

# Crear layout y establecer datos
layout = ReactiveMatrixLayout("B", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero

# Bar chart como vista principal (con selección)
layout.add_barchart(
    'B',
    category_col='dept',
    value_col='ventas',
    interactive=True,
    selection_var='selected_bars',
    colorMap={
        'IT': '#e74c3c',
        'HR': '#3498db',
        'Finance': '#2ecc71',
        'Sales': '#f39c12'
    },
    xLabel='Departamento',
    yLabel='Ventas'
)

layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Bar chart enlazado a scatter plot
layout = ReactiveMatrixLayout("SB", selection_model=SelectionModel())
layout.set_data(df)

# Vista principal
layout.add_scatter('S', x_col='edad', y_col='salario', 
                   category_col='dept', interactive=True)

# Vista enlazada
layout.add_barchart('B', category_col='dept', linked_to='S')

layout.display()
```

---

### 3. **Grouped Bar Chart**

**Tipo de gráfico:** `grouped_bar`  
**Clase:** `GroupedBarChart`

**Descripción:**
Gráfico de barras agrupadas que muestra múltiples series de datos agrupadas por categoría principal. Útil para comparar subcategorías dentro de categorías principales.

**Parámetros principales:**
- `main_col`: Columna de categoría principal (requerido)
- `sub_col`: Columna de subcategoría/serie (requerido)
- `value_col`: Columna de valores (opcional)
- `interactive`: Habilita selección (opcional)

**Selección:**
- ✅ **SÍ SOPORTA SELECCIÓN**
- **Tipo de selección:**
  - **Click en barra del grupo**: Click en una barra individual dentro de un grupo
  - **Evento enviado:** `sendEvent(divId, 'select', {items: [...], __view_letter__: 'G'})`
- **Requisito:** Debe tener `interactive=True` en el spec
- **Uso:**
  ```python
  layout.add_grouped_barchart('G', main_col='group', sub_col='series', 
                               interactive=True, selection_var='selected_grouped')
  ```

**Linked Views:**
- ✅ **Puede ser vista principal** (si `interactive=True` y `linked_to=None`)
- ✅ **Puede ser vista enlazada** (si `linked_to='S'` se actualiza con selecciones)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear datos de ejemplo
df = pd.DataFrame({
    'region': ['Norte', 'Norte', 'Sur', 'Sur', 'Este', 'Este'],
    'producto': ['A', 'B', 'A', 'B', 'A', 'B'],
    'ventas': [100, 150, 120, 180, 90, 130]
})

# Crear layout y establecer datos
layout = ReactiveMatrixLayout("G", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero

# Grouped bar chart como vista principal
layout.add_grouped_barchart(
    'G',
    main_col='region',
    sub_col='producto',
    value_col='ventas',
    interactive=True,
    selection_var='selected_grouped',
    xLabel='Región',
    yLabel='Ventas'
)

layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Grouped bar chart enlazado
layout = ReactiveMatrixLayout("SG", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='ventas', y_col='region', 
                   category_col='producto', interactive=True)
layout.add_grouped_barchart('G', main_col='region', sub_col='producto', 
                            value_col='ventas', linked_to='S')

layout.display()
```

---

### 4. **Pie Chart**

**Tipo de gráfico:** `pie`  
**Clase:** `PieChart`

**Descripción:**
Gráfico circular que muestra la proporción de cada categoría respecto al total. Útil para visualizar distribuciones porcentuales.

**Parámetros principales:**
- `category_col`: Columna de categorías (requerido)
- `value_col`: Columna de valores (opcional, si no se especifica cuenta ocurrencias)
- `interactive`: Habilita selección (opcional)

**Selección:**
- ✅ **SÍ SOPORTA SELECCIÓN**
- **Tipo de selección:**
  - **Click en segmento**: Click en un sector del pie para seleccionarlo
  - **Evento enviado:** `sendEvent(divId, 'select', {items: [...], __view_letter__: 'P'})`
- **Requisito:** Debe tener `interactive=True` en el spec
- **Uso:**
  ```python
  layout.add_pie('P', category_col='species', interactive=True, 
                 selection_var='selected_pie')
  ```

**Linked Views:**
- ✅ **Puede ser vista principal** (si `interactive=True` y `linked_to=None`)
- ✅ **Puede ser vista enlazada** (si `linked_to='S'` se actualiza con selecciones)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear datos de ejemplo
df = pd.DataFrame({
    'species': ['setosa', 'versicolor', 'virginica', 'setosa', 'versicolor'],
    'count': [50, 50, 50, 30, 40]
})

# Crear layout y establecer datos
layout = ReactiveMatrixLayout("P", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero

# Pie chart como vista principal
layout.add_pie(
    'P',
    category_col='species',
    value_col='count',
    interactive=True,
    selection_var='selected_pie',
    xLabel='Especies',
    yLabel='Cantidad'
)

layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Pie chart enlazado
layout = ReactiveMatrixLayout("SP", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='sepal_length', y_col='sepal_width', 
                   category_col='species', interactive=True)
layout.add_pie('P', category_col='species', linked_to='S')

layout.display()
```

---

## 📊 Gráficos sin Selección

Los siguientes gráficos son de solo visualización y no permiten selección de datos:

### 5. **Histogram**

**Tipo de gráfico:** `histogram`  
**Clase:** `HistogramChart`

**Descripción:**
Gráfico que muestra la distribución de una variable numérica dividida en intervalos (bins). Cada barra representa la frecuencia de valores en ese intervalo.

**Parámetros principales:**
- `value_col`: Columna numérica (requerido)
- `bins`: Número de intervalos (default: 10)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear datos de ejemplo
df = pd.DataFrame({
    'age': [25, 30, 35, 40, 45, 50, 55, 30, 35, 40, 45, 50]
})

# Crear layout y establecer datos
layout = ReactiveMatrixLayout("H", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero

# Histograma independiente
layout.add_histogram(
    'H',
    column='age',
    bins=10,
    xLabel='Edad',
    yLabel='Frecuencia'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Histograma enlazado a scatter plot
layout = ReactiveMatrixLayout("SH", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='age', y_col='salary', interactive=True)
layout.add_histogram('H', column='age', bins=15, linked_to='S')

layout.display()
```

---

### 6. **Boxplot**

**Tipo de gráfico:** `boxplot`  
**Clase:** `BoxplotChart`

**Descripción:**
Gráfico que muestra estadísticas descriptivas (cuartiles, mediana, outliers) de una variable numérica, opcionalmente agrupada por categorías.

**Parámetros principales:**
- `value_col`: Columna numérica (requerido)
- `category_col`: Columna de categorías (opcional, para múltiples boxplots)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear datos de ejemplo
df = pd.DataFrame({
    'salary': [50000, 60000, 70000, 80000, 90000, 55000, 65000, 75000],
    'dept': ['IT', 'HR', 'IT', 'Finance', 'HR', 'IT', 'Finance', 'HR']
})

# Crear layout y establecer datos
layout = ReactiveMatrixLayout("B", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero

# Boxplot independiente
layout.add_boxplot(
    'B',
    column='salary',
    category_col='dept',
    xLabel='Departamento',
    yLabel='Salario'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Boxplot enlazado
layout = ReactiveMatrixLayout("SB", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='age', y_col='salary', 
                   category_col='dept', interactive=True)
layout.add_boxplot('B', column='salary', category_col='dept', linked_to='S')

layout.display()
```

---

### 7. **Heatmap**

**Tipo de gráfico:** `heatmap`  
**Clase:** `HeatmapChart`

**Descripción:**
Matriz de colores donde cada celda representa un valor. Los colores indican la magnitud del valor. Útil para visualizar matrices de datos o correlaciones.

**Parámetros principales:**
- `x_col`: Columna para eje X (opcional)
- `y_col`: Columna para eje Y (opcional)
- `value_col`: Columna de valores (opcional)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo en formato "long" (cada fila es una celda del heatmap)
np.random.seed(42)
data = []
for col in ['A', 'B', 'C', 'D']:
    for row in ['X', 'Y', 'Z']:
        data.append({
            'col': col,      # Columna del heatmap (eje X)
            'row': row,      # Fila del heatmap (eje Y)
            'val': np.random.rand()  # Valor numérico
        })

df = pd.DataFrame(data)

# Heatmap independiente
layout = ReactiveMatrixLayout("H", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_heatmap(
    'H',
    x_col='col',      # Columna para eje X del heatmap
    y_col='row',      # Columna para eje Y del heatmap
    value_col='val',  # Columna con los valores numéricos
    xLabel='Columna',
    yLabel='Fila'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Heatmap enlazado
layout = ReactiveMatrixLayout("SH", selection_model=SelectionModel())
layout.set_data(df)

# Vista principal (scatter plot con datos relacionados)
layout.add_scatter('S', x_col='col', y_col='row', interactive=True)
# Vista enlazada (heatmap se actualiza con selección)
layout.add_heatmap('H', x_col='col', y_col='row', value_col='val', linked_to='S')

layout.display()
```

---

### 8. **Line Chart**

**Tipo de gráfico:** `line`  
**Clase:** `LineChart`

**Descripción:**
Gráfico de líneas que muestra la evolución de una variable a lo largo de otra (típicamente tiempo). Puede mostrar múltiples series.

**Parámetros principales:**
- `x_col`: Columna para eje X (requerido)
- `y_col`: Columna para eje Y (requerido)
- `series_col`: Columna para agrupar en series (opcional)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear datos de ejemplo
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=10, freq='D'),
    'value': [10, 15, 12, 18, 20, 16, 22, 19, 25, 23],
    'series': ['A', 'A', 'B', 'B', 'A', 'B', 'A', 'B', 'A', 'B']
})

# Line chart independiente
layout = ReactiveMatrixLayout("L", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_line(
    'L',
    x_col='date',
    y_col='value',
    series_col='series',
    xLabel='Fecha',
    yLabel='Valor'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Line chart enlazado
layout = ReactiveMatrixLayout("SL", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='date', y_col='value', 
                   category_col='series', interactive=True)
layout.add_line('L', x_col='date', y_col='value', series_col='series', linked_to='S')

layout.display()
```

---

### 9. **Line Plot** (Versión mejorada)

**Tipo de gráfico:** `line_plot`  
**Clase:** `LinePlotChart`

**Descripción:**
Versión mejorada del line chart con más opciones de personalización (marcadores, múltiples series, etc.).

**Parámetros principales:**
- `x_col`: Columna para eje X (requerido)
- `y_col`: Columna para eje Y (requerido)
- `series_col`: Columna para agrupar en series (opcional)
- `markers`: Mostrar marcadores en puntos (opcional)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo (usar valores numéricos para el eje X)
df = pd.DataFrame({
    'time': np.arange(1, 21),  # Valores numéricos: 1, 2, 3, ..., 20
    'value': [10, 15, 12, 18, 20, 16, 22, 19, 25, 23, 17, 21, 24, 19, 16, 20, 22, 18, 21, 23],
    'series': ['A'] * 10 + ['B'] * 10
})

# Line plot independiente
layout = ReactiveMatrixLayout("LP", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_line_plot(
    'LP',
    x_col='time',
    y_col='value',
    series_col='series',
    markers=True,
    xLabel='Tiempo',
    yLabel='Valor'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Line plot enlazado
layout = ReactiveMatrixLayout("SLP", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='time', y_col='value', 
                   category_col='series', interactive=True)
layout.add_line_plot('LP', x_col='time', y_col='value', 
                     series_col='series', linked_to='S')

layout.display()
```

---

### 10. **Violin Plot**

**Tipo de gráfico:** `violin`  
**Clase:** `ViolinChart`

**Descripción:**
Gráfico que combina un boxplot con un gráfico de densidad (KDE). Muestra la distribución completa de los datos, no solo estadísticas resumidas.

**Parámetros principales:**
- `value_col`: Columna numérica (requerido)
- `category_col`: Columna de categorías (opcional)
- `bins`: Número de puntos para el perfil de densidad (default: 50)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'value': np.concatenate([
        np.random.normal(5, 1, 50),
        np.random.normal(7, 1.5, 50),
        np.random.normal(9, 1, 50)
    ]),
    'category': ['A'] * 50 + ['B'] * 50 + ['C'] * 50
})

# Violin plot independiente
layout = ReactiveMatrixLayout("V", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_violin(
    'V',
    value_col='value',
    category_col='category',
    bins=50,
    xLabel='Categoría',
    yLabel='Valor'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Violin plot enlazado
layout = ReactiveMatrixLayout("SV", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='value', y_col='category', 
                   category_col='category', interactive=True)
layout.add_violin('V', value_col='value', category_col='category', linked_to='S')

layout.display()
```

---

### 11. **RadViz**

**Tipo de gráfico:** `radviz`  
**Clase:** `RadvizChart`

**Descripción:**
Visualización multidimensional donde cada dimensión se representa como un "anchor" en un círculo. Los puntos se posicionan según sus valores en cada dimensión.

**Parámetros principales:**
- `features`: Lista de columnas numéricas (requerido)
- `class_col`: Columna de categorías/clases (opcional)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Nota: Los anchors son arrastrables, pero no hay selección de puntos implementada

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'f1': np.random.rand(100),
    'f2': np.random.rand(100),
    'f3': np.random.rand(100),
    'class': np.random.choice(['A', 'B', 'C'], 100)
})

# RadViz independiente
layout = ReactiveMatrixLayout("R", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_radviz(
    'R',
    features=['f1', 'f2', 'f3'],
    class_col='class',
    xLabel='RadViz'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# RadViz enlazado
layout = ReactiveMatrixLayout("SR", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='f1', y_col='f2', 
                   category_col='class', interactive=True)
layout.add_radviz('R', features=['f1', 'f2', 'f3'], class_col='class', linked_to='S')

layout.display()
```

---

### 12. **Star Coordinates**

**Tipo de gráfico:** `star_coordinates`  
**Clase:** `StarCoordinatesChart`

**Descripción:**
Similar a RadViz, visualización multidimensional donde cada dimensión se representa como un eje desde el centro. Los puntos se posicionan según sus valores.

**Parámetros principales:**
- `features`: Lista de columnas numéricas (requerido)
- `class_col`: Columna de categorías/clases (opcional)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'f1': np.random.rand(100),
    'f2': np.random.rand(100),
    'f3': np.random.rand(100),
    'class': np.random.choice(['A', 'B', 'C'], 100)
})

# Star Coordinates independiente
layout = ReactiveMatrixLayout("SC", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_star_coordinates(
    'SC',
    features=['f1', 'f2', 'f3'],
    class_col='class',
    xLabel='Star Coordinates'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Star Coordinates enlazado
layout = ReactiveMatrixLayout("SSC", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='f1', y_col='f2', 
                   category_col='class', interactive=True)
layout.add_star_coordinates('SC', features=['f1', 'f2', 'f3'], 
                           class_col='class', linked_to='S')

layout.display()
```

---

### 13. **Parallel Coordinates**

**Tipo de gráfico:** `parallel_coordinates`  
**Clase:** `ParallelCoordinatesChart`

**Descripción:**
Visualización multidimensional donde cada dimensión se representa como un eje vertical paralelo. Cada observación se dibuja como una línea que conecta sus valores en cada dimensión.

**Parámetros principales:**
- `dimensions`: Lista de columnas numéricas (requerido)
- `category_col`: Columna de categorías (opcional, para colorear líneas)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'f1': np.random.rand(100),
    'f2': np.random.rand(100),
    'f3': np.random.rand(100),
    'class': np.random.choice(['A', 'B', 'C'], 100)
})

# Parallel Coordinates independiente
layout = ReactiveMatrixLayout("PC", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_parallel_coordinates(
    'PC',
    dimensions=['f1', 'f2', 'f3'],
    category_col='class',
    xLabel='Parallel Coordinates'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Parallel Coordinates enlazado
layout = ReactiveMatrixLayout("SPC", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='f1', y_col='f2', 
                   category_col='class', interactive=True)
layout.add_parallel_coordinates('PC', dimensions=['f1', 'f2', 'f3'], 
                                category_col='class', linked_to='S')

layout.display()
```

---

### 14. **Horizontal Bar Chart**

**Tipo de gráfico:** `horizontal_bar`  
**Clase:** `HorizontalBarChart`

**Descripción:**
Gráfico de barras horizontales. Similar al bar chart pero con barras orientadas horizontalmente. Útil cuando hay muchas categorías o nombres largos.

**Parámetros principales:**
- `category_col`: Columna de categorías (requerido)
- `value_col`: Columna de valores (opcional)
- `color`: Color único o `colorMap` para colorear por categoría

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN** (no implementado en código JavaScript)
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear datos de ejemplo
df = pd.DataFrame({
    'category': ['A', 'B', 'C', 'A', 'B', 'C', 'A', 'B'],
    'value': [10, 20, 15, 12, 25, 18, 8, 22]
})

# Horizontal bar chart independiente
layout = ReactiveMatrixLayout("HB", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_horizontal_bar(
    'HB',
    category_col='category',
    value_col='value',
    xLabel='Valor',
    yLabel='Categoría'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Horizontal bar chart enlazado
layout = ReactiveMatrixLayout("SHB", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='value', y_col='category', 
                   category_col='category', interactive=True)
layout.add_horizontal_bar('HB', category_col='category', 
                          value_col='value', linked_to='S')

layout.display()
```

---

### 15. **KDE (Kernel Density Estimation)**

**Tipo de gráfico:** `kde`  
**Clase:** `KdeChart`

**Descripción:**
Gráfico de estimación de densidad de kernel. Muestra una curva suave que aproxima la distribución de probabilidad de una variable numérica.

**Parámetros principales:**
- `column`: Columna numérica (requerido)
- `bandwidth`: Ancho de banda para KDE (opcional, auto si no se especifica)
- `fill`: Rellenar área bajo la curva (opcional, default: True)
- `opacity`: Opacidad del relleno (opcional, default: 0.3)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'age': np.random.normal(35, 10, 100)
})

# KDE independiente
layout = ReactiveMatrixLayout("K", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_kde(
    'K',
    column='age',
    bandwidth=0.5,
    fill=True,
    opacity=0.3,
    xLabel='Edad',
    yLabel='Densidad'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# KDE enlazado
layout = ReactiveMatrixLayout("SK", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='age', y_col='salary', interactive=True)
layout.add_kde('K', column='age', bandwidth=0.5, linked_to='S')

layout.display()
```

---

### 16. **Distplot**

**Tipo de gráfico:** `distplot`  
**Clase:** `DistplotChart`

**Descripción:**
Gráfico combinado que muestra un histograma junto con una curva KDE. Útil para visualizar tanto la distribución discreta (histograma) como la continua (KDE).

**Parámetros principales:**
- `column`: Columna numérica (requerido)
- `bins`: Número de bins para histograma (default: 30)
- `kde`: Incluir curva KDE (default: True)
- `rug`: Incluir rug plot (marcadores en el eje) (default: False)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'age': np.random.normal(35, 10, 100)
})

# Distplot independiente
layout = ReactiveMatrixLayout("D", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_distplot(
    'D',
    column='age',
    bins=30,
    kde=True,
    rug=False,
    xLabel='Edad',
    yLabel='Densidad'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Distplot enlazado
layout = ReactiveMatrixLayout("SD", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='age', y_col='salary', interactive=True)
layout.add_distplot('D', column='age', bins=30, kde=True, rug=False, linked_to='S')

layout.display()
```

---

### 17. **Rug Plot**

**Tipo de gráfico:** `rug`  
**Clase:** `RugChart`

**Descripción:**
Marcadores pequeños en el eje que muestran la posición de cada observación. Típicamente se usa junto con histogramas o KDE para mostrar la distribución de datos.

**Parámetros principales:**
- `column`: Columna numérica (requerido)
- `axis`: Eje donde mostrar rug ('x' o 'y', default: 'x')
- `color`: Color de los marcadores (opcional)
- `size`: Tamaño de los marcadores (opcional, default: 2)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'age': np.random.normal(35, 10, 50)
})

# Rug plot independiente
layout = ReactiveMatrixLayout("R", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_rug(
    'R',
    column='age',
    axis='x',
    color='#4a90e2',
    size=2,
    opacity=0.6,
    xLabel='Edad'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Rug plot enlazado
layout = ReactiveMatrixLayout("SR", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='age', y_col='salary', interactive=True)
layout.add_rug('R', column='age', axis='x', linked_to='S')

layout.display()
```

---

### 18. **Q-Q Plot (Quantile-Quantile)**

**Tipo de gráfico:** `qqplot`  
**Clase:** `QqplotChart`

**Descripción:**
Gráfico que compara los quantiles de los datos observados con los quantiles de una distribución teórica. Útil para verificar si los datos siguen una distribución específica (normal, uniforme, etc.).

**Parámetros principales:**
- `column`: Columna numérica (requerido)
- `dist`: Distribución teórica ('norm', 'uniform', etc., default: 'norm')
- `showLine`: Mostrar línea de referencia (default: True)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'age': np.random.normal(35, 10, 100)
})

# Q-Q plot independiente
layout = ReactiveMatrixLayout("Q", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_qqplot(
    'Q',
    column='age',
    dist='norm',
    showLine=True,
    xLabel='Quantiles Teóricos (Normal)',
    yLabel='Quantiles Observados'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Q-Q plot enlazado
layout = ReactiveMatrixLayout("SQ", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='age', y_col='salary', interactive=True)
layout.add_qqplot('Q', column='age', dist='norm', linked_to='S')

layout.display()
```

---

### 19. **ECDF (Empirical Cumulative Distribution Function)**

**Tipo de gráfico:** `ecdf`  
**Clase:** `EcdfChart`

**Descripción:**
Gráfico de función de distribución acumulativa empírica. Muestra la proporción de datos menores o iguales a cada valor. Útil para comparar distribuciones.

**Parámetros principales:**
- `column`: Columna numérica (requerido)
- `step`: Usar gráfico escalonado (default: True)
- `color`: Color de la línea (opcional)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'age': np.random.normal(35, 10, 100)
})

# ECDF independiente
layout = ReactiveMatrixLayout("E", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_ecdf(
    'E',
    column='age',
    step=True,
    color='#4a90e2',
    strokeWidth=2,
    xLabel='Edad',
    yLabel='Probabilidad Acumulativa'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# ECDF enlazado
layout = ReactiveMatrixLayout("SE", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='age', y_col='salary', interactive=True)
layout.add_ecdf('E', column='age', linked_to='S')

layout.display()
```

---

### 20. **Ridgeline Plot (Joy Plot)**

**Tipo de gráfico:** `ridgeline`  
**Clase:** `RidgelineChart`

**Descripción:**
Gráfico de densidades apiladas (KDE) por categoría. Cada categoría tiene su propia curva de densidad apilada verticalmente. Útil para comparar distribuciones entre categorías.

**Parámetros principales:**
- `column`: Columna numérica (requerido)
- `category_col`: Columna de categorías (requerido)
- `bandwidth`: Ancho de banda para KDE (opcional)
- `overlap`: Solapamiento entre curvas (default: 0.5)
- `opacity`: Opacidad de las curvas (default: 0.7)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'age': np.concatenate([
        np.random.normal(30, 5, 50),
        np.random.normal(40, 5, 50),
        np.random.normal(50, 5, 50)
    ]),
    'species': ['A'] * 50 + ['B'] * 50 + ['C'] * 50
})

# Ridgeline plot independiente
layout = ReactiveMatrixLayout("RL", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_ridgeline(
    'RL',
    column='age',
    category_col='species',
    bandwidth=None,
    overlap=0.5,
    opacity=0.7,
    xLabel='Edad',
    yLabel='Densidad'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Ridgeline plot enlazado
layout = ReactiveMatrixLayout("SRL", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='age', y_col='species', 
                   category_col='species', interactive=True)
layout.add_ridgeline('RL', column='age', category_col='species', linked_to='S')

layout.display()
```

---

### 21. **Ribbon Plot**

**Tipo de gráfico:** `ribbon`  
**Clase:** `RibbonChart`

**Descripción:**
Gráfico de área entre dos líneas con gradiente. Muestra el área entre dos series de datos, típicamente usado para mostrar rangos o intervalos de confianza.

**Parámetros principales:**
- `x_col`: Columna para eje X (requerido)
- `y1_col`: Columna para línea superior (requerido)
- `y2_col`: Columna para línea inferior (requerido)
- `color1`: Color de la línea superior (opcional)
- `color2`: Color de la línea inferior (opcional)
- `gradient`: Usar gradiente en el área (opcional)
- `showLines`: Mostrar las líneas además del área (default: True)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
dates = pd.date_range('2024-01-01', periods=20, freq='D')
df = pd.DataFrame({
    'date': dates,
    'max': np.random.uniform(20, 30, 20),
    'min': np.random.uniform(10, 20, 20)
})

# Ribbon plot independiente
layout = ReactiveMatrixLayout("RB", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_ribbon(
    'RB',
    x_col='date',
    y1_col='max',
    y2_col='min',
    color1='#4a90e2',
    color2='#e24a4a',
    gradient=True,
    opacity=0.4,
    showLines=True,
    xLabel='Fecha',
    yLabel='Rango'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Ribbon plot enlazado
layout = ReactiveMatrixLayout("SRB", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='date', y_col='max', interactive=True)
layout.add_ribbon('RB', x_col='date', y1_col='max', y2_col='min', linked_to='S')

layout.display()
```

---

### 22. **Histogram 2D**

**Tipo de gráfico:** `hist2d`  
**Clase:** `Hist2dChart`

**Descripción:**
Histograma bidimensional (heatmap de densidad). Muestra la distribución conjunta de dos variables numéricas usando colores para representar la densidad.

**Parámetros principales:**
- `x_col`: Columna para eje X (requerido)
- `y_col`: Columna para eje Y (requerido)
- `bins`: Número de bins (puede ser int o [int, int] para X e Y, default: 20)
- `colorScale`: Escala de colores (default: 'Blues')

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'x': np.random.normal(0, 1, 1000),
    'y': np.random.normal(0, 1, 1000)
})

# Histogram 2D independiente
layout = ReactiveMatrixLayout("H2", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_hist2d(
    'H2',
    x_col='x',
    y_col='y',
    bins=20,
    colorScale='Blues',
    xLabel='Eje X',
    yLabel='Eje Y'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Histogram 2D enlazado
layout = ReactiveMatrixLayout("SH2", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='x', y_col='y', interactive=True)
layout.add_hist2d('H2', x_col='x', y_col='y', bins=20, linked_to='S')

layout.display()
```

---

### 23. **Hexbin**

**Tipo de gráfico:** `hexbin`  
**Clase:** `HexbinChart`

**Descripción:**
Visualización de densidad usando hexágonos. Similar a hist2d pero usa hexágonos en lugar de rectángulos, lo que puede ser más estéticamente agradable.

**Parámetros principales:**
- `x_col`: Columna para eje X (requerido)
- `y_col`: Columna para eje Y (requerido)
- `bins`: Número de bins hexagonales (default: 20)
- `colorScale`: Escala de colores (opcional)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'x': np.random.normal(0, 1, 1000),
    'y': np.random.normal(0, 1, 1000)
})

# Hexbin independiente
layout = ReactiveMatrixLayout("HX", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_hexbin(
    'HX',
    x_col='x',
    y_col='y',
    bins=20,
    colorScale='Viridis',
    xLabel='Eje X',
    yLabel='Eje Y'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Hexbin enlazado
layout = ReactiveMatrixLayout("SHX", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='x', y_col='y', interactive=True)
layout.add_hexbin('HX', x_col='x', y_col='y', bins=20, linked_to='S')

layout.display()
```

---

### 24. **Polar Plot**

**Tipo de gráfico:** `polar`  
**Clase:** `PolarChart`

**Descripción:**
Gráfico en coordenadas polares. Los datos se representan usando ángulo y radio en lugar de coordenadas cartesianas.

**Parámetros principales:**
- `angle_col`: Columna para ángulo (en radianes o grados, requerido)
- `radius_col`: Columna para radio (requerido)
- `angle_unit`: Unidad del ángulo ('rad' o 'deg', default: 'rad')
- `showGrid`: Mostrar cuadrícula polar (default: True)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
angles = np.linspace(0, 2*np.pi, 20)
df = pd.DataFrame({
    'angle': angles,
    'radius': np.random.uniform(1, 5, 20)
})

# Polar plot independiente
layout = ReactiveMatrixLayout("P", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_polar(
    'P',
    angle_col='angle',
    radius_col='radius',
    angle_unit='rad',
    showGrid=True,
    color='#4a90e2',
    xLabel='Polar Plot'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Polar plot enlazado
layout = ReactiveMatrixLayout("SP", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='angle', y_col='radius', interactive=True)
layout.add_polar('P', angle_col='angle', radius_col='radius', linked_to='S')

layout.display()
```

---

### 25. **Funnel Plot**

**Tipo de gráfico:** `funnel`  
**Clase:** `FunnelChart`

**Descripción:**
Gráfico de embudo que muestra valores por etapas. Típicamente usado para visualizar procesos con etapas donde el valor disminuye en cada etapa.

**Parámetros principales:**
- `stage_col`: Columna de etapas (requerido)
- `value_col`: Columna de valores (requerido)
- `orientation`: Orientación ('vertical' o 'horizontal', default: 'vertical')
- `color`: Color del embudo (opcional)
- `opacity`: Opacidad (default: 0.7)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear datos de ejemplo
df = pd.DataFrame({
    'stage': ['Visitas', 'Interesados', 'Contactos', 'Oportunidades', 'Ventas'],
    'value': [1000, 500, 200, 100, 50]
})

# Funnel plot independiente
layout = ReactiveMatrixLayout("F", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_funnel(
    'F',
    stage_col='stage',
    value_col='value',
    orientation='vertical',
    color='#4a90e2',
    opacity=0.7,
    xLabel='Etapa',
    yLabel='Valor'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Funnel plot enlazado
layout = ReactiveMatrixLayout("SF", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='stage', y_col='value', interactive=True)
layout.add_funnel('F', stage_col='stage', value_col='value', linked_to='S')

layout.display()
```

---

### 26. **Errorbars**

**Tipo de gráfico:** `errorbars`  
**Clase:** `ErrorbarsChart`

**Descripción:**
Gráfico de puntos con barras de error. Muestra valores con sus intervalos de incertidumbre (errores estándar, desviaciones estándar, etc.).

**Parámetros principales:**
- `x_col`: Columna para eje X (requerido)
- `y_col`: Columna para eje Y (requerido)
- `yerr`: Columna para error en Y (opcional)
- `xerr`: Columna para error en X (opcional)
- `capSize`: Tamaño de las tapas de las barras de error (opcional)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo con errores
np.random.seed(42)
x = np.linspace(0, 10, 20)
df = pd.DataFrame({
    'x': x,
    'y': np.sin(x) + 2,
    'yerr': np.random.uniform(0.1, 0.3, 20)  # Errores en Y
})

# Errorbars independiente
layout = ReactiveMatrixLayout("EB", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_errorbars(
    'EB',
    x_col='x',
    y_col='y',
    yerr='yerr',
    capSize=5,
    color='#4a90e2',
    xLabel='Eje X',
    yLabel='Eje Y'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Errorbars enlazado
layout = ReactiveMatrixLayout("SEB", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='x', y_col='y', interactive=True)
layout.add_errorbars('EB', x_col='x', y_col='y', yerr='yerr', linked_to='S')

layout.display()
```

---

### 27. **Fill Between**

**Tipo de gráfico:** `fill_between`  
**Clase:** `FillBetweenChart`

**Descripción:**
Gráfico de área entre dos líneas. Similar a ribbon pero más simple, muestra el área entre dos series sin gradiente.

**Parámetros principales:**
- `x_col`: Columna para eje X (requerido)
- `y1`: Columna para primera línea Y (requerido)
- `y2`: Columna para segunda línea Y (requerido)
- `color`: Color del área (opcional)
- `opacity`: Opacidad del área (default: 0.3)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo para Fill Between
x = np.linspace(0, 10, 20)
df = pd.DataFrame({
    'x': x,
    'y1': np.sin(x) + 2,  # Línea superior
    'y2': np.sin(x) - 2   # Línea inferior
})

# Fill Between independiente
layout = ReactiveMatrixLayout("FB", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_fill_between(
    'FB',
    x_col='x',
    y1='y1',
    y2='y2',
    color='#4a90e2',
    opacity=0.3,
    xLabel='Eje X',
    yLabel='Eje Y'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Fill Between enlazado
layout = ReactiveMatrixLayout("SFB", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='x', y_col='y1', interactive=True)
layout.add_fill_between('FB', x_col='x', y1='y1', y2='y2', linked_to='S')

layout.display()
```

---

### 28. **Step Plot**

**Tipo de gráfico:** `step_plot`  
**Clase:** `StepPlotChart`

**Descripción:**
Gráfico de líneas escalonadas. Muestra datos como una función escalonada en lugar de una línea continua. Útil para datos discretos o funciones de paso.

**Parámetros principales:**
- `x_col`: Columna para eje X (requerido)
- `y_col`: Columna para eje Y (requerido)
- `stepType`: Tipo de escalón ('step', 'stepBefore', 'stepAfter', default: 'step')
- `color`: Color de la línea (opcional)
- `strokeWidth`: Grosor de la línea (opcional)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
x = np.linspace(0, 10, 20)
df = pd.DataFrame({
    'x': x,
    'y': np.sin(x) + np.random.normal(0, 0.1, 20)
})

# Step plot independiente
layout = ReactiveMatrixLayout("SP", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_step(
    'SP',
    x_col='x',
    y_col='y',
    stepType='step',
    color='#4a90e2',
    strokeWidth=2,
    xLabel='Eje X',
    yLabel='Eje Y'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Step plot enlazado
layout = ReactiveMatrixLayout("SSP", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='x', y_col='y', interactive=True)
layout.add_step('SP', x_col='x', y_col='y', linked_to='S')

layout.display()
```

---

### 29. **Correlation Heatmap**

**Tipo de gráfico:** `correlation_heatmap`  
**Clase:** (Método especial en ReactiveMatrixLayout)

**Descripción:**
Matriz de correlación visualizada como heatmap. Muestra las correlaciones entre todas las columnas numéricas del dataset.

**Parámetros principales:**
- No requiere parámetros específicos (calcula correlación de todas las columnas numéricas)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo con múltiples columnas numéricas
np.random.seed(42)
df = pd.DataFrame({
    'col1': np.random.rand(100),
    'col2': np.random.rand(100),
    'col3': np.random.rand(100),
    'col4': np.random.rand(100)
})

# Correlation Heatmap independiente
layout = ReactiveMatrixLayout("C", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_correlation_heatmap(
    'C',
    xLabel='Correlation Heatmap'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Correlation Heatmap enlazado
layout = ReactiveMatrixLayout("SC", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='col1', y_col='col2', interactive=True)
layout.add_correlation_heatmap('C', linked_to='S')

layout.display()
```

---

### 30. **Confusion Matrix**

**Tipo de gráfico:** `confusion_matrix`  
**Clase:** (Método especial en ReactiveMatrixLayout)

**Descripción:**
Matriz de confusión para evaluación de modelos de clasificación. Muestra las predicciones correctas e incorrectas.

**Parámetros principales:**
- `y_true_col`: Columna con valores reales (requerido)
- `y_pred_col`: Columna con predicciones (requerido)
- `normalize`: Normalizar valores (default: True)

**Selección:**
- ❌ **NO SOPORTA SELECCIÓN**
- Solo visualización

**Linked Views:**
- ✅ **Puede ser vista enlazada** (se actualiza con datos seleccionados)

**Ejemplo de Código Python:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd
import numpy as np

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'true': np.random.choice(['A', 'B', 'C'], 100),
    'pred': np.random.choice(['A', 'B', 'C'], 100),
    'feature1': np.random.rand(100),
    'feature2': np.random.rand(100)
})

# Confusion Matrix independiente
layout = ReactiveMatrixLayout("CM", selection_model=SelectionModel())
layout.set_data(df)  # ⚠️ IMPORTANTE: Establecer datos primero
layout.add_confusion_matrix(
    'CM',
    y_true_col='true',
    y_pred_col='pred',
    normalize=True,
    xLabel='Confusion Matrix'
)
layout.display()
```

**Ejemplo como Vista Enlazada:**
```python
# Confusion Matrix enlazado
layout = ReactiveMatrixLayout("SCM", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='feature1', y_col='feature2', 
                   category_col='true', interactive=True)
layout.add_confusion_matrix('CM', y_true_col='true', y_pred_col='pred', linked_to='S')

layout.display()
```

---

## 🔗 Soporte para Linked Views

### Vista Principal

**Solo el Scatter Plot puede ser vista principal** que genera selecciones mediante brush o click. Todas las demás vistas pueden ser vistas enlazadas que se actualizan automáticamente cuando cambia la selección en la vista principal.

### Vistas Enlazadas

**TODOS los gráficos pueden ser vistas enlazadas**, es decir, pueden actualizarse automáticamente cuando se seleccionan datos en una vista principal (típicamente un Scatter Plot).

**Cómo funciona:**
1. Se crea una vista principal (Scatter Plot con `interactive=True`)
2. Se crean vistas enlazadas especificando `linked_to='S'` (donde 'S' es la letra de la vista principal)
3. Cuando el usuario selecciona datos en la vista principal, todas las vistas enlazadas se actualizan automáticamente con solo los datos seleccionados

**Ejemplo completo:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

# Crear modelo de selección
selection = SelectionModel()

# Crear layout reactivo
layout = ReactiveMatrixLayout("SBH", selection_model=selection)

# Vista principal (genera selecciones)
layout.add_scatter('S', df, x_col='edad', y_col='salario', 
                   category_col='dept', interactive=True)

# Vistas enlazadas (se actualizan automáticamente)
layout.add_barchart('B', category_col='dept', linked_to='S')
layout.add_histogram('H', column='edad', linked_to='S')

layout.display()

# Acceder a datos seleccionados
selected_data = selection.get_items()  # Lista de diccionarios
selected_count = selection.get_count()  # Número de elementos
```

**Gráficos que pueden ser vistas principales:**
- ✅ Scatter Plot (brush + click)
- ✅ Bar Chart (click, si `interactive=True` y `linked_to=None`)
- ✅ Grouped Bar Chart (click, si `interactive=True` y `linked_to=None`)
- ✅ Pie Chart (click, si `interactive=True` y `linked_to=None`)

**Gráficos que solo pueden ser vistas enlazadas:**
- Todos los demás gráficos (Histogram, Boxplot, Heatmap, Line Chart, Violin, etc.)

---

## 📝 Resumen Ejecutivo

### Tabla de Capacidades

| Gráfico | Selección | Linked Views (Principal) | Linked Views (Enlazada) |
|---------|-----------|-------------------------|-------------------------|
| **Scatter Plot** | ✅ Brush + Click | ✅ Sí | ✅ Sí |
| **Bar Chart** | ✅ Click | ✅ Sí (si interactive=True) | ✅ Sí |
| **Grouped Bar Chart** | ✅ Click | ✅ Sí (si interactive=True) | ✅ Sí |
| **Pie Chart** | ✅ Click | ✅ Sí (si interactive=True) | ✅ Sí |
| **Histogram** | ❌ No | ❌ No | ✅ Sí |
| **Boxplot** | ❌ No | ❌ No | ✅ Sí |
| **Heatmap** | ❌ No | ❌ No | ✅ Sí |
| **Line Chart** | ❌ No | ❌ No | ✅ Sí |
| **Line Plot** | ❌ No | ❌ No | ✅ Sí |
| **Violin Plot** | ❌ No | ❌ No | ✅ Sí |
| **RadViz** | ❌ No | ❌ No | ✅ Sí |
| **Star Coordinates** | ❌ No | ❌ No | ✅ Sí |
| **Parallel Coordinates** | ❌ No | ❌ No | ✅ Sí |
| **Horizontal Bar Chart** | ❌ No | ❌ No | ✅ Sí |
| **KDE** | ❌ No | ❌ No | ✅ Sí |
| **Distplot** | ❌ No | ❌ No | ✅ Sí |
| **Rug Plot** | ❌ No | ❌ No | ✅ Sí |
| **Q-Q Plot** | ❌ No | ❌ No | ✅ Sí |
| **ECDF** | ❌ No | ❌ No | ✅ Sí |
| **Ridgeline Plot** | ❌ No | ❌ No | ✅ Sí |
| **Ribbon Plot** | ❌ No | ❌ No | ✅ Sí |
| **Histogram 2D** | ❌ No | ❌ No | ✅ Sí |
| **Hexbin** | ❌ No | ❌ No | ✅ Sí |
| **Polar Plot** | ❌ No | ❌ No | ✅ Sí |
| **Funnel Plot** | ❌ No | ❌ No | ✅ Sí |
| **Errorbars** | ❌ No | ❌ No | ✅ Sí |
| **Fill Between** | ❌ No | ❌ No | ✅ Sí |
| **Step Plot** | ❌ No | ❌ No | ✅ Sí |
| **Correlation Heatmap** | ❌ No | ❌ No | ✅ Sí |
| **Confusion Matrix** | ❌ No | ❌ No | ✅ Sí |

### Estadísticas

- **Total de gráficos:** 30
- **Gráficos con selección:** 4 (Scatter, Bar, Grouped Bar, Pie)
- **Gráficos sin selección:** 26
- **Gráficos que pueden ser vista principal:** 4 (Scatter, Bar, Grouped Bar, Pie)
- **Gráficos que pueden ser vistas enlazadas:** 30 (todos)

---

## 🔍 Notas Técnicas

### Implementación de Selección

- **Scatter Plot:** Implementado con `d3.brush()` y eventos de click en JavaScript (`matrix.js`)
- **Bar Chart:** Implementado con eventos de click en barras en JavaScript
- **Grouped Bar Chart:** Similar a Bar Chart, click en barras del grupo
- **Pie Chart:** Implementado con eventos de click en segmentos en JavaScript

### Implementación de Linked Views

- **Sistema:** Usa `SelectionModel` y callbacks reactivos en `ReactiveMatrixLayout`
- **Actualización:** Las vistas enlazadas se actualizan automáticamente cuando cambia `SelectionModel`
- **Datos:** Los datos seleccionados se filtran y se pasan a las vistas enlazadas
- **JavaScript:** El código JavaScript detecta `__linked_to__` en el spec y actualiza las vistas correspondientes

### Acceso a Datos Seleccionados

```python
from BESTLIB.reactive import SelectionModel

selection = SelectionModel()
layout = ReactiveMatrixLayout("SB", selection_model=selection)
layout.add_scatter('S', df, ...)
layout.display()

# Obtener datos seleccionados
selected_data = selection.get_items()  # Lista de diccionarios
selected_count = selection.get_count()  # Número de elementos
selected_df = selection.get_dataframe()  # DataFrame (si pandas está disponible)
```

---

## 📚 Referencias

- **Código fuente:** `BESTLIB/charts/`
- **Sistema reactivo:** `BESTLIB/reactive.py`
- **Vistas enlazadas legacy:** `BESTLIB/linked.py` (deprecated)
- **JavaScript:** `BESTLIB/matrix.js`
- **Documentación de interactividad:** `docs/development/CAPACIDADES_INTERACTIVIDAD.md`

---

**Última actualización:** Generado automáticamente revisando el código fuente de BESTLIB

