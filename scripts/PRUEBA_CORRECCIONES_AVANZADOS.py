"""
Script de prueba para validar las correcciones de gráficos avanzados
Ejecuta este script después de aplicar las correcciones
"""

import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

print("=" * 60)
print("PRUEBA DE CORRECCIONES: Gráficos Avanzados")
print("=" * 60)

# Activar debug
MatrixLayout.set_debug(True)

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'sepal_length': np.random.normal(5.8, 0.8, 150),
    'sepal_width': np.random.normal(3.0, 0.4, 150),
    'petal_length': np.random.normal(3.7, 1.7, 150),
    'petal_width': np.random.normal(1.2, 0.8, 150),
    'species': np.random.choice(['setosa', 'versicolor', 'virginica'], 150)
})

# Preparar datos para diferentes gráficos
print("\n1. Preparando datos...")
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

print(f"   ✅ df_value shape: {df_value.shape}")
print(f"   ✅ df_ridge shape: {df_ridge.shape}")
print(f"   ✅ df_hist2d shape: {df_hist2d.shape}")
print(f"   ✅ df_polar shape: {df_polar.shape}")
print(f"   ✅ df_funnel shape: {df_funnel.shape}")

# Crear layout 3x3
print("\n2. Creando layout 3x3...")
layout = MatrixLayout("""
KDR
QEH
PRF
""")

# Agregar gráficos con títulos de ejes
print("\n3. Agregando gráficos con títulos de ejes...")

try:
    layout.map_kde("K", df_value, column="value", xLabel="Value", yLabel="Density")
    print("   ✅ KDE agregado")
except Exception as e:
    print(f"   ❌ Error en KDE: {e}")

try:
    layout.map_distplot("D", df_value, column="value", bins=30, kde=True, rug=True, 
                       xLabel="Value", yLabel="Density")
    print("   ✅ Distplot agregado")
except Exception as e:
    print(f"   ❌ Error en Distplot: {e}")

try:
    layout.map_rug("R", df_value, column="value", xLabel="Value")
    print("   ✅ Rug agregado")
except Exception as e:
    print(f"   ❌ Error en Rug: {e}")

try:
    layout.map_qqplot("Q", df_value, column="value", xLabel="Theoretical Quantiles", 
                     yLabel="Sample Quantiles")
    print("   ✅ QQ-plot agregado")
except Exception as e:
    print(f"   ❌ Error en QQ-plot: {e}")

try:
    layout.map_ecdf("E", df_value, column="value", xLabel="Value", 
                   yLabel="Cumulative Probability")
    print("   ✅ ECDF agregado")
except Exception as e:
    print(f"   ❌ Error en ECDF: {e}")

try:
    layout.map_hist2d("H", df_hist2d, x_col="x", y_col="y", bins=20, 
                     xLabel="Sepal Length", yLabel="Petal Length")
    print("   ✅ Hist2D agregado")
except Exception as e:
    print(f"   ❌ Error en Hist2D: {e}")

try:
    layout.map_polar("P", df_polar, angle_col="angle", radius_col="radius", 
                    xLabel="Angle", yLabel="Radius")
    print("   ✅ Polar agregado")
except Exception as e:
    print(f"   ❌ Error en Polar: {e}")

try:
    layout.map_ridgeline("I", df_ridge, column="value", category_col="category", 
                        xLabel="Sepal Width")
    print("   ✅ Ridgeline agregado")
except Exception as e:
    print(f"   ❌ Error en Ridgeline: {e}")

try:
    layout.map_funnel("F", df_funnel, stage_col="stage", value_col="value", 
                     xLabel="Stage", yLabel="Count")
    print("   ✅ Funnel agregado")
except Exception as e:
    print(f"   ❌ Error en Funnel: {e}")

# Verificar specs
print("\n4. Verificando specs generados...")
specs_in_map = list(MatrixLayout._map.keys())
print(f"   Gráficos en _map: {specs_in_map}")

for letter in ['K', 'D', 'R', 'Q', 'E', 'H', 'P', 'I', 'F']:
    if letter in MatrixLayout._map:
        spec = MatrixLayout._map[letter]
        has_xlabel = 'xLabel' in spec or (spec.get('options', {}).get('xLabel'))
        has_ylabel = 'yLabel' in spec or (spec.get('options', {}).get('yLabel'))
        has_data = 'data' in spec and len(spec.get('data', [])) > 0
        print(f"   {letter}: type={spec.get('type')}, has_xlabel={has_xlabel}, "
              f"has_ylabel={has_ylabel}, has_data={has_data}")
    else:
        print(f"   ❌ {letter}: NO ENCONTRADO EN _map")

# Renderizar
print("\n5. Renderizando layout...")
print("   ⚠️  Revisa la visualización:")
print("      - Rug plot debe estar visible en posición (1,3) con ticks en el eje X")
print("      - Todos los gráficos deben tener títulos de ejes visibles")
print("      - Ningún gráfico debe aparecer vacío")

try:
    layout.display()
    print("   ✅ Layout renderizado")
except Exception as e:
    print(f"   ❌ Error al renderizar: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("PRUEBA COMPLETA")
print("=" * 60)
print("\n💡 Revisa la consola del navegador (F12) si hay problemas")
print("💡 Verifica que el Rug plot muestre ticks en el eje X")
print("💡 Verifica que todos los gráficos tengan títulos de ejes")

