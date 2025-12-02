# 🚀 BESTLIB - Referencia Rápida

## Instalación

### Jupyter Notebook / JupyterLab (Local)

```bash
pip install pybestlib
```

### Google Colab

**IMPORTANTE**: En Colab, usa `--no-deps` para evitar conflictos:

```python
!pip install --no-deps pybestlib
```

O desde GitHub:

```python
!pip install --no-deps git+https://github.com/NahiaEscalante/bestlib.git
```

## Importar

```python
from BESTLIB.layouts.matrix import MatrixLayout
from BESTLIB.layouts.reactive import ReactiveMatrixLayout
from BESTLIB.reactive.selection import SelectionModel

MatrixLayout.set_debug(True)  # Opcional: ver mensajes
```

> **Nota**: El módulo legacy `BESTLIB.matrix` y `LinkedViews` están deprecados. Usa `BESTLIB.layouts.matrix.MatrixLayout` y `ReactiveMatrixLayout` en su lugar.

## 1️⃣ Elementos Visuales Simples

### Círculo
```python
MatrixLayout.map({
    'C': {
        'shape': 'circle',
        'color': '#e74c3c',
        'size': 40,
        'title': 'Mi Círculo'
    }
})
layout = MatrixLayout("C")
layout
```

### Rectángulo
```python
MatrixLayout.map({
    'R': {
        'shape': 'rect',
        'color': '#3498db',
        'width': 80,
        'height': 50,
        'borderRadius': 5
    }
})
layout = MatrixLayout("R")
layout
```

### Línea
```python
MatrixLayout.map({
    'L': {
        'shape': 'line',
        'color': '#2ecc71',
        'strokeWidth': 5
    }
})
layout = MatrixLayout("L")
layout
```

## 2️⃣ Gráficos D3

### Bar Chart
```python
data = [
    {"category": "A", "value": 10},
    {"category": "B", "value": 20}
]

MatrixLayout.map({
    'B': {
        "type": "bar",
        "data": data,
        "color": "#4a90e2",
        "interactive": True
    }
})

layout = MatrixLayout("BBB")
layout
```

### Scatter Plot
### Grouped/Nested Bar Chart
```python
# main_col: categoría principal, sub_col: subcategoría, value_col opcional (si se omite, cuenta)
layout = ReactiveMatrixLayout("GB", selection_model=SelectionModel()).set_data(df)
layout.add_scatter('G', df, x_col='x', y_col='y', interactive=True)
layout.add_grouped_barchart('B', main_col='region', sub_col='producto', value_col='ventas', linked_to='G', axes=True)
layout.display()
```

### Heatmap
```python
layout = ReactiveMatrixLayout("SH", selection_model=SelectionModel()).set_data(df_long)
layout.add_scatter('S', df_long, x_col='valX', y_col='valY', interactive=True)
layout.add_heatmap('H', x_col='col', y_col='row', value_col='val', linked_to='S', axes=True)
layout.display()
```

### Correlation Heatmap
```python
layout = ReactiveMatrixLayout("CH", selection_model=SelectionModel()).set_data(df)
layout.add_scatter('C', df, x_col='x', y_col='y', interactive=True)
layout.add_correlation_heatmap('H', linked_to='C', colorScale='diverging')
layout.display()
```

### Line (multi-series) con hover sincronizado
```python
layout = ReactiveMatrixLayout("SL", selection_model=SelectionModel()).set_data(df)
layout.add_scatter('S', df, x_col='x', y_col='y', interactive=True)
layout.add_line('L', x_col='time', y_col='value', series_col='serie', linked_to='S')
layout.display()
```

### Pie / Donut Interactivo
```python
layout = ReactiveMatrixLayout("SP", selection_model=SelectionModel()).set_data(df)
layout.add_scatter('S', df, x_col='x', y_col='y', category_col='cat', interactive=True)
layout.add_pie('P', category_col='cat', value_col='val', donut=True, innerRadius=60, linked_to='S', interactive=True)
layout.display()
```

### Violin Plot
```python
layout = ReactiveMatrixLayout("SV", selection_model=SelectionModel()).set_data(df)
layout.add_scatter('S', df, x_col='x', y_col='y', interactive=True)
layout.add_violin('V', value_col='salario', category_col='dept', bins=20, linked_to='S')
layout.display()
```

### RadViz / Star Coordinates
```python
layout = ReactiveMatrixLayout("SR", selection_model=SelectionModel()).set_data(df)
layout.add_scatter('S', df, x_col='x', y_col='y', interactive=True)
layout.add_radviz('R', features=['f1','f2','f3','f4'], class_col='label', linked_to='S')
layout.display()
```
```python
data = [
    {"x": 1, "y": 2, "label": "P1"},
    {"x": 3, "y": 4, "label": "P2"}
]

MatrixLayout.map({
    'S': {
        "type": "scatter",
        "data": data,
        "pointRadius": 5,
        "interactive": True,
        "zoom": True
    }
})

layout = MatrixLayout("SSS")
layout
```

## 3️⃣ Selección de Datos

### Callback Simple
```python
selected = []

def on_select(payload):
    global selected
    selected = payload.get('items', [])
    print(f"Seleccionados: {len(selected)}")

layout.on('select', on_select)
```

### Callback con Análisis
```python
def on_select(payload):
    items = payload.get('items', [])
    if items:
        total = sum(item['value'] for item in items)
        avg = total / len(items)
        print(f"Total: {total}, Promedio: {avg}")

layout.on('select', on_select)
```

### Usar Datos en Otra Celda
```python
# En una celda:
selected_data = []
layout.on('select', lambda p: selected_data.append(p['items']))

# En otra celda:
import pandas as pd
df = pd.DataFrame(selected_data[-1] if selected_data else [])
print(df)
```

## 4️⃣ Dashboard

```python
MatrixLayout.map({
    'T': '<h2 style="text-align:center;">📊 Dashboard</h2>',
    'B': {"type": "bar", "data": [...], "interactive": True},
    'S': {"type": "scatter", "data": [...], "interactive": True},
    'I': '<div>Info</div>',
    '__merge__': True
})

dashboard = MatrixLayout("""
TTTTTT
BBBSSS
BBBSSS
IIIIII
""")

dashboard.on('select', lambda p: print(p))
dashboard
```

## 5️⃣ Eventos

| Evento | Trigger | Gráficos |
|--------|---------|----------|
| `select` | Arrastrar para seleccionar | bar, scatter |
| `point_click` | Click en punto | scatter |

## 6️⃣ Propiedades de Elementos

### Círculo
```python
{
    'shape': 'circle',
    'color': '#color',
    'size': 40,
    'opacity': 0.8,
    'stroke': '#000',
    'strokeWidth': 2,
    'title': 'Texto'
}
```

### Rectángulo
```python
{
    'shape': 'rect',
    'color': '#color',
    'width': 80,
    'height': 50,
    'borderRadius': 5,
    'opacity': 0.8,
    'stroke': '#000',
    'strokeWidth': 2
}
```

### Bar Chart
```python
{
    "type": "bar",
    "data": [{"category": "A", "value": 10}],
    "color": "#4a90e2",
    "hoverColor": "#357abd",
    "interactive": True,
    "axes": True
}
```

### Scatter Plot
```python
{
    "type": "scatter",
    "data": [{"x": 1, "y": 2, "label": "P1"}],
    "color": "#e74c3c",
    "pointRadius": 5,
    "interactive": True,
    "zoom": True,
    "axes": True
}
```

## 7️⃣ Debug

```python
# Activar
MatrixLayout.set_debug(True)

# Ver estado
status = MatrixLayout.get_status()
print(status)

# Desactivar
MatrixLayout.set_debug(False)
```

## 8️⃣ Merge de Celdas

```python
# Merge específico
MatrixLayout.map({
    'A': '<div>Grande</div>',
    '__merge__': ['A']
})

layout = MatrixLayout("""
AAA
AAA
""")

# Merge todo
MatrixLayout.map({
    'A': 'Celda A',
    'B': 'Celda B',
    '__merge__': True
})

layout = MatrixLayout("""
AAABBB
AAABBB
""")
```

## 9️⃣ Callbacks Múltiples

```python
layout = MatrixLayout("SSS")

# Encadenar
layout.on('select', callback1)\
      .on('point_click', callback2)

# O individual
layout.on('select', callback1)
layout.on('point_click', callback2)
```

## 🔟 Template Completo

```python
from BESTLIB.matrix import MatrixLayout

# Configurar
MatrixLayout.set_debug(True)

# Datos
bar_data = [{"category": "A", "value": 10}]
scatter_data = [{"x": 1, "y": 2}]

# Mapping
MatrixLayout.map({
    'T': '<h2>Título</h2>',
    'B': {"type": "bar", "data": bar_data, "interactive": True},
    'S': {"type": "scatter", "data": scatter_data, "interactive": True},
    'C': {'shape': 'circle', 'color': '#e74c3c'},
    '__merge__': True
})

# Layout
layout = MatrixLayout("""
TTTTTT
BBBSSS
BBBSSS
C....C
""")

# Variables de estado
bar_selection = []
scatter_selection = []

# Callbacks
def on_select(payload):
    global bar_selection, scatter_selection
    if payload['type'] == 'bar':
        bar_selection = payload['items']
    elif payload['type'] == 'scatter':
        scatter_selection = payload['items']
    print(f"Bar: {len(bar_selection)}, Scatter: {len(scatter_selection)}")

layout.on('select', on_select)

# Mostrar
layout
```

## 📚 Más Información

- **Demo Completo**: `examples/demo_completo.ipynb`
- **Documentación**: `docs/README.md`
- **Ejemplos**: carpeta `examples/`

---

**¡Listo para crear visualizaciones interactivas! 🎉**
