# 📊 BESTLIB - Beautiful & Efficient Visualization Library

**BESTLIB** es una librería de visualización interactiva para Jupyter Notebooks que permite crear dashboards con layouts ASCII y gráficos D3.js.

> **✨ Versión 0.1.0** - Arquitectura modular estable con compatibilidad hacia atrás

## ✨ Características

- 🎨 **30+ tipos de gráficos** (scatter, bar, histogram, boxplot, heatmap, line, pie, violin, kde, etc.)
- 🔗 **Vistas enlazadas** - Sincronización automática entre gráficos
- ⚡ **Sistema reactivo** - Actualización automática sin re-ejecutar celdas
- 🖱️ **Interactividad** - Brush selection, click events, tooltips
- 📐 **Layouts ASCII** - Define la disposición de gráficos con texto
- 🐼 **Soporte pandas** - Trabaja directamente con DataFrames
- 🎯 **Comunicación bidireccional** - Python ↔ JavaScript en tiempo real
- 🏗️ **Arquitectura modular** - Código limpio y extensible

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

### Layout Estático Simple

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

### Layout Reactivo con Vistas Enlazadas

```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear modelo de selección compartido
selection = SelectionModel()

# Crear layout reactivo
layout = ReactiveMatrixLayout("SB", selection_model=selection)
df = pd.read_csv('examples/iris.csv')
layout.set_data(df)

# Scatter interactivo
layout.add_scatter('S', x_col='sepal_length', y_col='petal_length', 
                  category_col='species', interactive=True)

# Bar chart enlazado (se actualiza automáticamente al seleccionar en scatter)
layout.add_barchart('B', category_col='species', linked_to='S')

layout.display()
```

## 📚 Documentación

### Documentación Principal

- **[docs/API_PUBLICA.md](docs/API_PUBLICA.md)** - 📖 **API Pública Oficial** (LEER PRIMERO)
- **[COLAB_INSTALL.md](COLAB_INSTALL.md)** - Guía de instalación para Google Colab
- **[CHANGELOG.md](CHANGELOG.md)** - Historial de cambios
- **[ARQUITECTURA.md](ARQUITECTURA.md)** - Arquitectura del proyecto

### Ejemplos

- **[examples/demo_completo_bestlib.ipynb](examples/demo_completo_bestlib.ipynb)** - Demo completo con Iris
- **[examples/COLAB_INSTALLATION.ipynb](examples/COLAB_INSTALLATION.ipynb)** - Guía de instalación en Colab
- **[examples/test_completo_iris.ipynb](examples/test_completo_iris.ipynb)** - Tests completos

### ⚠️ Código Legacy (NO USAR)

Los siguientes módulos son **legacy** y serán eliminados en v0.2.0:

- ❌ `BESTLIB.matrix` - Usar `from BESTLIB import MatrixLayout` en su lugar
- ❌ `BESTLIB.reactive` - Usar `from BESTLIB import ReactiveMatrixLayout, SelectionModel`
- ❌ `BESTLIB.linked.LinkedViews` - Usar `ReactiveMatrixLayout`
- ❌ `BESTLIB.compat.*` - Usar API pública directamente

**Ver [AUDITORIA_LEGACY.md](AUDITORIA_LEGACY.md) para guía de migración.**

## ✅ Estado del Proyecto

- ✅ Sintaxis correcta en todos los módulos
- ✅ 30+ tipos de gráficos funcionando
- ✅ Sistema de vistas enlazadas operativo
- ✅ Sistema reactivo implementado
- ✅ Dataset de prueba incluido (iris.csv)
- ✅ Arquitectura modular estable
- ✅ API pública bien definida
- ✅ Compatibilidad hacia atrás mantenida

### Arquitectura

```
BESTLIB/
├── layouts/          # ✅ MatrixLayout y ReactiveMatrixLayout (MODULAR)
├── charts/           # ✅ 30+ tipos de gráficos (MODULAR)
├── data/             # ✅ Preparación y validación (MODULAR)
├── reactive/         # ✅ Sistema reactivo (MODULAR)
├── core/             # ✅ Comunicación y eventos (MODULAR)
├── render/           # ✅ Renderizado HTML/JS (MODULAR)
├── utils/            # ✅ Utilidades (MODULAR)
│
├── matrix.py         # ⚠️ LEGACY - Será eliminado en v0.2.0
├── reactive.py       # ⚠️ LEGACY - Será eliminado en v0.2.0
├── linked.py         # ⚠️ DEPRECATED - Usar ReactiveMatrixLayout
└── compat/           # ⚠️ DEPRECATED - Thin wrappers temporales
```

## 🤝 Contribuciones

Desarrollado por: Nahia Escalante, Alejandro, Max
