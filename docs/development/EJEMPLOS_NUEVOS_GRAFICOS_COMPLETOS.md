# 📊 Ejemplos Completos: Nuevos Gráficos BESTLIB

## 📋 Preparación

```python
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# Crear datos de prueba (similar a Iris)
np.random.seed(42)
df = pd.DataFrame({
    'sepal_length': np.random.randn(50) * 2 + 5,
    'sepal_width': np.random.randn(50) * 1 + 3,
    'petal_length': np.random.randn(50) * 1.5 + 4,
    'petal_width': np.random.randn(50) * 0.5 + 1.5,
    'species': np.random.choice(['setosa', 'versicolor', 'virginica'], 50)
})
```

---

## 1️⃣ Line Plot (Gráfico de Líneas Completo)

```python
layout = MatrixLayout("L")
layout.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,
    markers=True,
    xLabel="Sepal Length",
    yLabel="Sepal Width"
)
layout.display()
```

**Con múltiples series:**
```python
layout = MatrixLayout("L")
layout.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    series_col="species",  # Múltiples líneas por especie
    strokeWidth=2,
    markers=True
)
layout.display()
```

---

## 2️⃣ Horizontal Bar (Barras Horizontales)

```python
layout = MatrixLayout("B")
species_counts = df['species'].value_counts().reset_index()
species_counts.columns = ['species', 'count']

layout.map_horizontal_bar(
    "B",
    species_counts,
    category_col="species",
    value_col="count",
    xLabel="Count",
    yLabel="Species"
)
layout.display()
```

**Sin value_col (cuenta automáticamente):**
```python
layout = MatrixLayout("B")
layout.map_horizontal_bar(
    "B",
    df,
    category_col="species",
    xLabel="Count",
    yLabel="Species"
)
layout.display()
```

---

## 3️⃣ Hexbin (Visualización de Densidad)

```python
layout = MatrixLayout("H")
layout.map_hexbin(
    "H",
    df,
    x_col="sepal_length",
    y_col="petal_length",
    bins=20,
    colorScale="Blues",
    xLabel="Sepal Length",
    yLabel="Petal Length"
)
layout.display()
```

**Con diferentes escalas de color:**
```python
layout = MatrixLayout("H")
layout.map_hexbin(
    "H",
    df,
    x_col="sepal_length",
    y_col="petal_length",
    bins=25,
    colorScale="Reds",  # O "Blues", "Viridis"
    xLabel="Sepal Length",
    yLabel="Petal Length"
)
layout.display()
```

---

## 4️⃣ Errorbars (Barras de Error)

```python
layout = MatrixLayout("E")

# Crear datos con errores
error_data = []
for i in range(10):
    error_data.append({
        'x': i,
        'y': np.random.rand() * 10,
        'yerr': np.random.rand() * 2,  # Error en Y
        'xerr': np.random.rand() * 0.3  # Error en X (opcional)
    })

error_df = pd.DataFrame(error_data)

layout.map_errorbars(
    "E",
    error_df,
    x_col="x",
    y_col="y",
    yerr="yerr",
    xerr="xerr",  # Opcional
    xLabel="X",
    yLabel="Y"
)
layout.display()
```

**Solo errores en Y:**
```python
layout = MatrixLayout("E")
layout.map_errorbars(
    "E",
    error_df,
    x_col="x",
    y_col="y",
    yerr="yerr",
    xLabel="X",
    yLabel="Y"
)
layout.display()
```

---

## 5️⃣ Fill Between (Área Entre Dos Líneas)

```python
layout = MatrixLayout("F")

# Crear datos con dos líneas
fill_data = []
for i in range(20):
    x = i * 0.5
    fill_data.append({
        'x': x,
        'y1': np.sin(x) + 2,  # Línea superior
        'y2': np.sin(x) - 2   # Línea inferior
    })

fill_df = pd.DataFrame(fill_data)

layout.map_fill_between(
    "F",
    fill_df,
    x_col="x",
    y1="y1",
    y2="y2",
    color="#4a90e2",
    opacity=0.3,
    showLines=True,
    xLabel="X",
    yLabel="Y"
)
layout.display()
```

**Sin mostrar líneas:**
```python
layout = MatrixLayout("F")
layout.map_fill_between(
    "F",
    fill_df,
    x_col="x",
    y1="y1",
    y2="y2",
    showLines=False,  # Solo área, sin líneas
    xLabel="X",
    yLabel="Y"
)
layout.display()
```

---

## 6️⃣ Step Plot (Gráfico Escalonado)

```python
layout = MatrixLayout("S")
layout.map_step(
    "S",
    df.sort_values('sepal_length'),
    x_col="sepal_length",
    y_col="sepal_width",
    stepType="step",  # "step", "stepBefore", "stepAfter"
    strokeWidth=2,
    color="#4a90e2",
    xLabel="Sepal Length",
    yLabel="Sepal Width"
)
layout.display()
```

**Diferentes tipos de step:**
```python
# Step Before
layout = MatrixLayout("S1")
layout.map_step(
    "S1",
    df.sort_values('sepal_length'),
    x_col="sepal_length",
    y_col="sepal_width",
    stepType="stepBefore",
    xLabel="Sepal Length",
    yLabel="Sepal Width"
)
layout.display()

# Step After
layout = MatrixLayout("S2")
layout.map_step(
    "S2",
    df.sort_values('sepal_length'),
    x_col="sepal_length",
    y_col="sepal_width",
    stepType="stepAfter",
    xLabel="Sepal Length",
    yLabel="Sepal Width"
)
layout.display()
```

---

## 🎯 Matriz Completa con Todos los Nuevos Gráficos

```python
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# Crear datos
np.random.seed(42)
df = pd.DataFrame({
    'sepal_length': np.random.randn(50) * 2 + 5,
    'sepal_width': np.random.randn(50) * 1 + 3,
    'petal_length': np.random.randn(50) * 1.5 + 4,
    'petal_width': np.random.randn(50) * 0.5 + 1.5,
    'species': np.random.choice(['setosa', 'versicolor', 'virginica'], 50)
})

# Datos para errorbars
error_data = []
for i in range(10):
    error_data.append({
        'x': i,
        'y': np.random.rand() * 10,
        'yerr': np.random.rand() * 2
    })
error_df = pd.DataFrame(error_data)

# Datos para fill_between
fill_data = []
for i in range(20):
    x = i * 0.5
    fill_data.append({
        'x': x,
        'y1': np.sin(x) + 2,
        'y2': np.sin(x) - 2
    })
fill_df = pd.DataFrame(fill_data)

# Datos para horizontal bar
species_counts = df['species'].value_counts().reset_index()
species_counts.columns = ['species', 'count']

# Crear matriz 3x2 con todos los nuevos gráficos
layout = MatrixLayout("""
LH
EB
FS
""")

# L = Line Plot
layout.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,
    markers=True,
    xLabel="Sepal Length",
    yLabel="Sepal Width"
)

# H = Hexbin
layout.map_hexbin(
    "H",
    df,
    x_col="sepal_length",
    y_col="petal_length",
    bins=20,
    colorScale="Blues",
    xLabel="Sepal Length",
    yLabel="Petal Length"
)

# E = Errorbars
layout.map_errorbars(
    "E",
    error_df,
    x_col="x",
    y_col="y",
    yerr="yerr",
    xLabel="X",
    yLabel="Y"
)

# B = Horizontal Bar
layout.map_horizontal_bar(
    "B",
    species_counts,
    category_col="species",
    value_col="count",
    xLabel="Count",
    yLabel="Species"
)

# F = Fill Between
layout.map_fill_between(
    "F",
    fill_df,
    x_col="x",
    y1="y1",
    y2="y2",
    color="#4a90e2",
    opacity=0.3,
    showLines=True,
    xLabel="X",
    yLabel="Y"
)

# S = Step Plot
layout.map_step(
    "S",
    df.sort_values('sepal_length'),
    x_col="sepal_length",
    y_col="sepal_width",
    stepType="step",
    strokeWidth=2,
    xLabel="Sepal Length",
    yLabel="Sepal Width"
)

layout.display()
```

---

## 📝 Notas Importantes

1. **Siempre usa:** `from BESTLIB.matrix import MatrixLayout` (import directo)
2. **Ordena los datos** para `step_plot` y `fill_between` si es necesario
3. **Para `errorbars` y `fill_between`**, necesitas crear datos con las columnas específicas (`yerr`, `y1`, `y2`)
4. **Para `horizontal_bar`**, puedes omitir `value_col` y se contará automáticamente
5. **Para `hexbin`**, ajusta `bins` según la densidad de datos (más bins = más detalle)

---

## ✅ Verificación

Si todos los gráficos se renderizan correctamente (no `[object Object]`), entonces:
- ✅ `isD3Spec()` está funcionando
- ✅ Los specs se generan correctamente
- ✅ El renderizado JavaScript funciona
- ✅ Los nuevos gráficos están completamente integrados

