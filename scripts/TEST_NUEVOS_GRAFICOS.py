"""
Script de prueba para verificar que los nuevos gráficos funcionan correctamente
"""
import sys
import pandas as pd
import numpy as np

# Agregar BESTLIB al path
sys.path.insert(0, '.')

from BESTLIB.matrix import MatrixLayout

print("=" * 60)
print("TEST: Nuevos Gráficos BESTLIB")
print("=" * 60)

# Crear datos de prueba (similar a Iris)
np.random.seed(42)
df = pd.DataFrame({
    'sepal_length': np.random.randn(50) * 2 + 5,
    'sepal_width': np.random.randn(50) * 1 + 3,
    'petal_length': np.random.randn(50) * 1.5 + 4,
    'petal_width': np.random.randn(50) * 0.5 + 1.5,
    'species': np.random.choice(['setosa', 'versicolor', 'virginica'], 50)
})

print("\n✅ Datos creados:", df.shape)

# ==========================================
# TEST 1: Line Plot
# ==========================================
print("\n" + "=" * 60)
print("TEST 1: Line Plot")
print("=" * 60)

try:
    layout1 = MatrixLayout("L")
    spec1 = layout1.map_line_plot(
        "L",
        df,
        x_col="sepal_length",
        y_col="sepal_width",
        strokeWidth=2,
        markers=True
    )
    
    print("✅ Spec generado correctamente")
    print(f"   Tipo: {spec1.get('type')}")
    print(f"   Tiene 'series': {'series' in spec1}")
    
    if 'series' in spec1:
        series = spec1['series']
        print(f"   Número de series: {len(series)}")
        for key, data in list(series.items())[:3]:
            print(f"   - Serie '{key}': {len(data)} puntos")
            if data:
                print(f"     Primer punto: x={data[0].get('x')}, y={data[0].get('y')}")
    
    print(f"   Keys en spec: {list(spec1.keys())[:10]}")
    
    # Verificar que el spec tenga el formato correcto
    if spec1.get('type') == 'line_plot' and 'series' in spec1:
        print("✅ Spec tiene formato correcto para line_plot")
    else:
        print("❌ Spec NO tiene formato correcto")
        print(f"   Esperado: type='line_plot', tiene 'series'")
        print(f"   Obtenido: type={spec1.get('type')}, tiene 'series'={'series' in spec1}")
    
except Exception as e:
    print(f"❌ Error en TEST 1: {e}")
    import traceback
    traceback.print_exc()

# ==========================================
# TEST 2: Horizontal Bar
# ==========================================
print("\n" + "=" * 60)
print("TEST 2: Horizontal Bar")
print("=" * 60)

try:
    layout2 = MatrixLayout("B")
    species_counts = df['species'].value_counts().reset_index()
    species_counts.columns = ['species', 'count']
    
    spec2 = layout2.map_horizontal_bar(
        "B",
        species_counts,
        category_col="species",
        value_col="count",
        xLabel="Count",
        yLabel="Species"
    )
    
    print("✅ Spec generado correctamente")
    print(f"   Tipo: {spec2.get('type')}")
    print(f"   Tiene 'data': {'data' in spec2}")
    
    if 'data' in spec2:
        data = spec2['data']
        print(f"   Número de barras: {len(data)}")
        if data:
            print(f"   Primer elemento: {data[0]}")
    
    if spec2.get('type') == 'horizontal_bar' and 'data' in spec2:
        print("✅ Spec tiene formato correcto para horizontal_bar")
    else:
        print("❌ Spec NO tiene formato correcto")
        
except Exception as e:
    print(f"❌ Error en TEST 2: {e}")
    import traceback
    traceback.print_exc()

# ==========================================
# TEST 3: Verificar que los métodos existen
# ==========================================
print("\n" + "=" * 60)
print("TEST 3: Verificar métodos disponibles")
print("=" * 60)

methods = [m for m in dir(MatrixLayout) if m.startswith('map_')]
print(f"✅ Métodos map_* disponibles: {len(methods)}")
print(f"   Nuevos gráficos:")
new_charts = ['map_line_plot', 'map_horizontal_bar', 'map_hexbin', 'map_errorbars', 'map_fill_between', 'map_step']
for chart in new_charts:
    if chart in methods:
        print(f"   ✅ {chart}")
    else:
        print(f"   ❌ {chart} NO disponible")

print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print("Si todos los tests pasan, los gráficos deberían renderizar correctamente.")
print("Si ves '[object Object]', verifica la consola del navegador para errores JS.")

