"""
Script de prueba completo para diagnosticar problemas de rendering
"""
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# Activar debug
MatrixLayout.set_debug(True)

# Cargar datos de ejemplo (Iris)
try:
    from sklearn.datasets import load_iris
    iris = load_iris()
    df = pd.DataFrame(iris.data, columns=iris.feature_names)
    df['species'] = iris.target_names[iris.target]
except:
    # Fallback: crear datos sintéticos
    np.random.seed(42)
    df = pd.DataFrame({
        'sepal_length': np.random.normal(5.8, 0.8, 150),
        'sepal_width': np.random.normal(3.0, 0.4, 150),
        'petal_length': np.random.normal(3.7, 1.7, 150),
        'petal_width': np.random.normal(1.2, 0.8, 150),
        'species': np.random.choice(['setosa', 'versicolor', 'virginica'], 150)
    })

print("=" * 60)
print("DIAGNÓSTICO: Preparación de datos")
print("=" * 60)

# Preparar datos
df_value = df[['sepal_length']].rename(columns={'sepal_length': 'value'})
df_ridge = df[['species', 'sepal_width']].rename(columns={'species': 'category', 'sepal_width': 'value'})
xvals = np.linspace(0, 5, 25)
df_ribbon = pd.DataFrame({
    'x': xvals,
    'y1': np.sin(xvals) + 2,
    'y2': np.sin(xvals) - 2
})
df_hist2d = df[['sepal_length', 'petal_length']].rename(columns={'sepal_length': 'x', 'petal_length': 'y'})
df_polar = pd.DataFrame({
    'angle': np.linspace(0, 2*np.pi, len(df)),
    'radius': df['petal_length']
})
df_funnel = df['species'].value_counts().reset_index()
df_funnel.columns = ['stage', 'value']

print(f"✅ df_value shape: {df_value.shape}")
print(f"✅ df_ridge shape: {df_ridge.shape}")
print(f"✅ df_hist2d shape: {df_hist2d.shape}")
print(f"✅ df_polar shape: {df_polar.shape}")
print(f"✅ df_funnel shape: {df_funnel.shape}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO: Generación de specs")
print("=" * 60)

# Crear layout - NOTA: Cambiar 'R' duplicado
layout = MatrixLayout("""
KDR
QEH
PRF
""")

# Generar specs y verificar
specs = {}

print("\n1. KDE:")
spec_kde = layout.map_kde("K", df_value, column="value")
specs['K'] = spec_kde
print(f"   type: {spec_kde.get('type')}")
print(f"   has_data: {'data' in spec_kde}")
print(f"   data_length: {len(spec_kde.get('data', [])) if 'data' in spec_kde else 0}")
if 'data' in spec_kde and len(spec_kde.get('data', [])) > 0:
    print(f"   data_sample: {spec_kde['data'][:2]}")

print("\n2. Distplot:")
spec_distplot = layout.map_distplot("D", df_value, column="value", bins=30, kde=True, rug=True)
specs['D'] = spec_distplot
print(f"   type: {spec_distplot.get('type')}")
print(f"   has_data: {'data' in spec_distplot}")
if 'data' in spec_distplot:
    data = spec_distplot['data']
    print(f"   data_type: {type(data)}")
    if isinstance(data, dict):
        print(f"   data_keys: {list(data.keys())}")
        print(f"   histogram_length: {len(data.get('histogram', []))}")
        print(f"   kde_length: {len(data.get('kde', []))}")
        print(f"   rug_length: {len(data.get('rug', []))}")

print("\n3. Rug:")
spec_rug = layout.map_rug("R", df_value, column="value", axis='x')
specs['R'] = spec_rug
print(f"   type: {spec_rug.get('type')}")
print(f"   has_data: {'data' in spec_rug}")
print(f"   data_length: {len(spec_rug.get('data', [])) if 'data' in spec_rug else 0}")

print("\n4. Q-Q Plot:")
spec_qqplot = layout.map_qqplot("Q", df_value, column="value", dist='norm')
specs['Q'] = spec_qqplot
print(f"   type: {spec_qqplot.get('type')}")
print(f"   has_data: {'data' in spec_qqplot}")
print(f"   data_length: {len(spec_qqplot.get('data', [])) if 'data' in spec_qqplot else 0}")

print("\n5. ECDF:")
spec_ecdf = layout.map_ecdf("E", df_value, column="value")
specs['E'] = spec_ecdf
print(f"   type: {spec_ecdf.get('type')}")
print(f"   has_data: {'data' in spec_ecdf}")
print(f"   data_length: {len(spec_ecdf.get('data', [])) if 'data' in spec_ecdf else 0}")

print("\n6. Hist2D:")
spec_hist2d = layout.map_hist2d("H", df_hist2d, x_col="x", y_col="y", bins=20)
specs['H'] = spec_hist2d
print(f"   type: {spec_hist2d.get('type')}")
print(f"   has_data: {'data' in spec_hist2d}")
print(f"   data_length: {len(spec_hist2d.get('data', [])) if 'data' in spec_hist2d else 0}")

print("\n7. Polar:")
spec_polar = layout.map_polar("P", df_polar, angle_col="angle", radius_col="radius")
specs['P'] = spec_polar
print(f"   type: {spec_polar.get('type')}")
print(f"   has_data: {'data' in spec_polar}")
print(f"   data_length: {len(spec_polar.get('data', [])) if 'data' in spec_polar else 0}")
if 'data' in spec_polar and len(spec_polar.get('data', [])) > 0:
    first_item = spec_polar['data'][0]
    print(f"   first_item_keys: {list(first_item.keys())}")

print("\n8. Ridgeline:")
spec_ridgeline = layout.map_ridgeline("I", df_ridge, column="value", category_col="category")  # Cambiar a 'I' para evitar duplicado
specs['I'] = spec_ridgeline
print(f"   type: {spec_ridgeline.get('type')}")
print(f"   has_series: {'series' in spec_ridgeline}")
if 'series' in spec_ridgeline:
    series = spec_ridgeline['series']
    print(f"   series_type: {type(series)}")
    if isinstance(series, dict):
        print(f"   series_keys: {list(series.keys())}")
        if len(series) > 0:
            first_key = list(series.keys())[0]
            print(f"   first_series_length: {len(series[first_key])}")

print("\n9. Funnel:")
spec_funnel = layout.map_funnel("F", df_funnel, stage_col="stage", value_col="value")
specs['F'] = spec_funnel
print(f"   type: {spec_funnel.get('type')}")
print(f"   has_data: {'data' in spec_funnel}")
print(f"   data_length: {len(spec_funnel.get('data', [])) if 'data' in spec_funnel else 0}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO: Verificación de MatrixLayout._map")
print("=" * 60)
print(f"MatrixLayout._map keys: {list(MatrixLayout._map.keys())}")
for key in ['K', 'D', 'R', 'Q', 'E', 'H', 'P', 'I', 'F']:
    if key in MatrixLayout._map:
        spec = MatrixLayout._map[key]
        print(f"  {key}: type={spec.get('type')}, has_data={'data' in spec}, has_series={'series' in spec}")
    else:
        print(f"  {key}: ❌ NO ENCONTRADO EN _map")

print("\n" + "=" * 60)
print("Renderizando layout...")
print("=" * 60)
print("\n⚠️  NOTA: Revisa la consola del navegador (F12) para ver los logs de JavaScript")
print("⚠️  NOTA: El layout usa 'I' para ridgeline en lugar de 'R' para evitar duplicados\n")

layout.display()

