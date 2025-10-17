# 🚀 BESTLIB - Referencia Rápida

## Importar

```python
from BESTLIB.matrix import MatrixLayout
MatrixLayout.set_debug(True)  # Opcional: ver mensajes
```

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
