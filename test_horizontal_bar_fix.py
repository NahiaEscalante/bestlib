"""
Script de prueba para verificar que horizontal_bar funciona correctamente
"""
import pandas as pd
from BESTLIB.matrix import MatrixLayout

print("=== Prueba 1: Datos básicos ===")
df = pd.DataFrame({
    'sepal_length': [5.1, 4.9, 4.7, 4.6, 5.0],
    'sepal_width': [3.5, 3.0, 3.2, 3.1, 3.6]
})

try:
    # Limpiar mapping anterior
    MatrixLayout._map = {}
    
    # Crear spec
    spec = MatrixLayout.map_horizontal_bar(
        "L",
        df,
        category_col="sepal_width",
        value_col="sepal_length",
        strokeWidth=2,
        markers=True
    )
    
    print(f"✅ Spec creado: tipo={spec.get('type')}, datos={len(spec.get('data', []))}")
    print(f"   Primeros datos: {spec.get('data', [])[:2]}")
    print(f"   Mapping guardado: {'L' in MatrixLayout._map}")
    
    # Crear layout
    layout = MatrixLayout("L")
    print("✅ Layout creado")
    print(f"   Div ID: {layout.div_id}")
    print(f"   Mapping en layout: {layout._map.get('L') is not None}")
    
    print("\n=== Para ver el gráfico en Jupyter/Colab, ejecuta: ===")
    print("layout.display()")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Prueba 2: Datos con categorías repetidas ===")
df2 = pd.DataFrame({
    'categoria': ['A', 'B', 'A', 'B', 'C'],
    'valor': [10, 20, 15, 25, 30]
})

try:
    MatrixLayout._map = {}
    spec2 = MatrixLayout.map_horizontal_bar(
        "H",
        df2,
        category_col="categoria",
        value_col="valor"
    )
    print(f"✅ Spec creado: tipo={spec2.get('type')}, datos={len(spec2.get('data', []))}")
    print(f"   Datos: {spec2.get('data', [])}")
    
except Exception as e:
    print(f"❌ Error: {e}")

