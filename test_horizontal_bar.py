"""
Ejemplo de prueba para horizontal_bar chart
"""
import pandas as pd
from BESTLIB.matrix import MatrixLayout

# Crear datos de ejemplo
df = pd.DataFrame({
    'sepal_length': [5.1, 4.9, 4.7, 4.6, 5.0],
    'sepal_width': [3.5, 3.0, 3.2, 3.1, 3.6]
})

# Opción 1: Usando category_col y value_col (recomendado)
# Para un horizontal bar chart, necesitas categorías y valores
# Ejemplo: usar sepal_width como categoría y sepal_length como valor
print("=== Opción 1: Usando category_col y value_col ===")
MatrixLayout.map_horizontal_bar(
    "L",
    df,
    category_col="sepal_width",  # Categorías (eje Y)
    value_col="sepal_length",     # Valores (eje X)
    strokeWidth=2,
    markers=True
)
layout1 = MatrixLayout("L")
print("Layout creado correctamente")

# Opción 2: Usando x_col y y_col (alias, para compatibilidad)
print("\n=== Opción 2: Usando x_col y y_col (alias) ===")
MatrixLayout.map_horizontal_bar(
    "H",
    df,
    y_col="sepal_width",   # Alias de category_col (categorías, eje Y)
    x_col="sepal_length",  # Alias de value_col (valores, eje X)
    strokeWidth=2,
    markers=True
)
layout2 = MatrixLayout("H")
print("Layout creado correctamente")

# Opción 3: Ejemplo más realista con categorías únicas
print("\n=== Opción 3: Ejemplo más realista ===")
df_real = pd.DataFrame({
    'categoria': ['A', 'B', 'C', 'A', 'B'],  # Categorías
    'valor': [10, 20, 15, 12, 25]            # Valores
})
MatrixLayout.map_horizontal_bar(
    "B",
    df_real,
    category_col="categoria",
    value_col="valor",
    interactive=True
)
layout3 = MatrixLayout("B")
print("Layout creado correctamente")

print("\n✅ Todos los ejemplos funcionaron correctamente!")
print("\nPara mostrar los gráficos en Jupyter/Colab, usa:")
print("  layout1.display()")
print("  layout2.display()")
print("  layout3.display()")

