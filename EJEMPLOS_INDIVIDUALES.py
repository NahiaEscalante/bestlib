"""
Ejemplos individuales para cada nuevo gráfico
Copia y pega cada bloque en una celda de Jupyter/Colab
"""

import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# ==========================================
# PREPARACIÓN: Crear datos de prueba
# ==========================================
np.random.seed(42)
df = pd.DataFrame({
    'sepal_length': np.random.randn(50) * 2 + 5,
    'sepal_width': np.random.randn(50) * 1 + 3,
    'petal_length': np.random.randn(50) * 1.5 + 4,
    'petal_width': np.random.randn(50) * 0.5 + 1.5,
    'species': np.random.choice(['setosa', 'versicolor', 'virginica'], 50)
})

print("✅ Datos creados:", df.shape)

# ==========================================
# 1. LINE PLOT
# ==========================================
print("\n" + "="*60)
print("1. LINE PLOT")
print("="*60)

layout1 = MatrixLayout("L")
layout1.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,
    markers=True,
    xLabel="Sepal Length",
    yLabel="Sepal Width"
)
layout1.display()

# ==========================================
# 2. HORIZONTAL BAR
# ==========================================
print("\n" + "="*60)
print("2. HORIZONTAL BAR")
print("="*60)

layout2 = MatrixLayout("B")
species_counts = df['species'].value_counts().reset_index()
species_counts.columns = ['species', 'count']

layout2.map_horizontal_bar(
    "B",
    species_counts,
    category_col="species",
    value_col="count",
    xLabel="Count",
    yLabel="Species"
)
layout2.display()

# ==========================================
# 3. HEXBIN
# ==========================================
print("\n" + "="*60)
print("3. HEXBIN")
print("="*60)

layout3 = MatrixLayout("H")
layout3.map_hexbin(
    "H",
    df,
    x_col="sepal_length",
    y_col="petal_length",
    bins=20,
    colorScale="Blues",
    xLabel="Sepal Length",
    yLabel="Petal Length"
)
layout3.display()

# ==========================================
# 4. ERRORBARS
# ==========================================
print("\n" + "="*60)
print("4. ERRORBARS")
print("="*60)

# Crear datos con errores
error_data = []
for i in range(10):
    error_data.append({
        'x': i,
        'y': np.random.rand() * 10,
        'yerr': np.random.rand() * 2
    })
error_df = pd.DataFrame(error_data)

layout4 = MatrixLayout("E")
layout4.map_errorbars(
    "E",
    error_df,
    x_col="x",
    y_col="y",
    yerr="yerr",
    xLabel="X",
    yLabel="Y"
)
layout4.display()

# ==========================================
# 5. FILL BETWEEN
# ==========================================
print("\n" + "="*60)
print("5. FILL BETWEEN")
print("="*60)

# Crear datos con dos líneas
fill_data = []
for i in range(20):
    x = i * 0.5
    fill_data.append({
        'x': x,
        'y1': np.sin(x) + 2,
        'y2': np.sin(x) - 2
    })
fill_df = pd.DataFrame(fill_data)

layout5 = MatrixLayout("F")
layout5.map_fill_between(
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
layout5.display()

# ==========================================
# 6. STEP PLOT
# ==========================================
print("\n" + "="*60)
print("6. STEP PLOT")
print("="*60)

layout6 = MatrixLayout("S")
layout6.map_step(
    "S",
    df.sort_values('sepal_length'),
    x_col="sepal_length",
    y_col="sepal_width",
    stepType="step",
    strokeWidth=2,
    color="#4a90e2",
    xLabel="Sepal Length",
    yLabel="Sepal Width"
)
layout6.display()

print("\n✅ Todos los gráficos mostrados")

