# 📊 BESTLIB - Beautiful & Efficient Visualization Library

**BESTLIB** es una librería de visualización interactiva para Jupyter Notebooks que permite crear dashboards con layouts ASCII y gráficos D3.js.

## ✨ Características

- 🎨 **11+ tipos de gráficos** (scatter, bar, histogram, boxplot, heatmap, line, pie, violin, radviz, etc.)
- 🔗 **Vistas enlazadas** - Sincronización automática entre gráficos
- ⚡ **Sistema reactivo** - Actualización automática sin re-ejecutar celdas
- 🖱️ **Interactividad** - Brush selection, click events, tooltips
- 📐 **Layouts ASCII** - Define la disposición de gráficos con texto
- 🐼 **Soporte pandas** - Trabaja directamente con DataFrames
- 🎯 **Comunicación bidireccional** - Python ↔ JavaScript en tiempo real

## 📦 Instalación

### Para Jupyter Notebook/Lab Local

```bash
# Instalar desde GitHub
pip install --upgrade --force-reinstall git+https://github.com/NahiaEscalante/bestlib.git@widget_mod

# O instalar en modo desarrollo
pip install -e .
```

### Para Google Colab ⚡

**⚠️ Importante:** Google Colab ya tiene las dependencias necesarias. Instala BESTLIB sin dependencias:

```python
# Instalación en Colab (sin dependencias para evitar conflictos)
!pip install --upgrade --no-deps git+https://github.com/NahiaEscalante/bestlib.git@widget_mod
```

**Nota:** Colab ya tiene `pandas`, `numpy`, `ipython`, `jupyter`, e `ipywidgets` instalados.

**📚 Guía completa:** Ver [COLAB_INSTALL.md](COLAB_INSTALL.md) o [examples/COLAB_INSTALLATION.ipynb](examples/COLAB_INSTALLATION.ipynb)

### Dependencias Requeridas

BESTLIB requiere las siguientes dependencias (deben instalarse manualmente si no están presentes):

- `ipython` (cualquier versión >= 7.0)
- `ipywidgets` (cualquier versión >= 7.0)
- `pandas` (cualquier versión >= 1.3.0)
- `numpy` (cualquier versión >= 1.20.0)

**Nota:** El código maneja las importaciones de forma opcional, por lo que BESTLIB funcionará incluso si algunas dependencias no están instaladas (con funcionalidades limitadas).

## 🚀 Inicio Rápido

```python
from BESTLIB import MatrixLayout
import pandas as pd

# Cargar datos
df = pd.read_csv('examples/iris.csv')

# Crear scatter plot
MatrixLayout.map_scatter('S', df, 
                         x_col='sepal_length', 
                         y_col='petal_length',
                         category_col='species',
                         interactive=True)

layout = MatrixLayout("S")
layout.display()
```

## 📚 Documentación

- **[COLAB_INSTALL.md](COLAB_INSTALL.md)** - Guía de instalación para Google Colab
- **[CHANGELOG.md](CHANGELOG.md)** - Historial de cambios
- **[ANALISIS_ERRORES_Y_SOLUCION.md](ANALISIS_ERRORES_Y_SOLUCION.md)** - Análisis técnico
- **[examples/demo_completo_bestlib.ipynb](examples/demo_completo_bestlib.ipynb)** - Demo completo con Iris
- **[examples/COLAB_INSTALLATION.ipynb](examples/COLAB_INSTALLATION.ipynb)** - Guía de instalación en Colab
- **[examples/test_completo_iris.ipynb](examples/test_completo_iris.ipynb)** - Tests completos

## ✅ Estado del Proyecto

- ✅ Sintaxis correcta en todos los módulos
- ✅ 11+ tipos de gráficos funcionando
- ✅ Sistema de vistas enlazadas operativo
- ✅ Sistema reactivo implementado
- ✅ Dataset de prueba incluido (iris.csv)
- ✅ Tests completos disponibles

## 🤝 Contribuciones

Desarrollado por: Nahia Escalante, Alejandro, Max
