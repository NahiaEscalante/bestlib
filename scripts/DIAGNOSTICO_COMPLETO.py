"""
DIAGNÓSTICO COMPLETO - Ejecuta esto en Jupyter/Colab para ver qué está pasando
"""

import pandas as pd
import json
from BESTLIB.matrix import MatrixLayout

# ==========================================
# 1. Crear datos
# ==========================================
print("=" * 60)
print("PASO 1: Crear datos")
print("=" * 60)

df = pd.DataFrame({
    'sepal_length': [5.1, 4.9, 4.7, 4.6, 5.0],
    'sepal_width': [3.5, 3.0, 3.2, 3.1, 3.6]
})

print("✅ Datos creados:", df.shape)
print(df)

# ==========================================
# 2. Crear layout y generar spec
# ==========================================
print("\n" + "=" * 60)
print("PASO 2: Generar spec")
print("=" * 60)

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
print(f"   Keys: {list(spec.keys())}")

# ==========================================
# 3. Verificar formato del spec
# ==========================================
print("\n" + "=" * 60)
print("PASO 3: Verificar formato del spec")
print("=" * 60)

if 'series' in spec:
    series = spec['series']
    print("✅ Spec tiene 'series'")
    print(f"   Tipo de series: {type(series)}")
    print(f"   Es dict: {isinstance(series, dict)}")
    print(f"   Keys en series: {list(series.keys())}")
    
    for key, data in series.items():
        print(f"\n   Serie '{key}':")
        print(f"     Tipo: {type(data)}")
        print(f"     Es lista: {isinstance(data, list)}")
        print(f"     Longitud: {len(data)}")
        if data:
            print(f"     Primer punto: {data[0]}")
            print(f"     Tipo de primer punto: {type(data[0])}")
            if isinstance(data[0], dict):
                print(f"     Keys del punto: {list(data[0].keys())}")
else:
    print("❌ ERROR: Spec NO tiene 'series'")
    print(f"   Spec completo: {spec}")

# ==========================================
# 4. Verificar serialización JSON
# ==========================================
print("\n" + "=" * 60)
print("PASO 4: Verificar serialización JSON")
print("=" * 60)

try:
    # Simular lo que hace _prepare_repr_data
    from BESTLIB.matrix import _sanitize_for_json
    
    spec_sanitized = _sanitize_for_json(spec)
    spec_json = json.dumps(spec_sanitized)
    
    print("✅ Spec serializado a JSON")
    print(f"   Longitud JSON: {len(spec_json)} caracteres")
    print(f"   Primeros 200 caracteres: {spec_json[:200]}")
    
    # Verificar que 'series' está en el JSON
    if '"series"' in spec_json:
        print("✅ 'series' está en el JSON")
    else:
        print("❌ ERROR: 'series' NO está en el JSON")
    
    # Deserializar y verificar
    spec_deserialized = json.loads(spec_json)
    if 'series' in spec_deserialized:
        print("✅ 'series' está después de deserializar")
        series_des = spec_deserialized['series']
        print(f"   Tipo: {type(series_des)}")
        print(f"   Keys: {list(series_des.keys()) if isinstance(series_des, dict) else 'N/A'}")
    else:
        print("❌ ERROR: 'series' NO está después de deserializar")
        
except Exception as e:
    print(f"❌ Error en serialización: {e}")
    import traceback
    traceback.print_exc()

# ==========================================
# 5. Verificar que está en el mapping
# ==========================================
print("\n" + "=" * 60)
print("PASO 5: Verificar mapping")
print("=" * 60)

if 'L' in layout._map:
    spec_in_map = layout._map['L']
    print("✅ Spec está en _map")
    print(f"   Tipo: {spec_in_map.get('type')}")
    print(f"   Tiene series: {'series' in spec_in_map}")
    
    # Verificar que el spec en _map es el mismo
    if spec_in_map == spec:
        print("✅ Spec en _map es idéntico al generado")
    else:
        print("⚠️  Spec en _map es diferente al generado")
else:
    print("❌ ERROR: Spec NO está en _map")

# ==========================================
# 6. Preparar datos para display (simular)
# ==========================================
print("\n" + "=" * 60)
print("PASO 6: Simular _prepare_repr_data")
print("=" * 60)

try:
    data = layout._prepare_repr_data()
    mapping_merged = {**layout._map, **data['meta']}
    mapping_sanitized = _sanitize_for_json(mapping_merged)
    mapping_json = json.dumps(mapping_sanitized)
    
    print("✅ Mapping preparado")
    print(f"   Longitud JSON: {len(mapping_json)} caracteres")
    
    # Verificar que 'L' está en el mapping
    if '"L"' in mapping_json:
        print("✅ 'L' está en el mapping JSON")
    else:
        print("❌ ERROR: 'L' NO está en el mapping JSON")
    
    # Deserializar y verificar
    mapping_deserialized = json.loads(mapping_json)
    if 'L' in mapping_deserialized:
        spec_in_mapping = mapping_deserialized['L']
        print("✅ 'L' está en el mapping deserializado")
        print(f"   Tipo: {spec_in_mapping.get('type')}")
        print(f"   Tiene series: {'series' in spec_in_mapping}")
        
        if 'series' in spec_in_mapping:
            series_in_mapping = spec_in_mapping['series']
            print(f"   Series en mapping: {type(series_in_mapping)}")
            print(f"   Keys: {list(series_in_mapping.keys()) if isinstance(series_in_mapping, dict) else 'N/A'}")
    else:
        print("❌ ERROR: 'L' NO está en el mapping deserializado")
        print(f"   Keys disponibles: {list(mapping_deserialized.keys())[:10]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# ==========================================
# RESUMEN
# ==========================================
print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print("Si todos los pasos muestran ✅, el problema está en JavaScript.")
print("Abre la consola del navegador (F12) y busca errores.")
print("\nSi algún paso muestra ❌, ese es el problema a corregir.")

