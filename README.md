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

```bash
# Instalar dependencias
pip install -r requirements.txt

# Instalar en modo desarrollo
pip install -e .
```

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

- **[CHANGELOG.md](CHANGELOG.md)** - Historial de cambios
- **[ANALISIS_ERRORES_Y_SOLUCION.md](ANALISIS_ERRORES_Y_SOLUCION.md)** - Análisis técnico
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
