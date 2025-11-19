# 🎯 Solución: NameError con ChartRegistry en Notebooks

## ❌ Error Común

```python
# CELDA 1: Intentar usar ChartRegistry sin importar
scatter = ChartRegistry.get('scatter')  # ❌ NameError: name 'ChartRegistry' is not defined
```

## ✅ Solución Correcta

**IMPORTANTE:** Siempre ejecuta la celda de importación ANTES de usar `ChartRegistry`.

```python
# ============================================
# CELDA 1: IMPORTAR (EJECUTAR PRIMERO) ⚠️
# ============================================
from BESTLIB import ChartRegistry

# Verificar que se importó correctamente
print(f"✅ ChartRegistry: {ChartRegistry is not None}")
print(f"📊 Tipos disponibles: {ChartRegistry.list_types()}")

# ============================================
# CELDA 2: USAR ChartRegistry (después de importar)
# ============================================
# Ahora SÍ puedes usar ChartRegistry
scatter = ChartRegistry.get('scatter')
print(f"✅ Scatter obtenido: {scatter}")
```

## 📝 Ejemplo Completo Paso a Paso

### Paso 1: Configuración del Entorno

```python
# CELDA 1: Configurar path y verificar estructura
import sys
import os
from pathlib import Path

# Detectar si estamos en Colab
try:
    import google.colab
    IN_COLAB = True
    print("🌐 Google Colab detectado")
except ImportError:
    IN_COLAB = False
    print("💻 Entorno local")

# Agregar ruta del proyecto si es necesario
if IN_COLAB:
    # Ajustar según tu configuración en Colab
    project_path = "/content/bestlib"  # Cambiar si es diferente
    if project_path not in sys.path:
        sys.path.insert(0, project_path)
else:
    # Para local, detectar automáticamente
    current_dir = Path.cwd()
    project_root = current_dir.parent if current_dir.name == 'examples' else current_dir
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

print(f"📁 Ruta del proyecto: {project_root if not IN_COLAB else project_path}")
```

### Paso 2: Importar ChartRegistry

```python
# CELDA 2: Importar ChartRegistry (CRÍTICO - ejecutar antes de usar)
try:
    from BESTLIB import ChartRegistry
    print("✅ ChartRegistry importado correctamente")
    print(f"   Tipo: {type(ChartRegistry)}")
    print(f"   Tipos disponibles: {ChartRegistry.list_types()}")
except ImportError as e:
    print(f"❌ Error al importar: {e}")
    print("\n💡 Verifica:")
    print("   1. Que la ruta del proyecto esté en sys.path")
    print("   2. Que la estructura BESTLIB/charts/ exista")
    print("   3. Reinicia el kernel si es necesario")
    raise
```

### Paso 3: Usar ChartRegistry

```python
# CELDA 3: Ahora puedes usar ChartRegistry
import pandas as pd
import numpy as np

# Crear datos
np.random.seed(42)
df = pd.DataFrame({
    'edad': np.random.randint(20, 60, 100),
    'salario': np.random.randint(3000, 15000, 100),
    'departamento': np.random.choice(['IT', 'Sales', 'Finance'], 100)
})

# Obtener scatter chart desde registry
scatter = ChartRegistry.get('scatter')

# Generar spec
spec = scatter.get_spec(
    data=df,
    x_col='edad',
    y_col='salario',
    category_col='departamento',
    interactive=True,
    axes=True
)

print(f"✅ Spec generado: {type(spec)}")
print(f"   Keys: {list(spec.keys()) if isinstance(spec, dict) else 'N/A'}")
```

### Paso 4: Usar con MatrixLayout

```python
# CELDA 4: Configurar y mostrar layout
from BESTLIB.matrix import MatrixLayout

MatrixLayout.map({
    'S': spec
})

layout = MatrixLayout("S")
layout.display()
```

## 🔍 Diagnóstico Rápido

Si tienes problemas, ejecuta este código de diagnóstico:

```python
# Diagnóstico completo
import sys
print("📋 Diagnóstico de Importación")
print("=" * 50)

# 1. Verificar sys.path
print("\n1. sys.path:")
for i, path in enumerate(sys.path[:5]):  # Primeros 5
    print(f"   {i+1}. {path}")

# 2. Verificar estructura
print("\n2. Estructura BESTLIB:")
try:
    from pathlib import Path
    bestlib_path = None
    for path in sys.path:
        test_path = Path(path) / "BESTLIB"
        if test_path.exists():
            bestlib_path = test_path
            break
    
    if bestlib_path:
        print(f"   ✅ BESTLIB encontrado en: {bestlib_path}")
        charts_path = bestlib_path / "charts"
        registry_path = charts_path / "registry.py"
        print(f"   ✅ charts/ existe: {charts_path.exists()}")
        print(f"   ✅ registry.py existe: {registry_path.exists()}")
    else:
        print("   ❌ BESTLIB no encontrado en sys.path")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Intentar importar
print("\n3. Intentar importar:")
try:
    from BESTLIB import ChartRegistry
    print(f"   ✅ ChartRegistry importado: {ChartRegistry}")
    print(f"   ✅ Tipos: {ChartRegistry.list_types()}")
except ImportError as e:
    print(f"   ❌ ImportError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
```

## ✅ Checklist de Solución

Si `ChartRegistry` no está definido:

- [ ] **Ejecutaste la celda de importación?** 
  ```python
  from BESTLIB import ChartRegistry
  ```

- [ ] **Verificaste que el import funcionó?**
  ```python
  print(ChartRegistry)  # Debe mostrar la clase
  ```

- [ ] **Está BESTLIB en sys.path?**
  ```python
  import sys
  print([p for p in sys.path if 'bestlib' in p.lower()])
  ```

- [ ] **Reiniciaste el kernel?** (Kernel → Restart)

- [ ] **Verificaste la estructura?**
  ```
  BESTLIB/
    charts/
      registry.py  ← Debe existir
      __init__.py
  ```

## 🚀 Ejemplo Mínimo Funcional

```python
# CELDA ÚNICA: Todo en una celda (para evitar problemas de orden)
from BESTLIB import ChartRegistry, MatrixLayout
import pandas as pd
import numpy as np

# Verificar import
assert ChartRegistry is not None, "ChartRegistry no se importó"

# Datos
df = pd.DataFrame({
    'x': np.random.randn(50),
    'y': np.random.randn(50)
})

# Usar ChartRegistry
scatter = ChartRegistry.get('scatter')
spec = scatter.get_spec(data=df, x_col='x', y_col='y', interactive=True)

# Mostrar
MatrixLayout.map({'S': spec})
MatrixLayout("S").display()
```

## 💡 Notas Importantes

1. **Orden de ejecución**: Las celdas deben ejecutarse en orden
2. **Kernel**: Si cambias imports, reinicia el kernel
3. **Path**: Asegúrate de que BESTLIB esté en `sys.path`
4. **Verificación**: Siempre verifica que el import funcionó antes de usar

