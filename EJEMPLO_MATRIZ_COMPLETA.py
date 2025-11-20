"""
Ejemplo de matriz completa con todos los nuevos gráficos
Copia y pega esto en una celda de Jupyter/Colab
"""

import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# ==========================================
# Crear datos de prueba
# ==========================================
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

# ==========================================
# Crear matriz 3x2 con todos los nuevos gráficos
# ==========================================
# Layout:
# L H
# E B
# F S
# ==========================================

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

# Mostrar
layout.display()

print("✅ Matriz completa con 6 nuevos gráficos")

