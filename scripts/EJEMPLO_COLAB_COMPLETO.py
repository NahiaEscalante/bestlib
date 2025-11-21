"""
Ejemplo completo para usar BESTLIB en Google Colab
Después de instalar, ejecuta este código
"""

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# Activar debug para ver logs (opcional)
MatrixLayout.set_debug(True)

# ============================================================================
# PREPARAR DATOS
# ============================================================================
print("Preparando datos...")

# Crear datos de ejemplo (o cargar tus propios datos)
np.random.seed(42)
df = pd.DataFrame({
    'sepal_length': np.random.normal(5.8, 0.8, 150),
    'sepal_width': np.random.normal(3.0, 0.4, 150),
    'petal_length': np.random.normal(3.7, 1.7, 150),
    'petal_width': np.random.normal(1.2, 0.8, 150),
    'species': np.random.choice(['setosa', 'versicolor', 'virginica'], 150)
})

# Preparar datos para diferentes gráficos
df_value = df[['sepal_length']].rename(columns={'sepal_length': 'value'})
df_ridge = df[['species', 'sepal_width']].rename(
    columns={'species': 'category', 'sepal_width': 'value'}
)
df_hist2d = df[['sepal_length', 'petal_length']].rename(
    columns={'sepal_length': 'x', 'petal_length': 'y'}
)
df_polar = pd.DataFrame({
    'angle': np.linspace(0, 2*np.pi, len(df)),
    'radius': df['petal_length']
})
df_funnel = df['species'].value_counts().reset_index()
df_funnel.columns = ['stage', 'value']

print("✅ Datos preparados")

# ============================================================================
# EJEMPLO 1: Gráfico Individual (KDE)
# ============================================================================
print("\n" + "=" * 60)
print("EJEMPLO 1: KDE Individual")
print("=" * 60)

layout1 = MatrixLayout("K")
layout1.map_kde("K", df_value, column="value")
layout1.display()

# ============================================================================
# EJEMPLO 2: Matriz 2x2 (KDE, Distplot, Hist2D, ECDF)
# ============================================================================
print("\n" + "=" * 60)
print("EJEMPLO 2: Matriz 2x2")
print("=" * 60)

layout2 = MatrixLayout("""
KD
HE
""")

layout2.map_kde("K", df_value, column="value")
layout2.map_distplot("D", df_value, column="value", bins=30, kde=True, rug=True)
layout2.map_hist2d("H", df_hist2d, x_col="x", y_col="y", bins=20)
layout2.map_ecdf("E", df_value, column="value")

layout2.display()

# ============================================================================
# EJEMPLO 3: Matriz Completa 3x3 (Todos los gráficos nuevos)
# ============================================================================
print("\n" + "=" * 60)
print("EJEMPLO 3: Matriz Completa 3x3")
print("=" * 60)
print("⚠️  Nota: Usa 'I' para ridgeline para evitar duplicado con 'R' de rug")

layout3 = MatrixLayout("""
KDR
QEH
PRF
""")

layout3.map_kde("K", df_value, column="value")
layout3.map_distplot("D", df_value, column="value", bins=30, kde=True, rug=True)
layout3.map_rug("R", df_value, column="value", axis='x')
layout3.map_qqplot("Q", df_value, column="value", dist='norm')
layout3.map_ecdf("E", df_value, column="value")
layout3.map_hist2d("H", df_hist2d, x_col="x", y_col="y", bins=20)
layout3.map_polar("P", df_polar, angle_col="angle", radius_col="radius")
layout3.map_ridgeline("I", df_ridge, column="value", category_col="category")  # 'I' en lugar de 'R'
layout3.map_funnel("F", df_funnel, stage_col="stage", value_col="value")

layout3.display()

print("\n✅ Todos los gráficos renderizados")
print("💡 Revisa la consola del navegador (F12) si hay problemas")

