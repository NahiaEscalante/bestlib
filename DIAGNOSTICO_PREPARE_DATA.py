"""
Diagnóstico específico para prepare_data()
"""
import pandas as pd
import numpy as np

# Crear datos de prueba
df_value = pd.DataFrame({
    'value': [5.1, 4.9, 4.7, 4.6, 5.0, 5.4, 4.6, 5.0, 4.4, 4.9]
})

print("=" * 60)
print("DIAGNÓSTICO: DataFrame de entrada")
print("=" * 60)
print(f"df_value shape: {df_value.shape}")
print(f"df_value columns: {list(df_value.columns)}")
print(f"df_value head:\n{df_value.head()}")
print(f"df_value['value'] type: {type(df_value['value'])}")
print(f"df_value['value'].values type: {type(df_value['value'].values)}")
print(f"df_value['value'].values: {df_value['value'].values}")
print(f"df_value['value'].dropna().values: {df_value['value'].dropna().values}")
print(f"len after dropna: {len(df_value['value'].dropna().values)}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO: Probar prepare_data directamente")
print("=" * 60)

# Importar correctamente desde el módulo charts
from BESTLIB.charts.kde import KdeChart

chart = KdeChart()
print(f"chart.chart_type: {chart.chart_type}")

try:
    print("\n1. Validando datos...")
    chart.validate_data(df_value, column="value")
    print("   ✅ Validación pasada")
except Exception as e:
    print(f"   ❌ Error en validación: {e}")

try:
    print("\n2. Preparando datos...")
    result = chart.prepare_data(df_value, column="value")
    print(f"   result type: {type(result)}")
    print(f"   result keys: {list(result.keys())}")
    if 'data' in result:
        print(f"   result['data'] type: {type(result['data'])}")
        print(f"   result['data'] length: {len(result['data'])}")
        if len(result['data']) > 0:
            print(f"   result['data'][0]: {result['data'][0]}")
        else:
            print("   ❌ result['data'] está vacío!")
except Exception as e:
    print(f"   ❌ Error en prepare_data: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNÓSTICO: Probar get_spec directamente")
print("=" * 60)

try:
    spec = chart.get_spec(df_value, column="value")
    print(f"spec type: {type(spec)}")
    print(f"spec keys: {list(spec.keys())}")
    if 'data' in spec:
        print(f"spec['data'] type: {type(spec['data'])}")
        print(f"spec['data'] length: {len(spec['data'])}")
        if len(spec['data']) > 0:
            print(f"spec['data'][0]: {spec['data'][0]}")
        else:
            print("❌ spec['data'] está vacío!")
except Exception as e:
    print(f"❌ Error en get_spec: {e}")
    import traceback
    traceback.print_exc()

