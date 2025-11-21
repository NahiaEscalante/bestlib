"""
Script completo de instalación para Google Colab
Copia y pega esto en una celda de Colab
"""

print("=" * 60)
print("INSTALACIÓN DE BESTLIB EN GOOGLE COLAB")
print("=" * 60)

# ============================================================================
# PASO 1: Clonar repositorio
# ============================================================================
print("\n1. Clonando repositorio...")
print("   ⚠️  IMPORTANTE: Ajusta la URL de tu repositorio")
print("   Ejemplo: !git clone https://github.com/tu-usuario/bestlib.git")

# Descomenta y ajusta la siguiente línea con tu URL:
# !git clone https://github.com/tu-usuario/bestlib.git

# Si ya está clonado, solo actualiza:
# !cd bestlib && git pull

# ============================================================================
# PASO 2: Instalar BESTLIB
# ============================================================================
print("\n2. Instalando BESTLIB...")
print("   Ejecutando: pip install -e . --force-reinstall --no-deps")

# Descomenta la siguiente línea:
# !cd bestlib && pip install -e . --force-reinstall --no-deps

# ============================================================================
# PASO 3: Instalar dependencias
# ============================================================================
print("\n3. Instalando dependencias...")
print("   Ejecutando: pip install pandas numpy scipy ipython ipywidgets")

# Descomenta la siguiente línea:
# !pip install pandas numpy scipy ipython ipywidgets

# ============================================================================
# PASO 4: Verificar instalación
# ============================================================================
print("\n4. Verificando instalación...")

try:
    import sys
    # Agregar al path si es necesario
    if '/content/bestlib' not in sys.path:
        sys.path.insert(0, '/content/bestlib')
    
    import BESTLIB
    print(f"   ✅ BESTLIB ubicado en: {BESTLIB.__file__}")
    
    from BESTLIB.charts import ChartRegistry
    print(f"   ✅ ChartRegistry importado: {ChartRegistry}")
    
    from BESTLIB.charts.kde import KdeChart
    print(f"   ✅ KdeChart importado: {KdeChart}")
    
    # Verificar registro
    chart = ChartRegistry.get('kde')
    print(f"   ✅ KDE registrado: {chart}")
    
    print("\n" + "=" * 60)
    print("✅ INSTALACIÓN COMPLETA")
    print("=" * 60)
    print("\n⚠️  IMPORTANTE: Reinicia el runtime ahora")
    print("   Runtime → Restart runtime")
    print("\nLuego puedes usar BESTLIB normalmente:")
    print("   from BESTLIB.matrix import MatrixLayout")
    print("   layout = MatrixLayout('K')")
    print("   layout.map_kde('K', df, column='value')")
    print("   layout.display()")
    
except Exception as e:
    print(f"   ❌ Error en verificación: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Solución:")
    print("   1. Verifica que el repositorio se clonó correctamente")
    print("   2. Verifica que ejecutaste 'pip install -e .'")
    print("   3. Reinicia el runtime y vuelve a intentar")

