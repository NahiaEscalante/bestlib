# 📊 BESTLIB

> BestLib, the best lib for graphics - Interactive dashboards for Jupyter with D3.js

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange.svg)](https://jupyter.org/)

**BESTLIB** es una librería de visualización interactiva que te permite crear dashboards profesionales en Jupyter Notebooks usando layouts ASCII y gráficos D3.js. Diseñada para ser simple, poderosa y completamente interactiva.

## ✨ Características Principales

- 🎨 **30+ tipos de gráficos** - Scatter, bar, histogram, boxplot, heatmap, line, pie, violin, radviz, kde, polar y más
- 🔗 **Vistas enlazadas** - `ReactiveMatrixLayout` sincroniza automáticamente múltiples gráficos (LinkedViews legacy)
- ⚡ **Sistema reactivo** - Actualización automática sin re-ejecutar celdas
- 🖱️ **Interactividad completa** - Brush selection, click events, tooltips personalizables
- 📐 **Layouts ASCII** - Define la disposición de gráficos con texto simple
- 🐼 **Soporte pandas nativo** - Trabaja directamente con DataFrames sin conversiones

## 🚀 Instalación

```bash
pip install pybestlib
```

### Para Google Colab

```python
!pip install bestlib
```

**Nota:** Colab ya incluye las dependencias necesarias (`pandas`, `numpy`, `ipywidgets`).

## 💡 Inicio Rápido

```python
from BESTLIB import MatrixLayout
import pandas as pd

# Cargar datos
df = pd.read_csv('iris.csv')

# Crear scatter plot interactivo
MatrixLayout.map_scatter('S', df, 
                         x_col='sepal_length', 
                         y_col='petal_length',
                         category_col='species',
                         interactive=True)

# Mostrar dashboard
layout = MatrixLayout("S")
layout.display()
```

### Ejemplo con Múltiples Gráficos

```python
from BESTLIB import ReactiveMatrixLayout
import pandas as pd

df = pd.read_csv('iris.csv')
layout = ReactiveMatrixLayout("""
SH
HB
""")

# Scatter plot con selección
layout.add_scatter('S', df, x_col='sepal_length', y_col='petal_length', 
                   category_col='species', interactive=True)

# Histograma enlazado
layout.add_histogram('H', df, col='petal_length', interactive=True)

# Bar chart
layout.add_barchart('B', df, x_col='species', y_col='sepal_length')

layout.display()
```

## 📊 Tipos de Gráficos Disponibles

### Gráficos Básicos

| Gráfico | Método | Descripción |
|---------|--------|-------------|
| **Scatter Plot** | `add_scatter()` | Dispersión con brush selection |
| **Bar Chart** | `add_barchart()` | Barras verticales simples |
| **Grouped Bar Chart** | `add_grouped_barchart()` | Barras agrupadas por categoría |
| **Horizontal Bar** | `add_horizontal_bar()` | Barras horizontales |
| **Histogram** | `add_histogram()` | Distribuciones con bins configurables |
| **Boxplot** | `add_boxplot()` | Diagramas de caja por categoría |
| **Line Chart** | `add_line()` | Series temporales y múltiples líneas |
| **Line Plot** | `add_line_plot()` | Gráfico de líneas alternativo |
| **Pie Chart** | `add_pie()` | Gráficos circulares |
| **Violin Plot** | `add_violin()` | Distribuciones de densidad |

### Gráficos Avanzados

| Gráfico | Método | Descripción |
|---------|--------|-------------|
| **Heatmap** | `add_heatmap()` | Mapas de calor |
| **Correlation Heatmap** | `add_correlation_heatmap()` | Matriz de correlación |
| **Hexbin** | `add_hexbin()` | Dispersión con bins hexagonales |
| **Hist2D** | `add_hist2d()` | Histograma 2D (densidad bivariada) |
| **KDE** | `add_kde()` | Estimación de densidad kernel |
| **Distplot** | `add_distplot()` | Histograma + KDE + rug plot |
| **Rug Plot** | `add_rug()` | Marcadores marginales |
| **QQ Plot** | `add_qqplot()` | Gráfico cuantil-cuantil |
| **ECDF** | `add_ecdf()` | Función de distribución acumulativa empírica |
| **Ridgeline** | `add_ridgeline()` | Distribuciones apiladas |
| **Errorbars** | `add_errorbars()` | Barras de error |
| **Fill Between** | `add_fill_between()` | Área entre dos curvas |
| **Ribbon** | `add_ribbon()` | Cinta entre series |
| **Step Plot** | `add_step()` | Gráfico de escalones |

### Gráficos Especializados

| Gráfico | Método | Descripción |
|---------|--------|-------------|
| **RadViz** | `add_radviz()` | Visualización radial multidimensional |
| **Star Coordinates** | `add_star_coordinates()` | Coordenadas estelares |
| **Parallel Coordinates** | `add_parallel_coordinates()` | Coordenadas paralelas |
| **Polar** | `add_polar()` | Gráfico polar/radial |
| **Funnel** | `add_funnel()` | Gráfico de embudo |
| **Confusion Matrix** | `add_confusion_matrix()` | Matriz de confusión (ML) |

## 🎯 Casos de Uso

- **Análisis exploratorio de datos** - Visualiza rápidamente tus DataFrames
- **Dashboards interactivos** - Crea interfaces de análisis sin HTML/JavaScript
- **Presentaciones dinámicas** - Gráficos que responden a interacciones del usuario
- **Enseñanza de datos** - Visualizaciones interactivas para educación

## 🔧 Dependencias

BESTLIB funciona con dependencias opcionales. Para funcionalidad completa, instala:

```bash
pip install ipython ipywidgets pandas numpy
```

**Opcional:** `scikit-learn` (solo para `add_confusion_matrix()`)

### 🛠️ Assets JS

El código fuente de `matrix.js` vive en `js/src/index.js`. Para regenerar el bundle:

```bash
cd js
npm install
npm run build
```

### 📦 Releases

Para publicar una versión ejecuta los pasos descritos en [`docs/RELEASE.md`](docs/RELEASE.md).

## 🤝 Contribuciones

Desarrollado por **Nahia Escalante, Alejandro Rojas y Max Antúnez**

¿Encontraste un bug o tienes una sugerencia? ¡Abre un issue!

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

---

**¿Listo para crear visualizaciones increíbles?** ⚡ `pip install bestlib` y comienza ahora.
