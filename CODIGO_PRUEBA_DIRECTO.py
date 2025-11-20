"""
CÓDIGO DE PRUEBA DIRECTO - Copia y pega esto en una celda de Jupyter/Colab
"""

# ==========================================
# PASO 1: Importar y crear datos
# ==========================================
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# Crear datos de prueba (o usa tu dataset)
df = pd.DataFrame({
    'sepal_length': [5.1, 4.9, 4.7, 4.6, 5.0, 5.4, 4.6, 5.0, 4.4, 4.9],
    'sepal_width': [3.5, 3.0, 3.2, 3.1, 3.6, 3.9, 3.4, 3.4, 2.9, 3.1],
    'petal_length': [1.4, 1.4, 1.3, 1.5, 1.4, 1.7, 1.4, 1.5, 1.4, 1.5],
    'petal_width': [0.2, 0.2, 0.2, 0.2, 0.2, 0.4, 0.3, 0.2, 0.2, 0.1]
})

print("✅ Datos creados:", df.shape)
print(df.head())

# ==========================================
# PASO 2: Verificar que el spec se genera correctamente
# ==========================================
print("\n" + "="*60)
print("PASO 2: Verificar Spec")
print("="*60)

layout = MatrixLayout("L")
spec = layout.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,
    markers=True
)

print("✅ Spec generado")
print(f"   Tipo: {spec.get('type')}")
print(f"   Tiene 'series': {'series' in spec}")
print(f"   Keys en spec: {list(spec.keys())[:10]}")

if 'series' in spec:
    series = spec['series']
    print(f"   Número de series: {len(series)}")
    for key, data in series.items():
        print(f"   - Serie '{key}': {len(data)} puntos")
        if data and len(data) > 0:
            print(f"     Primer punto: x={data[0].get('x')}, y={data[0].get('y')}")
            print(f"     Último punto: x={data[-1].get('x')}, y={data[-1].get('y')}")
else:
    print("❌ ERROR: El spec NO tiene 'series'")
    print(f"   Spec completo: {spec}")

# ==========================================
# PASO 3: Verificar que está en el mapping
# ==========================================
print("\n" + "="*60)
print("PASO 3: Verificar Mapping")
print("="*60)

if 'L' in layout._map:
    spec_in_map = layout._map['L']
    print("✅ Spec está en _map")
    print(f"   Tipo: {spec_in_map.get('type')}")
    print(f"   Tiene series: {'series' in spec_in_map}")
else:
    print("❌ ERROR: Spec NO está en _map")

# ==========================================
# PASO 4: Activar debug y mostrar
# ==========================================
print("\n" + "="*60)
print("PASO 4: Mostrar Gráfico (con debug)")
print("="*60)
print("⚠️  Abre la consola del navegador (F12) para ver errores")
print("⚠️  Busca mensajes que empiecen con '❌' o 'Error'")

MatrixLayout.set_debug(True)
layout.display()

print("\n✅ Si ves '[object Object]', revisa la consola del navegador")
print("✅ Si ves el gráfico, ¡todo funciona correctamente!")

