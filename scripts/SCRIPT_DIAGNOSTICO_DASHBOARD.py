#!/usr/bin/env python3
"""
Script de diagnóstico para dashboard BESTLIB
Ejecuta este script para identificar problemas con tu dashboard interactivo
"""
import sys

print("=" * 60)
print("🔍 DIAGNÓSTICO DE DASHBOARD BESTLIB")
print("=" * 60)

# Test 1: Imports
print("\n1️⃣ Test de Imports:")
try:
    from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
    from BESTLIB.matrix import MatrixLayout
    from BESTLIB.charts import ChartRegistry
    print("   ✅ Todos los imports exitosos")
    print(f"   - ReactiveMatrixLayout: {ReactiveMatrixLayout.__module__}")
    print(f"   - MatrixLayout: {MatrixLayout.__module__}")
    print(f"   - ChartRegistry: {ChartRegistry.__module__}")
except Exception as e:
    print(f"   ❌ Error en imports: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Crear layout básico
print("\n2️⃣ Test de Creación de Layout:")
try:
    selection = SelectionModel()
    layout = ReactiveMatrixLayout("AS\nHX", selection_model=selection)
    print("   ✅ Layout creado")
    print(f"   - Tipo: {type(layout)}")
    print(f"   - Tiene _layout: {hasattr(layout, '_layout')}")
    print(f"   - Tiene _data: {hasattr(layout, '_data')}")
except Exception as e:
    print(f"   ❌ Error creando layout: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Configurar datos
print("\n3️⃣ Test de Configuración de Datos:")
try:
    import pandas as pd
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10],
        'cat': ['A', 'B', 'A', 'B', 'A']
    })
    layout.set_data(df)
    print("   ✅ Datos configurados")
    print(f"   - Shape: {df.shape}")
except Exception as e:
    print(f"   ❌ Error configurando datos: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Agregar gráficos
print("\n4️⃣ Test de Agregar Gráficos:")
charts_to_test = [
    ('A', 'scatter', {'x_col': 'x', 'y_col': 'y', 'category_col': 'cat', 'interactive': True}),
    ('H', 'histogram', {'column': 'x', 'linked_to': 'A'}),
    ('B', 'barchart', {'category_col': 'cat', 'linked_to': 'A'}),
]

for letter, chart_type, kwargs in charts_to_test:
    try:
        if chart_type == 'scatter':
            layout.add_scatter(letter, **kwargs)
        elif chart_type == 'histogram':
            layout.add_histogram(letter, **kwargs)
        elif chart_type == 'barchart':
            layout.add_barchart(letter, **kwargs)
        print(f"   ✅ {chart_type} '{letter}' agregado")
    except Exception as e:
        print(f"   ❌ Error agregando {chart_type} '{letter}': {e}")
        import traceback
        traceback.print_exc()

# Test 5: Verificar _layout._map
print("\n5️⃣ Test de Verificación de _layout._map:")
try:
    if hasattr(layout._layout, '_map'):
        keys = list(layout._layout._map.keys())
        print(f"   ✅ _map tiene {len(keys)} gráficos: {keys}")
        for key in keys:
            spec = layout._layout._map[key]
            print(f"      - '{key}': type={spec.get('type', 'N/A')}")
    else:
        print("   ❌ _layout no tiene _map")
except Exception as e:
    print(f"   ❌ Error verificando _map: {e}")

# Test 6: Test de display (sin ejecutar realmente)
print("\n6️⃣ Test de Método display():")
try:
    has_display = hasattr(layout, 'display')
    print(f"   ✅ Método display disponible: {has_display}")
    if has_display:
        import inspect
        sig = inspect.signature(layout.display)
        print(f"   - Firma: {sig}")
        
        # Verificar que _layout tiene display
        has_layout_display = hasattr(layout._layout, 'display')
        print(f"   - _layout.display disponible: {has_layout_display}")
        
        # Verificar _repr_html_
        has_repr_html = hasattr(layout._layout, '_repr_html_')
        print(f"   - _layout._repr_html_ disponible: {has_repr_html}")
        
        if has_repr_html:
            try:
                html = layout._layout._repr_html_()
                print(f"   - HTML generado: {len(html)} caracteres")
                if len(html) < 100:
                    print("   ⚠️ HTML muy corto, puede haber un problema")
                else:
                    print("   ✅ HTML generado correctamente")
            except Exception as e:
                print(f"   ❌ Error generando HTML: {e}")
                import traceback
                traceback.print_exc()
except Exception as e:
    print(f"   ❌ Error verificando display: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ DIAGNÓSTICO COMPLETO")
print("=" * 60)
print("\nSi todos los tests pasan pero display() no funciona:")
print("1. Reinicia el kernel de Jupyter/Colab")
print("2. Verifica que estás en un entorno Jupyter (no script Python)")
print("3. Intenta usar: from IPython.display import display; display(layout._layout)")
print("4. Verifica la consola del navegador para errores JavaScript")

