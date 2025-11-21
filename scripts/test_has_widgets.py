
# Script de prueba para verificar HAS_WIDGETS
import sys
sys.path.insert(0, '/Users/nahiaescalante/Documents/2025/Visualizacion/bestlib')

from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

# Crear layout
layout = ReactiveMatrixLayout("S", selection_model=SelectionModel())

# Verificar que selection_widget funciona
print("✅ ReactiveMatrixLayout creado")
print(f"   selection_widget existe: {hasattr(layout, 'selection_widget')}")

# Probar acceso (sin ejecutar display)
try:
    widget = layout.selection_widget
    print("✅ selection_widget accesible sin errores")
    print(f"   Widget: {widget}")
except NameError as e:
    if 'HAS_WIDGETS' in str(e):
        print(f"❌ Error: {e}")
        print("   ⚠️ Todavía usando versión legacy")
    else:
        print(f"⚠️ Otro NameError: {e}")
except Exception as e:
    print(f"⚠️ Error: {e}")
