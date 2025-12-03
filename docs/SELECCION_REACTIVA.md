## Guía de selección reactiva en BESTLIB

Esta guía explica cómo activar y consumir la selección interactiva en los gráficos
soportados por `ReactiveMatrixLayout`, garantizando que el usuario reciba
siempre un `pandas.DataFrame` (cuando pandas está disponible).

### 1. Conceptos generales

- **ReactiveMatrixLayout**: orquesta el layout y conecta la selección entre vistas.
- **SelectionModel**: modelo reactivo que recibe los ítems seleccionados y los expone
  como lista de diccionarios o `DataFrame`.
- **selection_var**: nombre de variable en Python donde se guarda la selección
  (por conveniencia) como `DataFrame` cuando hay pandas.

Patrón básico:

```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

selection = SelectionModel()
layout = ReactiveMatrixLayout("S", selection_model=selection).set_data(df)
```

Siempre que un gráfico sea **vista principal** con `interactive=True`, los clicks/brushes
en ese gráfico enviarán filas originales de vuelta a Python.

### 2. Scatter (`scatter`)

- **Método**: `add_scatter`
- **Unidad de selección**: puntos individuales o regiones (brush).

```python
layout = ReactiveMatrixLayout("S", selection_model=selection).set_data(df)
layout.add_scatter(
    'S',
    x_col='edad',
    y_col='salario',
    category_col='dept',
    interactive=True,               # vista principal
    selection_var='selected_scatter'
)
```

- **Datos recibidos**:
  - `selection.get_items()` devuelve lista o `DataFrame` con filas originales.
  - Variable `selected_scatter` contendrá un `DataFrame` (si pandas está instalado).

### 3. Bar chart (`bar`) y Grouped bar (`grouped_bar`)

- **Método**: `add_barchart`
- **Unidad de selección**:
  - `bar`: una barra por categoría.
  - `grouped_bar`: barra por (grupo, serie).

```python
layout = ReactiveMatrixLayout("B", selection_model=selection).set_data(df)
layout.add_barchart(
    'B',
    category_col='dept',
    value_col='ventas',
    interactive=True,               # vista principal
    selection_var='selected_bar'
)
```

Al hacer click en una barra:
- `selected_bar`: `DataFrame` con todas las filas cuyo `dept` coincide con la barra.

### 4. Histogram (`histogram`)

- **Método**: `add_histogram`
- **Unidad de selección**: bin del histograma.

```python
layout = ReactiveMatrixLayout("H", selection_model=selection).set_data(df)
layout.add_histogram(
    'H',
    column='edad',
    bins=20,
    interactive=True,
    selection_var='selected_bins'
)
```

Click en un bin:
- `selected_bins`: `DataFrame` con las filas que caen en ese rango de valores.

### 5. Boxplot (`boxplot`)

- **Método**: `add_boxplot`
- **Unidad de selección**: caja por categoría.

```python
layout = ReactiveMatrixLayout("BX", selection_model=selection).set_data(df)
layout.add_boxplot(
    'BX',
    column='salario',
    category_col='dept',
    interactive=True,
    selection_var='selected_box'
)
```

Click en una caja:
- `selected_box`: `DataFrame` con las filas de esa categoría.

### 6. Pie (`pie`)

- **Método**: `add_pie`
- **Unidad de selección**: segmento (categoría).

```python
layout = ReactiveMatrixLayout("P", selection_model=selection).set_data(df)
layout.add_pie(
    'P',
    category_col='dept',
    value_col='ventas',          # opcional
    interactive=True,
    selection_var='selected_dept'
)
```

Click en un segmento:
- `selected_dept`: `DataFrame` con filas de la categoría seleccionada.

### 7. Heatmap (`heatmap`)

- **Método**: `add_heatmap`
- **Unidad de selección**: celda `(x, y)`.

```python
layout = ReactiveMatrixLayout("H", selection_model=selection).set_data(df)
layout.add_heatmap(
    'H',
    x_col='col',
    y_col='row',
    value_col='val',
    interactive=True,
    selection_var='selected_cell'
)
```

Click en una celda:
- `selected_cell`: `DataFrame` con las filas originales que generaron esa celda.

### 8. Violin (`violin`)

- **Método**: `add_violin`
- **Unidad de selección**: violín (categoría).

```python
layout = ReactiveMatrixLayout("V", selection_model=selection).set_data(df)
layout.add_violin(
    'V',
    value_col='salario',
    category_col='dept',
    interactive=True,
    selection_var='selected_violin'
)
```

Click en un violín:
- `selected_violin`: `DataFrame` con filas de la categoría correspondiente.

### 9. Horizontal Bar (`horizontal_bar`)

- **Método**: `add_horizontal_bar`
- **Unidad de selección**: barra horizontal (categoría).

```python
layout = ReactiveMatrixLayout("HB", selection_model=selection).set_data(df)
layout.add_horizontal_bar(
    'HB',
    category_col='dept',
    value_col='ventas',
    interactive=True,
    selection_var='selected_hbar'
)
```

Click en una barra:
- `selected_hbar`: `DataFrame` con filas de esa categoría.

### 10. Errorbars (`errorbars`)

- **Método**: `add_errorbars`
- **Unidad de selección**: punto central de cada barra de error.

```python
layout = ReactiveMatrixLayout("EB", selection_model=selection).set_data(df)
layout.add_errorbars(
    'EB',
    x_col='x',
    y_col='y',
    yerr='yerr',            # opcional
    xerr='xerr',            # opcional
    interactive=True,
    selection_var='selected_error'
)
```

Click en un punto:
- `selected_error`: `DataFrame` con la(s) fila(s) original(es) asociada(s) a ese punto.

### 11. Hexbin (`hexbin`)

- **Método**: `add_hexbin`
- **Unidad de selección**: hexágono (bin de densidad).

```python
layout = ReactiveMatrixLayout("HX", selection_model=selection).set_data(df)
layout.add_hexbin(
    'HX',
    x_col='x',
    y_col='y',
    interactive=True,
    selection_var='selected_hex'
)
```

Click en un hexágono:
- `selected_hex`: `DataFrame` con todas las filas cuyos puntos caen en ese hexágono.

### 12. Parallel Coordinates, RadViz, Star Coordinates

- **Métodos**:
  - `add_parallel_coordinates`
  - `add_radviz`
  - `add_star_coordinates`
- **Unidad de selección**: líneas/puntos (según el gráfico).
- Selección está ya implementada; el patrón de uso es:

```python
layout = ReactiveMatrixLayout("PC", selection_model=selection).set_data(df)
layout.add_parallel_coordinates(
    'P',
    dimensions=['x1', 'x2', 'x3'],
    category_col='clase',
    # estos gráficos hoy se usan principalmente como enlazados;
    # cuando se usan como principales, la selección se maneja igual:
    # selection.get_items() -> DataFrame
)
```

### 13. Acceso a la selección desde Python

Para cualquier gráfico configurado como vista principal (`interactive=True`):

- **SelectionModel**:

```python
items = selection.get_items()   # lista de dicts o DataFrame
df_sel = items if hasattr(items, 'head') else pd.DataFrame(items)
```

- **Variables `selection_var`**:

```python
layout.add_barchart('B', category_col='dept', interactive=True, selection_var='selected_bar')

# Después de interactuar:
selected_bar   # DataFrame con la selección actual (si hay pandas)
```

BESTLIB intenta siempre:
- Convertir `payload.items` a `DataFrame` con `_items_to_dataframe`.
- Actualizar `SelectionModel`, `_selected_data` y cualquier `selection_var`
  con el `DataFrame` resultante cuando pandas está disponible.


