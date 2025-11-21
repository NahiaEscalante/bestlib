# 📚 Documentación Completa de BESTLIB

**BESTLIB (Beautiful & Efficient Visualization Library)** es una librería de visualización interactiva para Jupyter Notebooks que permite crear dashboards con layouts ASCII y gráficos D3.js.

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Instalación](#instalación)
3. [Conceptos Fundamentales](#conceptos-fundamentales)
4. [Clases Principales](#clases-principales)
5. [Tipos de Gráficos](#tipos-de-gráficos)
6. [Parámetros Comunes](#parámetros-comunes)
7. [Vistas Enlazadas (Linked Views)](#vistas-enlazadas-linked-views)
8. [Sistema Reactivo](#sistema-reactivo)
9. [Interactividad](#interactividad)
10. [Ejemplos Completos](#ejemplos-completos)

---

## Introducción

BESTLIB permite crear visualizaciones interactivas en Jupyter Notebooks usando:

- **Layouts ASCII**: Define la disposición de gráficos usando texto simple
- **Gráficos D3.js**: Renderizado interactivo en el navegador
- **Sistema Reactivo**: Actualización automática sin re-ejecutar celdas
- **Vistas Enlazadas**: Sincronización automática entre múltiples gráficos

### Características Principales

- ✅ **13+ tipos de gráficos** disponibles
- ✅ **Soporte completo para pandas DataFrames**
- ✅ **Comunicación bidireccional** Python ↔ JavaScript
- ✅ **Selecciones interactivas** con brush y click
- ✅ **Variables de selección** para análisis posterior
- ✅ **Tooltips y zoom** en gráficos interactivos

---

## Instalación

### Instalación Local (Jupyter Notebook/Lab)

```bash
pip install --upgrade --force-reinstall git+https://github.com/NahiaEscalante/bestlib.git@widget_mod
```

### Instalación en Google Colab

```python
!pip install --upgrade --no-deps git+https://github.com/NahiaEscalante/bestlib.git@widget_mod
```

**Nota:** Colab ya tiene las dependencias necesarias (`pandas`, `numpy`, `ipywidgets`).

### Dependencias

- `ipython` >= 7.0
- `ipywidgets` >= 7.0
- `pandas` >= 1.3.0 (opcional pero recomendado)
- `numpy` >= 1.20.0 (opcional)

---

## Conceptos Fundamentales

### Layout ASCII

Un layout ASCII define la disposición de gráficos usando letras. Cada letra representa una celda donde se puede colocar un gráfico.

**Ejemplos:**

```python
# Layout simple: 1 gráfico
layout = MatrixLayout("S")

# Layout en fila: 2 gráficos
layout = MatrixLayout("AB")

# Layout en columna: 2 gráficos
layout = MatrixLayout("""
A
B
""")

# Layout en matriz: 2x2
layout = MatrixLayout("""
AB
CD
""")

# Layout complejo: múltiples gráficos
layout = MatrixLayout("""
ASB
HXP
""")
```

### Letras y Celdas

- Cada letra única representa una celda
- Las letras repetidas muestran el mismo gráfico en múltiples posiciones
- Los espacios y saltos de línea se respetan para el layout

---

## Clases Principales

### 1. MatrixLayout

Clase base para crear visualizaciones estáticas (sin reactividad).

#### Constructor

```python
MatrixLayout(ascii_layout=None)
```

**Parámetros:**
- `ascii_layout` (str, opcional): Layout ASCII que define la disposición de gráficos

**Ejemplo:**
```python
from BESTLIB import MatrixLayout

layout = MatrixLayout("AB")
```

#### Métodos Principales

##### `map_scatter(letter, data, x_col=None, y_col=None, category_col=None, size_col=None, color_col=None, **kwargs)`

Crea un scatter plot.

**Parámetros:**
- `letter` (str): Letra del layout donde irá el gráfico
- `data`: DataFrame de pandas o lista de diccionarios
- `x_col` (str, opcional): Nombre de columna para eje X
- `y_col` (str, opcional): Nombre de columna para eje Y
- `category_col` (str, opcional): Columna para categorías (colorear puntos)
- `size_col` (str, opcional): Columna para tamaño de puntos
- `color_col` (str, opcional): Columna para color de puntos
- `**kwargs`: Argumentos adicionales (ver [Parámetros Comunes](#parámetros-comunes))

**Ejemplo:**
```python
import pandas as pd

df = pd.read_csv('iris.csv')
MatrixLayout.map_scatter('S', df, 
                         x_col='sepal_length', 
                         y_col='sepal_width',
                         category_col='species',
                         interactive=True,
                         xLabel='Sepal Length',
                         yLabel='Sepal Width')
```

##### `map_barchart(letter, data, category_col=None, value_col=None, **kwargs)`

Crea un bar chart (gráfico de barras).

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame o lista de diccionarios
- `category_col` (str, opcional): Columna para categorías
- `value_col` (str, opcional): Columna para valores (si no se especifica, cuenta)
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
# Con valores
MatrixLayout.map_barchart('B', df, 
                          category_col='species', 
                          value_col='sepal_length',
                          xLabel='Species',
                          yLabel='Average Sepal Length')

# Sin valores (cuenta automáticamente)
MatrixLayout.map_barchart('B', df, 
                          category_col='species',
                          xLabel='Species',
                          yLabel='Count')
```

##### `map_grouped_barchart(letter, data, main_col=None, sub_col=None, value_col=None, **kwargs)`

Crea un bar chart agrupado (categorías principales con subcategorías).

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame o lista de diccionarios
- `main_col` (str): Columna para categoría principal
- `sub_col` (str): Columna para subcategoría
- `value_col` (str, opcional): Columna para valores
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
MatrixLayout.map_grouped_barchart('G', df,
                                  main_col='species',
                                  sub_col='petal_length_category',
                                  value_col='sepal_length')
```

##### `map_histogram(letter, data, value_col=None, bins=10, **kwargs)`

Crea un histograma.

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame o lista de diccionarios
- `value_col` (str, opcional): Columna numérica para el histograma
- `bins` (int, opcional): Número de bins (por defecto 10)
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
MatrixLayout.map_histogram('H', df,
                           value_col='sepal_length',
                           bins=20,
                           xLabel='Sepal Length',
                           yLabel='Frequency')
```

##### `map_boxplot(letter, data, category_col=None, value_col=None, column=None, **kwargs)`

Crea un boxplot.

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame o lista de diccionarios
- `category_col` (str, opcional): Columna para categorías (eje X)
- `value_col` (str, opcional): Columna para valores (eje Y)
- `column` (str, opcional): Alias de `value_col`
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
MatrixLayout.map_boxplot('X', df,
                         category_col='species',
                         value_col='sepal_width',
                         xLabel='Species',
                         yLabel='Sepal Width')
```

##### `map_heatmap(letter, data, x_col=None, y_col=None, value_col=None, **kwargs)`

Crea un heatmap.

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame (matriz) o lista de diccionarios
- `x_col` (str, opcional): Columna para eje X (si es tabla larga)
- `y_col` (str, opcional): Columna para eje Y (si es tabla larga)
- `value_col` (str, opcional): Columna para valores (si es tabla larga)
- `**kwargs`: Argumentos adicionales

**Nota:** Si se pasa un DataFrame sin especificar columnas, se asume que es una matriz y se usan índices/columnas automáticamente.

**Ejemplo:**
```python
# Matriz de correlación
corr_matrix = df.select_dtypes(include=['number']).corr()
MatrixLayout.map_heatmap('M', corr_matrix)

# Tabla larga
MatrixLayout.map_heatmap('M', df,
                         x_col='category',
                         y_col='subcategory',
                         value_col='value')
```

##### `map_correlation_heatmap(letter, data, **kwargs)`

Crea un heatmap de matriz de correlación (Pearson).

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame con columnas numéricas
- `**kwargs`: Argumentos adicionales (incluye `showValues` para mostrar valores numéricos)

**Ejemplo:**
```python
MatrixLayout.map_correlation_heatmap('C', df, showValues=True)
```

##### `map_line(letter, data, x_col=None, y_col=None, series_col=None, **kwargs)`

Crea un line chart (gráfico de líneas).

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame o lista de diccionarios
- `x_col` (str): Columna para eje X
- `y_col` (str): Columna para eje Y
- `series_col` (str, opcional): Columna para múltiples series
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
# Línea simple
MatrixLayout.map_line('L', df,
                      x_col='date',
                      y_col='value')

# Múltiples series
MatrixLayout.map_line('L', df,
                      x_col='date',
                      y_col='value',
                      series_col='category')
```

##### `map_pie(letter, data, category_col=None, value_col=None, **kwargs)`

Crea un pie chart (gráfico de pastel).

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame o lista de diccionarios
- `category_col` (str, opcional): Columna para categorías
- `value_col` (str, opcional): Columna para valores (si no se especifica, cuenta)
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
MatrixLayout.map_pie('P', df,
                     category_col='species',
                     value_col='sepal_length')
```

##### `map_violin(letter, data, value_col=None, category_col=None, bins=20, **kwargs)`

Crea un violin plot.

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame o lista de diccionarios
- `value_col` (str, opcional): Columna para valores
- `category_col` (str, opcional): Columna para categorías
- `bins` (int, opcional): Número de bins para el histograma (por defecto 20)
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
MatrixLayout.map_violin('V', df,
                        value_col='sepal_length',
                        category_col='species',
                        bins=30)
```

##### `map_radviz(letter, data, features=None, class_col=None, **kwargs)`

Crea un RadViz plot (visualización radial).

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame de pandas
- `features` (list, opcional): Lista de columnas numéricas (por defecto, todas las numéricas)
- `class_col` (str, opcional): Columna para categorías
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
MatrixLayout.map_radviz('R', df,
                        features=['sepal_length', 'sepal_width', 'petal_length', 'petal_width'],
                        class_col='species')
```

##### `map_star_coordinates(letter, data, features=None, class_col=None, **kwargs)`

Crea un Star Coordinates plot (similar a RadViz pero con nodos movibles).

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame de pandas
- `features` (list, opcional): Lista de columnas numéricas (por defecto, todas las numéricas)
- `class_col` (str, opcional): Columna para categorías
- `**kwargs`: Argumentos adicionales

**Características:**
- Los nodos pueden moverse libremente por toda el área del gráfico
- Líneas desde el centro del gráfico hasta los nodos como referencia visual
- Los puntos se recalculan automáticamente cuando se mueven los nodos

**Ejemplo:**
```python
MatrixLayout.map_star_coordinates('SC', df,
                                  features=['sepal_length', 'sepal_width', 'petal_length', 'petal_width'],
                                  class_col='species',
                                  interactive=True)
```

##### `map_parallel_coordinates(letter, data, dimensions=None, category_col=None, **kwargs)`

Crea un Parallel Coordinates Plot.

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame de pandas
- `dimensions` (list, opcional): Lista de columnas a usar como ejes (por defecto, todas las numéricas)
- `category_col` (str, opcional): Columna para categorías (colorear líneas)
- `**kwargs`: Argumentos adicionales

**Características:**
- Ejes paralelos que pueden moverse y reordenarse
- Líneas rectas entre columnas (no curvas)
- Reordenamiento de columnas por intercambio (drag & drop)
- Selección de líneas completas

**Ejemplo:**
```python
MatrixLayout.map_parallel_coordinates('PC', df,
                                      dimensions=['sepal_length', 'sepal_width', 'petal_length', 'petal_width'],
                                      category_col='species',
                                      interactive=True)
```

#### Métodos de Utilidad

##### `display()`

Muestra el layout con todos los gráficos configurados.

```python
layout = MatrixLayout("AB")
# ... configurar gráficos ...
layout.display()
```

##### `on(event, callback)`

Registra un callback para eventos del layout.

**Parámetros:**
- `event` (str): Tipo de evento ('select', 'click', 'brush', etc.)
- `callback` (callable): Función que recibe el payload del evento

**Ejemplo:**
```python
def on_select(payload):
    items = payload.get('items', [])
    print(f"Seleccionados: {len(items)} elementos")

layout.on('select', on_select)
```

##### `connect_selection(selection_model)`

Conecta un modelo de selección al layout.

**Parámetros:**
- `selection_model`: Instancia de `SelectionModel`

**Ejemplo:**
```python
from BESTLIB.reactive import SelectionModel

selection = SelectionModel()
layout.connect_selection(selection)
```

##### `set_debug(enabled)`

Habilita o deshabilita el modo debug.

```python
MatrixLayout.set_debug(True)  # Activar mensajes de debug
```

---

### 2. ReactiveMatrixLayout

Clase para crear visualizaciones reactivas con vistas enlazadas.

#### Constructor

```python
ReactiveMatrixLayout(ascii_layout=None, selection_model=None)
```

**Parámetros:**
- `ascii_layout` (str, opcional): Layout ASCII
- `selection_model` (SelectionModel, opcional): Modelo de selección (se crea uno por defecto)

**Ejemplo:**
```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

selection = SelectionModel()
layout = ReactiveMatrixLayout("ASB", selection_model=selection)
```

#### Métodos Principales

##### `set_data(data)`

Establece los datos para todos los gráficos del layout.

**Parámetros:**
- `data`: DataFrame de pandas o lista de diccionarios

**Ejemplo:**
```python
layout.set_data(df)
```

##### `add_scatter(letter, data=None, x_col=None, y_col=None, category_col=None, interactive=True, **kwargs)`

Agrega un scatter plot (vista principal con brush selection).

**Parámetros:**
- `letter` (str): Letra del layout
- `data`: DataFrame o lista de diccionarios (opcional si se usó `set_data()`)
- `x_col` (str): Columna para eje X
- `y_col` (str): Columna para eje Y
- `category_col` (str, opcional): Columna para categorías
- `interactive` (bool): Si True, habilita brush selection (por defecto True)
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
layout.add_scatter('A', df,
                   x_col='sepal_length',
                   y_col='sepal_width',
                   category_col='species',
                   interactive=True)
```

##### `add_barchart(letter, category_col=None, value_col=None, linked_to=None, interactive=None, selection_var=None, **kwargs)`

Agrega un bar chart (puede ser vista principal o enlazada).

**Parámetros:**
- `letter` (str): Letra del layout
- `category_col` (str, opcional): Columna para categorías
- `value_col` (str, opcional): Columna para valores
- `linked_to` (str, opcional): Letra de la vista principal que actualiza este gráfico
- `interactive` (bool, opcional): Si True, permite selección por click
- `selection_var` (str, opcional): Nombre de variable Python para guardar selecciones
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
# Vista principal (interactiva)
layout.add_barchart('B', 
                    category_col='species',
                    interactive=True,
                    selection_var='selected_species')

# Vista enlazada (se actualiza automáticamente)
layout.add_barchart('B',
                    category_col='species',
                    linked_to='A')  # Se actualiza cuando se selecciona en 'A'
```

##### `add_grouped_barchart(letter, main_col=None, sub_col=None, value_col=None, linked_to=None, interactive=None, selection_var=None, **kwargs)`

Agrega un grouped bar chart.

**Parámetros:**
- `letter` (str): Letra del layout
- `main_col` (str): Columna para categoría principal
- `sub_col` (str): Columna para subcategoría
- `value_col` (str, opcional): Columna para valores
- `linked_to` (str, opcional): Letra de la vista principal
- `interactive` (bool, opcional): Si True, permite selección
- `selection_var` (str, opcional): Nombre de variable para guardar selecciones
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
layout.add_grouped_barchart('G',
                            main_col='species',
                            sub_col='petal_length_category',
                            value_col='sepal_length',
                            linked_to='A')
```

##### `add_histogram(letter, column=None, bins=20, linked_to=None, interactive=None, selection_var=None, **kwargs)`

Agrega un histograma.

**Parámetros:**
- `letter` (str): Letra del layout
- `column` (str): Columna numérica para el histograma
- `bins` (int): Número de bins (por defecto 20)
- `linked_to` (str, opcional): Letra de la vista principal
- `interactive` (bool, opcional): Si True, permite selección por click
- `selection_var` (str, opcional): Nombre de variable para guardar selecciones
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
# Vista principal
layout.add_histogram('H',
                     column='sepal_length',
                     bins=15,
                     interactive=True,
                     selection_var='selected_bins')

# Vista enlazada
layout.add_histogram('H',
                     column='sepal_length',
                     bins=15,
                     linked_to='A')
```

##### `add_boxplot(letter, column=None, category_col=None, linked_to=None, **kwargs)`

Agrega un boxplot enlazado.

**Parámetros:**
- `letter` (str): Letra del layout
- `column` (str): Columna numérica para valores
- `category_col` (str, opcional): Columna para categorías
- `linked_to` (str, opcional): Letra de la vista principal
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
layout.add_boxplot('X',
                   column='petal_length',
                   category_col='species',
                   linked_to='S')
```

##### `add_heatmap(letter, x_col=None, y_col=None, value_col=None, linked_to=None, **kwargs)`

Agrega un heatmap.

**Parámetros:**
- `letter` (str): Letra del layout
- `x_col` (str, opcional): Columna para eje X
- `y_col` (str, opcional): Columna para eje Y
- `value_col` (str, opcional): Columna para valores
- `linked_to` (str, opcional): Letra de la vista principal
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
layout.add_heatmap('M',
                   x_col='category',
                   y_col='subcategory',
                   value_col='value',
                   linked_to='A')
```

##### `add_correlation_heatmap(letter, linked_to=None, **kwargs)`

Agrega un heatmap de matriz de correlación.

**Parámetros:**
- `letter` (str): Letra del layout
- `linked_to` (str, opcional): Letra de la vista principal
- `**kwargs`: Argumentos adicionales (incluye `showValues`)

**Ejemplo:**
```python
layout.add_correlation_heatmap('C', linked_to='A', showValues=True)
```

##### `add_line(letter, x_col=None, y_col=None, series_col=None, linked_to=None, **kwargs)`

Agrega un line chart.

**Parámetros:**
- `letter` (str): Letra del layout
- `x_col` (str): Columna para eje X
- `y_col` (str): Columna para eje Y
- `series_col` (str, opcional): Columna para múltiples series
- `linked_to` (str, opcional): Letra de la vista principal
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
layout.add_line('L',
                x_col='date',
                y_col='value',
                series_col='category',
                linked_to='A')
```

##### `add_pie(letter, category_col=None, value_col=None, linked_to=None, interactive=None, selection_var=None, **kwargs)`

Agrega un pie chart.

**Parámetros:**
- `letter` (str): Letra del layout
- `category_col` (str, opcional): Columna para categorías
- `value_col` (str, opcional): Columna para valores
- `linked_to` (str, opcional): Letra de la vista principal
- `interactive` (bool, opcional): Si True, permite selección por click
- `selection_var` (str, opcional): Nombre de variable para guardar selecciones
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
# Vista principal
layout.add_pie('P',
               category_col='species',
               interactive=True,
               selection_var='selected_species')

# Vista enlazada
layout.add_pie('P',
               category_col='species',
               linked_to='B')
```

##### `add_violin(letter, value_col=None, category_col=None, bins=20, linked_to=None, **kwargs)`

Agrega un violin plot.

**Parámetros:**
- `letter` (str): Letra del layout
- `value_col` (str, opcional): Columna para valores
- `category_col` (str, opcional): Columna para categorías
- `bins` (int): Número de bins (por defecto 20)
- `linked_to` (str, opcional): Letra de la vista principal
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
layout.add_violin('V',
                  value_col='sepal_length',
                  category_col='species',
                  bins=30,
                  linked_to='A')
```

##### `add_radviz(letter, features=None, class_col=None, linked_to=None, **kwargs)`

Agrega un RadViz plot.

**Parámetros:**
- `letter` (str): Letra del layout
- `features` (list, opcional): Lista de columnas numéricas
- `class_col` (str, opcional): Columna para categorías
- `linked_to` (str, opcional): Letra de la vista principal
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
layout.add_radviz('R',
                  features=['sepal_length', 'sepal_width', 'petal_length', 'petal_width'],
                  class_col='species',
                  linked_to='A')
```

##### `add_star_coordinates(letter, features=None, class_col=None, linked_to=None, **kwargs)`

Agrega un Star Coordinates plot.

**Parámetros:**
- `letter` (str): Letra del layout
- `features` (list, opcional): Lista de columnas numéricas
- `class_col` (str, opcional): Columna para categorías
- `linked_to` (str, opcional): Letra de la vista principal
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
layout.add_star_coordinates('SC',
                            features=['sepal_length', 'sepal_width', 'petal_length', 'petal_width'],
                            class_col='species',
                            linked_to='A',
                            interactive=True)
```

##### `add_parallel_coordinates(letter, dimensions=None, category_col=None, linked_to=None, **kwargs)`

Agrega un Parallel Coordinates Plot.

**Parámetros:**
- `letter` (str): Letra del layout
- `dimensions` (list, opcional): Lista de columnas a usar como ejes
- `category_col` (str, opcional): Columna para categorías
- `linked_to` (str, opcional): Letra de la vista principal
- `**kwargs`: Argumentos adicionales

**Ejemplo:**
```python
layout.add_parallel_coordinates('PC',
                                dimensions=['sepal_length', 'sepal_width', 'petal_length', 'petal_width'],
                                category_col='species',
                                linked_to='A',
                                interactive=True)
```

##### `display()`

Muestra el layout con todos los gráficos configurados.

```python
layout.display()
```

---

### 3. SelectionModel

Modelo reactivo especializado para selecciones de brush.

#### Constructor

```python
SelectionModel()
```

#### Métodos Principales

##### `on_change(callback)`

Registra un callback que se ejecuta cuando los datos cambian.

**Parámetros:**
- `callback` (callable): Función que recibe `(items, count)` como argumentos

**Ejemplo:**
```python
def on_select(items, count):
    print(f"✅ {count} puntos seleccionados")
    # items es un DataFrame de pandas con los datos seleccionados

selection = SelectionModel()
selection.on_change(on_select)
```

##### `update(items)`

Actualiza los items seleccionados (normalmente llamado internamente).

**Parámetros:**
- `items`: Lista de diccionarios o DataFrame

##### `get_items()`

Obtiene los items seleccionados actuales.

**Retorna:**
- DataFrame de pandas (si pandas está disponible) o lista de diccionarios

**Ejemplo:**
```python
selected_data = selection.get_items()
print(f"Filas seleccionadas: {len(selected_data)}")
```

##### `get_count()`

Obtiene el número de items seleccionados.

**Retorna:**
- int: Número de items

---

### 4. LinkedViews

Gestor de vistas enlazadas (alternativa a ReactiveMatrixLayout).

**Nota:** Esta clase es una alternativa más simple pero menos potente que `ReactiveMatrixLayout`. Se recomienda usar `ReactiveMatrixLayout` para la mayoría de casos.

---

## Parámetros Comunes

Todos los métodos de gráficos aceptan los siguientes parámetros opcionales en `**kwargs`:

### Etiquetas y Títulos

- `xLabel` (str): Etiqueta para el eje X
- `yLabel` (str): Etiqueta para el eje Y
- `title` (str): Título del gráfico

**Ejemplo:**
```python
MatrixLayout.map_scatter('S', df,
                         x_col='sepal_length',
                         y_col='sepal_width',
                         xLabel='Sepal Length (cm)',
                         yLabel='Sepal Width (cm)',
                         title='Iris Dataset')
```

### Interactividad

- `interactive` (bool): Si True, habilita interactividad (brush, click, tooltips)

**Ejemplo:**
```python
MatrixLayout.map_scatter('S', df,
                         x_col='sepal_length',
                         y_col='sepal_width',
                         interactive=True)
```

### Tamaño

- `figsize` (tuple): Tamaño del gráfico en píxeles `(width, height)` o pulgadas `(width, height)` si valores <= 50

**Ejemplo:**
```python
# En píxeles
MatrixLayout.map_scatter('S', df,
                         x_col='sepal_length',
                         y_col='sepal_width',
                         figsize=(800, 600))

# En pulgadas (se convierte automáticamente a píxeles)
MatrixLayout.map_scatter('S', df,
                         x_col='sepal_length',
                         y_col='sepal_width',
                         figsize=(8, 6))
```

### Colores

- `color` (str): Color único para todos los elementos
- `colorMap` (dict): Mapa de colores para categorías `{'category': 'color'}`

**Ejemplo:**
```python
# Color único
MatrixLayout.map_barchart('B', df,
                          category_col='species',
                          color='#4a90e2')

# Mapa de colores
MatrixLayout.map_barchart('B', df,
                          category_col='species',
                          colorMap={'setosa': '#e74c3c', 
                                   'versicolor': '#3498db', 
                                   'virginica': '#2ecc71'})
```

### Ejes

- `axes` (bool): Si True, muestra ejes (por defecto True)
- `xLabelRotation` (int): Rotación de la etiqueta del eje X en grados (por defecto 0)
- `yLabelRotation` (int): Rotación de la etiqueta del eje Y en grados (por defecto -90)

**Ejemplo:**
```python
MatrixLayout.map_barchart('B', df,
                          category_col='species',
                          axes=True,
                          xLabelRotation=45,
                          yLabelRotation=-90)
```

### Otros Parámetros Específicos

#### Para Scatter Plots

- `pointRadius` (float): Radio de los puntos (por defecto 3)
- `opacity` (float): Opacidad de los puntos (0.0 a 1.0)

**Ejemplo:**
```python
MatrixLayout.map_scatter('S', df,
                         x_col='sepal_length',
                         y_col='sepal_width',
                         pointRadius=5,
                         opacity=0.7)
```

#### Para Heatmaps

- `showValues` (bool): Si True, muestra valores numéricos en las celdas

**Ejemplo:**
```python
MatrixLayout.map_correlation_heatmap('C', df, showValues=True)
```

---

## Vistas Enlazadas (Linked Views)

Las vistas enlazadas permiten que múltiples gráficos se actualicen automáticamente cuando se selecciona en una vista principal.

### Concepto

- **Vista Principal**: Gráfico interactivo donde el usuario hace selecciones (normalmente scatter plots)
- **Vista Enlazada**: Gráfico que se actualiza automáticamente cuando cambia la selección en la vista principal

### Ejemplo Completo

```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Cargar datos
df = pd.read_csv('iris.csv')

# Crear layout reactivo
layout = ReactiveMatrixLayout("""
ASB
HXP
""", selection_model=SelectionModel())

# Establecer datos
layout.set_data(df)

# Vista principal: Scatter plot A
layout.add_scatter('A', 
                   x_col='sepal_length', 
                   y_col='sepal_width',
                   color_col='species',
                   interactive=True)

# Vista principal: Scatter plot S
layout.add_scatter('S',
                   x_col='petal_length',
                   y_col='petal_width',
                   color_col='species',
                   interactive=True)

# Vista enlazada: Histograma H (se actualiza cuando se selecciona en A)
layout.add_histogram('H',
                     column='sepal_length',
                     linked_to='A',
                     bins=15)

# Vista enlazada: Boxplot X (se actualiza cuando se selecciona en S)
layout.add_boxplot('X',
                   column='petal_length',
                   category_col='species',
                   linked_to='S')

# Vista enlazada: Bar chart B (se actualiza cuando se selecciona en A)
layout.add_barchart('B',
                    category_col='species',
                    linked_to='A')

# Vista enlazada: Pie chart P (se actualiza cuando se selecciona en B)
layout.add_pie('P',
               category_col='species',
               linked_to='B')

# Mostrar layout
layout.display()
```

### Flujo de Actualización

1. Usuario selecciona puntos en el scatter plot 'A' (brush selection)
2. El histograma 'H' se actualiza automáticamente con los datos seleccionados
3. El bar chart 'B' se actualiza automáticamente con los datos seleccionados
4. El pie chart 'P' se actualiza automáticamente cuando cambia 'B'

### Variables de Selección

Puedes guardar las selecciones en variables de Python para análisis posterior:

```python
# Crear layout con variable de selección
layout.add_barchart('B',
                    category_col='species',
                    interactive=True,
                    selection_var='selected_species')

layout.display()

# Después de seleccionar en el gráfico, la variable contiene los datos
print(selected_species)  # DataFrame de pandas con las filas seleccionadas
```

---

## Sistema Reactivo

El sistema reactivo permite que los datos se actualicen automáticamente sin re-ejecutar celdas.

### SelectionModel

El `SelectionModel` es el componente central del sistema reactivo:

```python
from BESTLIB.reactive import SelectionModel

# Crear modelo de selección
selection = SelectionModel()

# Registrar callback
def on_select(items, count):
    print(f"✅ {count} elementos seleccionados")
    # items es un DataFrame de pandas

selection.on_change(on_select)

# Conectar con layout
layout = ReactiveMatrixLayout("AB", selection_model=selection)
layout.set_data(df)
layout.add_scatter('A', x_col='x', y_col='y', interactive=True)
layout.display()

# Acceder a datos seleccionados
selected_data = selection.get_items()  # DataFrame de pandas
```

### Datos Seleccionados

Cuando se selecciona en un gráfico interactivo:

- Los datos seleccionados se devuelven como **DataFrame de pandas** (si pandas está disponible)
- Si pandas no está disponible, se devuelven como lista de diccionarios
- Los datos contienen **todas las filas originales** del DataFrame, no solo información resumida

**Ejemplo:**
```python
# Seleccionar en histograma
layout.add_histogram('H',
                     column='sepal_length',
                     interactive=True,
                     selection_var='selected_bins')

# Después de seleccionar un bin, selected_bins contiene todas las filas
# del DataFrame que caen en ese bin
print(selected_bins)  # DataFrame con todas las filas originales
```

---

## Interactividad

### Tipos de Interactividad

#### 1. Brush Selection (Scatter Plots)

Permite seleccionar puntos arrastrando un rectángulo sobre el gráfico.

**Habilitación:**
```python
layout.add_scatter('S', df,
                   x_col='sepal_length',
                   y_col='sepal_width',
                   interactive=True)  # Habilita brush selection
```

**Uso:**
- Click y arrastrar para crear un rectángulo de selección
- Los puntos dentro del rectángulo se resaltan
- Los gráficos enlazados se actualizan automáticamente

#### 2. Click Selection

Permite seleccionar elementos haciendo click.

**Gráficos que soportan click:**
- Bar Chart
- Histogram
- Pie Chart
- Parallel Coordinates (líneas)

**Ejemplo:**
```python
layout.add_barchart('B',
                    category_col='species',
                    interactive=True)  # Habilita click selection
```

**Uso:**
- Click en una barra para seleccionarla
- Ctrl/Cmd + Click para selección múltiple (en Parallel Coordinates)

#### 3. Drag & Drop

Permite mover elementos del gráfico.

**Gráficos que soportan drag & drop:**
- Star Coordinates (nodos)
- Parallel Coordinates (columnas/ejes)

**Ejemplo:**
```python
# Star Coordinates: arrastrar nodos
layout.add_star_coordinates('SC', df,
                            features=['sepal_length', 'sepal_width'],
                            interactive=True)

# Parallel Coordinates: arrastrar columnas para reordenar
layout.add_parallel_coordinates('PC', df,
                                dimensions=['sepal_length', 'sepal_width'],
                                interactive=True)
```

#### 4. Tooltips

Muestra información al pasar el mouse sobre elementos.

**Habilitación automática:**
- Los tooltips se muestran automáticamente en gráficos interactivos
- Muestran información relevante del elemento (coordenadas, valores, categorías)

---

## Ejemplos Completos

### Ejemplo 1: Layout Simple con Scatter Plot

```python
from BESTLIB import MatrixLayout
import pandas as pd

# Cargar datos
df = pd.read_csv('iris.csv')

# Crear scatter plot
MatrixLayout.map_scatter('S', df,
                         x_col='sepal_length',
                         y_col='sepal_width',
                         category_col='species',
                         interactive=True,
                         xLabel='Sepal Length',
                         yLabel='Sepal Width')

layout = MatrixLayout("S")
layout.display()
```

### Ejemplo 2: Layout con Múltiples Gráficos

```python
from BESTLIB import MatrixLayout
import pandas as pd

df = pd.read_csv('iris.csv')

# Configurar múltiples gráficos
MatrixLayout.map_scatter('S', df,
                         x_col='sepal_length',
                         y_col='sepal_width',
                         category_col='species')

MatrixLayout.map_barchart('B', df,
                          category_col='species',
                          value_col='sepal_length')

MatrixLayout.map_histogram('H', df,
                           value_col='petal_length',
                           bins=20)

MatrixLayout.map_boxplot('X', df,
                         category_col='species',
                         value_col='sepal_width')

# Crear layout 2x2
layout = MatrixLayout("""
SB
HX
""")
layout.display()
```

### Ejemplo 3: Vistas Enlazadas Complejas

```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

df = pd.read_csv('iris.csv')

# Crear layout reactivo
layout = ReactiveMatrixLayout("""
ASB
HXP
""", selection_model=SelectionModel())

layout.set_data(df)

# Scatter plots principales
layout.add_scatter('A',
                   x_col='sepal_length',
                   y_col='sepal_width',
                   color_col='species',
                   interactive=True)

layout.add_scatter('S',
                   x_col='petal_length',
                   y_col='petal_width',
                   color_col='species',
                   interactive=True)

# Gráficos enlazados
layout.add_histogram('H',
                     column='sepal_length',
                     linked_to='A',
                     bins=15)

layout.add_boxplot('X',
                   column='petal_length',
                   category_col='species',
                   linked_to='S')

layout.add_barchart('B',
                    category_col='species',
                    linked_to='A')

layout.add_pie('P',
               category_col='species',
               linked_to='B')

layout.display()

# Acceder a datos seleccionados
selected = layout.selection_model.get_items()
print(f"Filas seleccionadas: {len(selected)}")
```

### Ejemplo 4: Star Coordinates Interactivo

```python
from BESTLIB.reactive import ReactiveMatrixLayout
import pandas as pd

df = pd.read_csv('iris.csv')

layout = ReactiveMatrixLayout("SC")
layout.set_data(df)

layout.add_star_coordinates('SC',
                            features=['sepal_length', 'sepal_width', 
                                     'petal_length', 'petal_width'],
                            class_col='species',
                            interactive=True)

layout.display()

# Los nodos pueden moverse libremente arrastrándolos
# Los puntos se recalculan automáticamente
```

### Ejemplo 5: Parallel Coordinates con Selección

```python
from BESTLIB.reactive import ReactiveMatrixLayout
import pandas as pd

df = pd.read_csv('iris.csv')

layout = ReactiveMatrixLayout("PC")
layout.set_data(df)

layout.add_parallel_coordinates('PC',
                                dimensions=['sepal_length', 'sepal_width',
                                           'petal_length', 'petal_width'],
                                category_col='species',
                                interactive=True)

layout.display()

# Características:
# - Líneas rectas entre columnas
# - Arrastrar columnas para reordenarlas (intercambio)
# - Click en líneas para seleccionarlas
# - Ctrl/Cmd + Click para selección múltiple
```

### Ejemplo 6: Variables de Selección

```python
from BESTLIB.reactive import ReactiveMatrixLayout
import pandas as pd

df = pd.read_csv('iris.csv')

layout = ReactiveMatrixLayout("BH")
layout.set_data(df)

# Bar chart con variable de selección
layout.add_barchart('B',
                    category_col='species',
                    interactive=True,
                    selection_var='selected_species')

# Histogram con variable de selección
layout.add_histogram('H',
                     column='sepal_length',
                     interactive=True,
                     selection_var='selected_bins')

layout.display()

# Después de seleccionar en los gráficos:
print(f"Especies seleccionadas: {len(selected_species)} filas")
print(f"Bins seleccionados: {len(selected_bins)} filas")

# Análisis posterior
if len(selected_species) > 0:
    print(selected_species.describe())
```

---

## Notas Importantes

### Datos Seleccionados

- **Formato**: Los datos seleccionados se devuelven como **DataFrame de pandas** (si pandas está disponible)
- **Contenido**: Contienen **todas las filas originales** del DataFrame, no solo información resumida
- **Acceso**: Usa `selection_model.get_items()` o variables de selección (`selection_var`)

### Orden de Features

- En **Star Coordinates** y **RadViz**, los features se ordenan **alfabéticamente** automáticamente
- Esto asegura consistencia en el orden de los nodos

### Normalización

- Los puntos en **Star Coordinates** y **RadViz** están normalizados a `[-1, 1]`
- Esto asegura que los puntos siempre estén dentro del área visible

### Compatibilidad

- BESTLIB funciona con o sin pandas instalado
- Si pandas no está disponible, algunas funcionalidades están limitadas
- Los DataFrames se convierten automáticamente a listas de diccionarios cuando es necesario

---

## Troubleshooting

### Los gráficos no se muestran

1. Verifica que estés en un Jupyter Notebook/Lab
2. Asegúrate de haber llamado `layout.display()`
3. Revisa la consola del navegador para errores JavaScript

### Las vistas enlazadas no se actualizan

1. Verifica que `linked_to` apunte a una letra válida
2. Asegúrate de que la vista principal tenga `interactive=True`
3. Verifica que los datos estén establecidos con `set_data()`

### Los datos seleccionados están vacíos

1. Verifica que hayas seleccionado elementos en el gráfico
2. Asegúrate de que `interactive=True` esté habilitado
3. Revisa que la variable de selección esté correctamente configurada

### Errores de importación

1. Verifica que todas las dependencias estén instaladas
2. En Colab, usa `--no-deps` durante la instalación
3. Reinicia el kernel después de instalar

---

## Referencia Rápida

### Tipos de Gráficos Disponibles

| Tipo | Método MatrixLayout | Método ReactiveMatrixLayout | Interactivo |
|------|---------------------|----------------------------|-------------|
| Scatter Plot | `map_scatter` | `add_scatter` | ✅ Brush |
| Bar Chart | `map_barchart` | `add_barchart` | ✅ Click |
| Grouped Bar Chart | `map_grouped_barchart` | `add_grouped_barchart` | ✅ Click |
| Histogram | `map_histogram` | `add_histogram` | ✅ Click |
| Boxplot | `map_boxplot` | `add_boxplot` | ❌ |
| Heatmap | `map_heatmap` | `add_heatmap` | ❌ |
| Correlation Heatmap | `map_correlation_heatmap` | `add_correlation_heatmap` | ❌ |
| Line Chart | `map_line` | `add_line` | ❌ |
| Pie Chart | `map_pie` | `add_pie` | ✅ Click |
| Violin Plot | `map_violin` | `add_violin` | ❌ |
| RadViz | `map_radviz` | `add_radviz` | ✅ Brush |
| Star Coordinates | `map_star_coordinates` | `add_star_coordinates` | ✅ Drag & Brush |
| Parallel Coordinates | `map_parallel_coordinates` | `add_parallel_coordinates` | ✅ Drag & Click |

### Parámetros Comunes

- `xLabel`, `yLabel`, `title`: Etiquetas y títulos
- `interactive`: Habilita interactividad
- `figsize`: Tamaño del gráfico
- `color`, `colorMap`: Colores
- `axes`: Mostrar/ocultar ejes
- `xLabelRotation`, `yLabelRotation`: Rotación de etiquetas

---

## Conclusión

BESTLIB es una librería poderosa para crear visualizaciones interactivas en Jupyter Notebooks. Con su sistema de layouts ASCII, vistas enlazadas y reactividad, permite crear dashboards complejos de forma sencilla.

Para más ejemplos, consulta los notebooks en la carpeta `examples/`.

---

**Desarrollado por:** Nahia Escalante, Alejandro, Max

**Versión:** 1.0

**Licencia:** Ver archivo LICENSE en el repositorio

