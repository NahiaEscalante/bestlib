"""
Script de validación final para verificar que todo el pipeline funciona
"""
import sys
import os

print("=" * 60)
print("VALIDACIÓN FINAL DEL PIPELINE KDE")
print("=" * 60)

# Paso 1: Verificar ubicación de BESTLIB
print("\n1. Verificando ubicación de BESTLIB...")
try:
    import BESTLIB
    bestlib_path = BESTLIB.__file__
    print(f"   ✅ BESTLIB importado desde: {bestlib_path}")
    
    # Verificar que charts existe
    charts_path = os.path.join(os.path.dirname(bestlib_path), 'charts')
    charts_init = os.path.join(charts_path, '__init__.py')
    if os.path.exists(charts_init):
        print(f"   ✅ BESTLIB/charts/__init__.py existe")
    else:
        print(f"   ❌ BESTLIB/charts/__init__.py NO existe en: {charts_init}")
        print(f"   ⚠️  Esto indica que la instalación no incluyó los subpaquetes")
        print(f"   💡 Solución: Ejecuta 'pip install -e . --force-reinstall'")
except Exception as e:
    print(f"   ❌ Error al importar BESTLIB: {e}")
    exit(1)

# Paso 2: Verificar imports de charts
print("\n2. Verificando imports de charts...")
try:
    from BESTLIB.charts import ChartRegistry
    print(f"   ✅ ChartRegistry importado: {ChartRegistry}")
except Exception as e:
    print(f"   ❌ Error al importar ChartRegistry: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    from BESTLIB.charts.kde import KdeChart
    print(f"   ✅ KdeChart importado: {KdeChart}")
except Exception as e:
    print(f"   ❌ Error al importar KdeChart: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Paso 3: Verificar registro en ChartRegistry
print("\n3. Verificando registro en ChartRegistry...")
try:
    chart = ChartRegistry.get('kde')
    print(f"   ✅ KDE está registrado: {chart}")
    print(f"   ✅ Tipo: {type(chart)}")
except Exception as e:
    print(f"   ❌ Error al obtener KDE del registry: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Paso 4: Probar generación de spec
print("\n4. Probando generación de spec...")
try:
    import pandas as pd
    df_value = pd.DataFrame({"value": [5.1, 4.9, 4.7, 4.6, 5.0, 5.4, 4.6, 5.0, 4.4, 4.9]})
    
    chart = KdeChart()
    spec = chart.get_spec(df_value, column="value")
    
    print(f"   ✅ Spec generado: type={spec.get('type')}")
    print(f"   ✅ Spec tiene 'data': {'data' in spec}")
    if 'data' in spec:
        data_len = len(spec['data'])
        print(f"   ✅ spec['data'] length: {data_len}")
        if data_len > 0:
            print(f"   ✅ Primer punto: {spec['data'][0]}")
        else:
            print(f"   ⚠️  spec['data'] está vacío (esto es el problema que estamos investigando)")
except Exception as e:
    print(f"   ❌ Error al generar spec: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Paso 5: Probar map_kde
print("\n5. Probando map_kde en MatrixLayout...")
try:
    from BESTLIB.matrix import MatrixLayout
    
    layout = MatrixLayout("K")
    spec = layout.map_kde("K", df_value, column="value")
    
    print(f"   ✅ map_kde ejecutado")
    print(f"   ✅ Spec retornado: type={spec.get('type')}")
    if 'data' in spec:
        print(f"   ✅ spec['data'] length: {len(spec['data'])}")
    
    # Verificar que está en _map
    if 'K' in MatrixLayout._map:
        stored = MatrixLayout._map['K']
        print(f"   ✅ Spec almacenado en MatrixLayout._map['K']")
        if 'data' in stored:
            print(f"   ✅ Stored spec['data'] length: {len(stored['data'])}")
    else:
        print(f"   ❌ Spec NO está en MatrixLayout._map")
        
except Exception as e:
    print(f"   ❌ Error en map_kde: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Paso 6: Verificar renderer JavaScript
print("\n6. Verificando renderer JavaScript...")
try:
    matrix_js_path = os.path.join(os.path.dirname(bestlib_path), 'matrix.js')
    if os.path.exists(matrix_js_path):
        with open(matrix_js_path, 'r') as f:
            js_content = f.read()
        
        has_render_kde = 'function renderKdeD3' in js_content
        has_case_kde = "chartType === 'kde'" in js_content or "case 'kde'" in js_content
        
        print(f"   ✅ matrix.js existe")
        print(f"   ✅ renderKdeD3 existe: {has_render_kde}")
        print(f"   ✅ case 'kde' existe: {has_case_kde}")
    else:
        print(f"   ⚠️  matrix.js no encontrado en: {matrix_js_path}")
except Exception as e:
    print(f"   ⚠️  Error al verificar JS: {e}")

print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print("✅ Si todos los pasos pasaron, el pipeline está correcto")
print("⚠️  Si spec['data'] está vacío, el problema está en prepare_data()")
print("💡 Revisa los logs de Python para ver errores específicos")
print("\nPara renderizar:")
print("  layout.display()")

