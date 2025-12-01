# 📊 BESTLIB v2

**Beautiful & Efficient Visualization Library** - Crea dashboards interactivos en Jupyter Notebooks con layouts ASCII y gráficos D3.js.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Características

- 🎨 **30+ tipos de gráficos** - scatter, bar, line, histogram, boxplot, heatmap, violin, kde, y más
- 🔗 **Vistas enlazadas** - Sincronización automática entre gráficos
- ⚡ **Sistema reactivo** - Actualización sin re-ejecutar celdas
- 🖱️ **Interactividad completa** - Brush selection, click events, tooltips
- 📐 **Layouts ASCII** - Define dashboards con texto simple
- 🐼 **Integración pandas** - Trabaja directamente con DataFrames
- 🎯 **Comunicación bidireccional** - Python ↔ JavaScript en tiempo real

## 📦 Instalación

### Jupyter Notebook/Lab Local

```bash
pip install git+https://github.com/NahiaEscalante/bestlib.git@v2
```

### Google Colab

```python
!pip install --no-deps git+https://github.com/NahiaEscalante/bestlib.git@v2
```

### Instalación con todas las dependencias

```bash
pip install "bestlib[full]" @ git+https://github.com/NahiaEscalante/bestlib.git@v2
```

## 🚀 Inicio Rápido

### Ejemplo Básico

```python
import bestlib
import pandas as pd

# Cargar datos
df = pd.read_csv('data.csv')

# Crear dashboard con layout ASCII
layout = bestlib.MatrixLayout('''
    scatter | bar
    --------+----
    heatmap | pie
''')

# Agregar gráficos
layout['scatter'] = {'type': 'scatter', 'data': df, 'x_col': 'x', 'y_col': 'y'}
layout['bar'] = {'type': 'bar', 'data': df, 'x_col': 'category', 'y_col': 'value'}
layout['heatmap'] = {'type': 'heatmap', 'data': df}
layout['pie'] = {'type': 'pie', 'data': df, 'values_col': 'value', 'labels_col': 'category'}

# Renderizar
layout.render()
```

### Dashboard Reactivo con Vistas Enlazadas

```python
from bestlib import ReactiveMatrixLayout

# Crear layout reactivo
layout = ReactiveMatrixLayout('''
    scatter | histogram
    --------+---------
    boxplot | bar
''', link_all=True)  # Enlace automático

# Los gráficos se sincronizan automáticamente
layout['scatter'] = {'type': 'scatter', 'data': df, 'x_col': 'x', 'y_col': 'y'}
layout['histogram'] = {'type': 'histogram', 'data': df, 'column': 'value'}
layout['boxplot'] = {'type': 'boxplot', 'data': df, 'column': 'value'}
layout['bar'] = {'type': 'bar', 'data': df, 'x_col': 'category'}

layout.render()

# Seleccionar datos en un gráfico actualiza todos los demás automáticamente
```

## 📚 Tipos de Gráficos Disponibles

### Básicos
- `scatter` - Diagrama de dispersión
- `bar` - Gráfico de barras
- `line` - Gráfico de líneas
- `histogram` - Histograma
- `boxplot` - Diagrama de caja
- `pie` - Gráfico circular
- `heatmap` - Mapa de calor

### Estadísticos
- `violin` - Gráfico de violín
- `kde` - Estimación de densidad kernel
- `ridgeline` - Gráfico ridgeline
- `qqplot` - Q-Q plot
- `ecdf` - Función de distribución empírica
- `distplot` - Distribución con KDE

### Avanzados
- `polar` - Gráfico polar
- `funnel` - Gráfico embudo
- `ribbon` - Gráfico cinta
- `hexbin` - Hexbin plot
- `hist2d` - Histograma 2D
- `parallel_coordinates` - Coordenadas paralelas
- `radviz` - RadViz
- `star_coordinates` - Coordenadas estrella

### Otros
- `grouped_bar` - Barras agrupadas
- `horizontal_bar` - Barras horizontales
- `errorbars` - Barras de error
- `fill_between` - Relleno entre líneas
- `step_plot` - Gráfico escalonado
- `rug` - Rug plot

Ver todos los tipos:
```python
import bestlib
print(bestlib.list_chart_types())
```

## 🔗 Vistas Enlazadas

```python
from bestlib import ReactiveMatrixLayout

layout = ReactiveMatrixLayout('''
    A | B
    --+--
    C | D
''')

# Enlace manual
layout.link_views(['A', 'B'])  # A y B sincronizados
layout.link_views(['C', 'D'])  # C y D sincronizados

# O enlace automático de todos
layout = ReactiveMatrixLayout(..., link_all=True)
```

## 🎨 Personalización

```python
layout['scatter'] = {
    'type': 'scatter',
    'data': df,
    'x_col': 'x',
    'y_col': 'y',
    'color': '#ff6b6b',
    'size': 6,
    'opacity': 0.7,
    'title': 'Mi Scatter Plot',
    'xlabel': 'Eje X',
    'ylabel': 'Eje Y',
    'width': 400,
    'height': 300,
}
```

## 📖 Documentación

- [Guía completa](docs/)
- [Ejemplos](examples/)
- [API Reference](docs/api.md)

## 🤝 Contribuir

Las contribuciones son bienvenidas. Ver [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [D3.js](https://d3js.org/) - Visualizaciones JavaScript
- [IPyWidgets](https://ipywidgets.readthedocs.io/) - Widgets interactivos
- Comunidad Python y Jupyter

---

Hecho con ❤️ por [Nahia Escalante](https://github.com/NahiaEscalante)
