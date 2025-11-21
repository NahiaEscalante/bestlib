"""
Validación completa del pipeline KDE
Verifica que todo el flujo funcione correctamente
"""
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

print("=" * 60)
print("VALIDACIÓN COMPLETA DEL PIPELINE KDE")
print("=" * 60)

# Activar debug
MatrixLayout.set_debug(True)

print("\n1. Verificar que KdeChart existe y se puede importar...")
try:
    from BESTLIB.charts.kde import KdeChart
    print("   ✅ KdeChart importado correctamente")
    print(f"   ✅ chart_type: {KdeChart().chart_type}")
except Exception as e:
    print(f"   ❌ Error al importar KdeChart: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n2. Verificar que está registrado en ChartRegistry...")
try:
    from BESTLIB.charts import ChartRegistry
    chart = ChartRegistry.get('kde')
    print(f"   ✅ KDE está registrado en ChartRegistry")
    print(f"   ✅ Tipo de chart obtenido: {type(chart)}")
except Exception as e:
    print(f"   ❌ Error al obtener KDE del registry: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n3. Crear datos de prueba...")
df_value = pd.DataFrame({
    'value': [5.1, 4.9, 4.7, 4.6, 5.0, 5.4, 4.6, 5.0, 4.4, 4.9, 5.1, 4.8, 4.7, 4.9, 5.0]
})
print(f"   ✅ DataFrame creado: shape={df_value.shape}")
print(f"   ✅ Columnas: {list(df_value.columns)}")
print(f"   ✅ Primeros valores: {df_value['value'].head().tolist()}")

print("\n4. Probar KdeChart directamente...")
try:
    chart = KdeChart()
    
    # Validar
    chart.validate_data(df_value, column="value")
    print("   ✅ Validación pasada")
    
    # Preparar datos
    prepared = chart.prepare_data(df_value, column="value")
    print(f"   ✅ Datos preparados: type={type(prepared)}")
    print(f"   ✅ Keys en prepared: {list(prepared.keys())}")
    if 'data' in prepared:
        print(f"   ✅ prepared['data'] length: {len(prepared['data'])}")
        if len(prepared['data']) > 0:
            print(f"   ✅ Primer punto: {prepared['data'][0]}")
            print(f"   ✅ Último punto: {prepared['data'][-1]}")
        else:
            print("   ❌ prepared['data'] está vacío!")
    
    # Obtener spec
    spec = chart.get_spec(df_value, column="value")
    print(f"   ✅ Spec generado: type={spec.get('type')}")
    print(f"   ✅ Spec tiene 'data': {'data' in spec}")
    if 'data' in spec:
        print(f"   ✅ spec['data'] length: {len(spec['data'])}")
        if len(spec['data']) > 0:
            print(f"   ✅ Primer punto del spec: {spec['data'][0]}")
        else:
            print("   ❌ spec['data'] está vacío!")
    print(f"   ✅ Spec tiene 'options': {'options' in spec}")
    
except Exception as e:
    print(f"   ❌ Error al probar KdeChart: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n5. Probar map_kde en MatrixLayout...")
try:
    layout = MatrixLayout("K")
    spec = layout.map_kde("K", df_value, column="value")
    print(f"   ✅ map_kde ejecutado correctamente")
    print(f"   ✅ Spec retornado: type={spec.get('type')}")
    print(f"   ✅ Spec tiene 'data': {'data' in spec}")
    if 'data' in spec:
        print(f"   ✅ spec['data'] length: {len(spec['data'])}")
    
    # Verificar que está en MatrixLayout._map
    if 'K' in MatrixLayout._map:
        stored_spec = MatrixLayout._map['K']
        print(f"   ✅ Spec almacenado en MatrixLayout._map['K']")
        print(f"   ✅ Stored spec type: {stored_spec.get('type')}")
        print(f"   ✅ Stored spec tiene 'data': {'data' in stored_spec}")
        if 'data' in stored_spec:
            print(f"   ✅ Stored spec['data'] length: {len(stored_spec['data'])}")
    else:
        print("   ❌ Spec NO está en MatrixLayout._map['K']")
    
except Exception as e:
    print(f"   ❌ Error al probar map_kde: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n6. Verificar que renderKdeD3 existe en JavaScript...")
print("   ℹ️  Esto se verifica manualmente en la consola del navegador")
print("   ℹ️  Después de display(), verifica que renderKdeD3 se llame")

print("\n" + "=" * 60)
print("RENDERIZANDO LAYOUT...")
print("=" * 60)
print("\n⚠️  Revisa la consola del navegador (F12) después de esto")
print("⚠️  Deberías ver logs de renderKdeD3 y el gráfico renderizado\n")

try:
    layout.display()
    print("✅ Layout.display() ejecutado")
except Exception as e:
    print(f"❌ Error al ejecutar display(): {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("VALIDACIÓN COMPLETA")
print("=" * 60)
print("✅ Si todos los pasos anteriores pasaron, el pipeline está correcto")
print("✅ Si el gráfico no se renderiza, revisa la consola del navegador (F12)")
print("✅ Busca logs que empiecen con '[BESTLIB] renderKdeD3'")

