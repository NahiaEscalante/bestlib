# 📊 Ejemplos de Uso - Nuevos Gráficos BESTLIB

Este documento contiene ejemplos completos y listos para ejecutar de los 6 nuevos gráficos agregados a BESTLIB.

---

## 📦 Instalación en Google Colab

```python
# Instalar BESTLIB desde el repositorio
!git clone https://github.com/NahiaEscalante/bestlib.git
%cd bestlib
!pip install -e .
```

---

## 📚 Preparación de Datos

```python
import pandas as pd
import numpy as np

# Cargar dataset Iris
df = pd.read_csv('iris.csv')  # O usar: from sklearn.datasets import load_iris

# Crear datos sintéticos adicionales para algunos gráficos
np.random.seed(42)
n = 100
df_synthetic = pd.DataFrame({
    'x': np.linspace(0, 10, n),
    'y1': np.sin(np.linspace(0, 10, n)) + np.random.normal(0, 0.1, n),
    'y2': np.cos(np.linspace(0, 10, n)) + np.random.normal(0, 0.1, n),
    'y': np.sin(np.linspace(0, 10, n)) + np.random.normal(0, 0.1, n),
    'yerr': np.random.uniform(0.1, 0.3, n),
    'category': np.random.choice(['A', 'B', 'C'], n)
})
```

---

## 1️⃣ Line Plot Completo

### Ejemplo Individual

```python
from BESTLIB.layouts import MatrixLayout

# Crear datos de series temporales
import pandas as pd
import numpy as np

np.random.seed(42)
dates = pd.date_range('2024-01-01', periods=50, freq='D')
df_line = pd.DataFrame({
    'date': dates,
    'value1': np.cumsum(np.random.randn(50)) + 100,
    'value2': np.cumsum(np.random.randn(50)) + 120,
    'series': ['A'] * 25 + ['B'] * 25
})

# Crear layout
layout = MatrixLayout("L")

# Agregar line plot
layout.map_line_plot('L', df_line, 
                     x_col='date', 
                     y_col='value1',
                     series_col='series',
                     xLabel='Fecha',
                     yLabel='Valor',
                     markers=True,
                     strokeWidth=2)

layout.display()
```

### Ejemplo con ReactiveMatrixLayout

```python
from BESTLIB.layouts import ReactiveMatrixLayout
from BESTLIB import SelectionModel

layout = ReactiveMatrixLayout("L", selection_model=SelectionModel())
layout.set_data(df_line)

layout.add_line_plot('L', 
                     x_col='date', 
                     y_col='value1',
                     series_col='series',
                     xLabel='Fecha',
                     yLabel='Valor',
                     markers=True)

layout.display()
```

---

## 2️⃣ Horizontal Bar Chart

### Ejemplo Individual

```python
from BESTLIB.layouts import MatrixLayout

# Usar datos de Iris
layout = MatrixLayout("B")

# Contar especies
layout.map_horizontal_bar('B', df, 
                          category_col='species',
                          xLabel='Count',
                          yLabel='Species',
                          color='#3498db')

layout.display()
```

### Ejemplo con ReactiveMatrixLayout

```python
from BESTLIB.layouts import ReactiveMatrixLayout
from BESTLIB import SelectionModel

layout = ReactiveMatrixLayout("BS", selection_model=SelectionModel())
layout.set_data(df)

# Scatter plot principal
layout.add_scatter('S', x_col='sepal_length', y_col='sepal_width', 
                   color_col='species', interactive=True)

# Horizontal bar enlazado
layout.add_horizontal_bar('B', 
                          category_col='species',
                          linked_to='S',
                          xLabel='Count',
                          yLabel='Species')

layout.display()
```

---

## 3️⃣ Hexbin Chart

### Ejemplo Individual

```python
from BESTLIB.layouts import MatrixLayout

layout = MatrixLayout("H")

# Hexbin de sepal_length vs petal_width
layout.map_hexbin('H', df,
                  x_col='sepal_length',
                  y_col='petal_width',
                  xLabel='Sepal Length',
                  yLabel='Petal Width',
                  bins=20,
                  colorScale='Blues')

layout.display()
```

### Ejemplo con ReactiveMatrixLayout

```python
from BESTLIB.layouts import ReactiveMatrixLayout
from BESTLIB import SelectionModel

layout = ReactiveMatrixLayout("SH", selection_model=SelectionModel())
layout.set_data(df)

layout.add_scatter('S', x_col='sepal_length', y_col='sepal_width', 
                   color_col='species', interactive=True)

layout.add_hexbin('H', 
                  x_col='sepal_length',
                  y_col='petal_width',
                  linked_to='S',
                  bins=20,
                  colorScale='Viridis')

layout.display()
```

---

## 4️⃣ Errorbars Chart

### Ejemplo Individual

```python
from BESTLIB.layouts import MatrixLayout

# Crear datos con errores
import pandas as pd
import numpy as np

np.random.seed(42)
df_errors = pd.DataFrame({
    'x': range(10),
    'y': np.random.randn(10).cumsum() + 10,
    'yerr': np.random.uniform(0.5, 2.0, 10),
    'xerr': np.random.uniform(0.2, 0.5, 10)
})

layout = MatrixLayout("E")

layout.map_errorbars('E', df_errors,
                     x_col='x',
                     y_col='y',
                     yerr='yerr',
                     xerr='xerr',
                     xLabel='X',
                     yLabel='Y',
                     color='#e74c3c',
                     capSize=5)

layout.display()
```

### Ejemplo con ReactiveMatrixLayout

```python
from BESTLIB.layouts import ReactiveMatrixLayout
from BESTLIB import SelectionModel

layout = ReactiveMatrixLayout("SE", selection_model=SelectionModel())
layout.set_data(df_errors)

layout.add_scatter('S', x_col='x', y_col='y', interactive=True)

layout.add_errorbars('E',
                     x_col='x',
                     y_col='y',
                     yerr='yerr',
                     linked_to='S',
                     capSize=5)

layout.display()
```

---

## 5️⃣ Fill Between Chart

### Ejemplo Individual

```python
from BESTLIB.layouts import MatrixLayout

# Usar datos sintéticos con dos series Y
layout = MatrixLayout("F")

layout.map_fill_between('F', df_synthetic,
                        x_col='x',
                        y1='y1',
                        y2='y2',
                        xLabel='X',
                        yLabel='Y',
                        color='#3498db',
                        opacity=0.3,
                        showLines=True)

layout.display()
```

### Ejemplo con ReactiveMatrixLayout

```python
from BESTLIB.layouts import ReactiveMatrixLayout
from BESTLIB import SelectionModel

layout = ReactiveMatrixLayout("SF", selection_model=SelectionModel())
layout.set_data(df_synthetic)

layout.add_scatter('S', x_col='x', y_col='y', interactive=True)

layout.add_fill_between('F',
                        x_col='x',
                        y1='y1',
                        y2='y2',
                        linked_to='S',
                        opacity=0.3)

layout.display()
```

---

## 6️⃣ Step Plot

### Ejemplo Individual

```python
from BESTLIB.layouts import MatrixLayout

# Crear datos escalonados
import pandas as pd
import numpy as np

np.random.seed(42)
df_step = pd.DataFrame({
    'x': np.linspace(0, 10, 20),
    'y': np.cumsum(np.random.choice([-1, 0, 1], 20))
})

layout = MatrixLayout("S")

layout.map_step('S', df_step,
                x_col='x',
                y_col='y',
                xLabel='X',
                yLabel='Y',
                stepType='step',  # 'step', 'stepBefore', 'stepAfter'
                color='#2ecc71',
                strokeWidth=2)

layout.display()
```

### Ejemplo con ReactiveMatrixLayout

```python
from BESTLIB.layouts import ReactiveMatrixLayout
from BESTLIB import SelectionModel

layout = ReactiveMatrixLayout("SS", selection_model=SelectionModel())
layout.set_data(df_step)

layout.add_scatter('S', x_col='x', y_col='y', interactive=True)

layout.add_step('S',
                x_col='x',
                y_col='y',
                linked_to='S',
                stepType='stepAfter')

layout.display()
```

---

## 🎨 Ejemplo Completo: Matriz con TODOS los Nuevos Gráficos

```python
from BESTLIB.layouts import ReactiveMatrixLayout
from BESTLIB import SelectionModel
import pandas as pd
import numpy as np

# Preparar datos
np.random.seed(42)

# Datos base de Iris
df = pd.read_csv('iris.csv')  # O cargar desde sklearn

# Datos sintéticos para fill_between y errorbars
n = 50
df_synthetic = pd.DataFrame({
    'x': np.linspace(0, 10, n),
    'y1': np.sin(np.linspace(0, 10, n)) + np.random.normal(0, 0.1, n),
    'y2': np.cos(np.linspace(0, 10, n)) + np.random.normal(0, 0.1, n),
    'y': np.sin(np.linspace(0, 10, n)) + np.random.normal(0, 0.1, n),
    'yerr': np.random.uniform(0.1, 0.3, n)
})

# Combinar datos
df_combined = pd.concat([
    df[['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'species']].assign(type='iris'),
    df_synthetic.assign(type='synthetic')
], ignore_index=True)

# Crear layout con matriz 2x3
layout = ReactiveMatrixLayout("""
LH
ES
BF
""", selection_model=SelectionModel())

layout.set_data(df_combined)

# L = Line Plot
layout.add_line_plot('L', 
                     x_col='sepal_length', 
                     y_col='sepal_width',
                     xLabel='Sepal Length',
                     yLabel='Sepal Width',
                     markers=True,
                     strokeWidth=2)

# H = Hexbin
layout.add_hexbin('H',
                  x_col='sepal_length',
                  y_col='petal_width',
                  xLabel='Sepal Length',
                  yLabel='Petal Width',
                  bins=15,
                  colorScale='Blues')

# E = Errorbars (usar datos sintéticos)
df_errors = pd.DataFrame({
    'x': range(10),
    'y': np.random.randn(10).cumsum() + 10,
    'yerr': np.random.uniform(0.5, 2.0, 10)
})
layout.set_data(df_errors)
layout.add_errorbars('E',
                     x_col='x',
                     y_col='y',
                     yerr='yerr',
                     xLabel='X',
                     yLabel='Y',
                     capSize=5)

# S = Step Plot
df_step = pd.DataFrame({
    'x': np.linspace(0, 10, 20),
    'y': np.cumsum(np.random.choice([-1, 0, 1], 20))
})
layout.set_data(df_step)
layout.add_step('S',
                x_col='x',
                y_col='y',
                xLabel='X',
                yLabel='Y',
                stepType='step',
                color='#2ecc71')

# B = Horizontal Bar
layout.set_data(df)
layout.add_horizontal_bar('B',
                         category_col='species',
                         xLabel='Count',
                         yLabel='Species',
                         color='#3498db')

# F = Fill Between
layout.set_data(df_synthetic)
layout.add_fill_between('F',
                        x_col='x',
                        y1='y1',
                        y2='y2',
                        xLabel='X',
                        yLabel='Y',
                        color='#9b59b6',
                        opacity=0.3)

# Mostrar
layout.display()
```

---

## 📝 Notas Importantes

### Parámetros Comunes

Todos los gráficos soportan:
- `xLabel`, `yLabel`: Etiquetas de ejes
- `axes`: Mostrar/ocultar ejes (por defecto `True`)
- `figsize`: Tamaño del gráfico
- `color`: Color principal
- `interactive`: Habilita interactividad (donde aplica)

### Parámetros Específicos

#### Line Plot
- `series_col`: Columna para múltiples series
- `markers`: Mostrar marcadores en puntos (boolean)
- `strokeWidth`: Grosor de línea (por defecto 2)

#### Horizontal Bar
- `category_col`: Columna de categorías (requerido)
- `value_col`: Columna de valores (opcional, cuenta si se omite)

#### Hexbin
- `bins`: Número de bins (por defecto 20)
- `colorScale`: Escala de colores ('Blues', 'Reds', 'Viridis')

#### Errorbars
- `yerr`: Columna de error en Y (opcional)
- `xerr`: Columna de error en X (opcional)
- `capSize`: Tamaño de las caps (por defecto 5)

#### Fill Between
- `y1`: Primera línea Y (requerido)
- `y2`: Segunda línea Y (requerido)
- `opacity`: Opacidad del área (por defecto 0.3)
- `showLines`: Mostrar líneas de borde (por defecto `True`)

#### Step Plot
- `stepType`: Tipo de escalonado ('step', 'stepBefore', 'stepAfter')
- `strokeWidth`: Grosor de línea (por defecto 2)

---

## ✅ Validaciones

Todos los gráficos validan:
- ✅ Columnas requeridas existen
- ✅ Datos numéricos cuando aplica
- ✅ Mensajes de error claros
- ✅ Manejo de datos vacíos

---

## 🎯 Compatibilidad

- ✅ **MatrixLayout**: Todos los gráficos funcionan con `map_*` methods
- ✅ **ReactiveMatrixLayout**: Todos los gráficos funcionan con `add_*` methods
- ✅ **Linked Views**: Todos soportan `linked_to` para vistas enlazadas
- ✅ **Google Colab**: Funciona perfectamente
- ✅ **Jupyter Notebook/Lab**: Funciona perfectamente

---

## 🔍 Solución de Problemas

### Error: "category_col es requerido"
- Asegúrate de pasar `category_col` para horizontal bar

### Error: "y1 e y2 son requeridos"
- Para fill_between, debes especificar ambas columnas Y

### Error: "Columna 'x' no encontrada"
- Verifica que las columnas especificadas existan en el DataFrame

### Gráfico no se muestra
- Asegúrate de llamar `layout.display()` al final
- Verifica que los datos no estén vacíos

---

**¡Listo para usar!** 🎉

