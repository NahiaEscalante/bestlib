# ✅ Solución: Error `ModuleNotFoundError: No module named 'BESTLIB.layouts'`

## 🔍 Problema

Si ves este error:
```
ModuleNotFoundError: No module named 'BESTLIB.layouts'
```

Significa que algo está intentando importar desde `BESTLIB.layouts` pero ese módulo no está disponible o no está en el path.

---

## ✅ Solución: Usar Import Directo

**NO uses:**
```python
from BESTLIB.layouts import MatrixLayout  # ❌ Puede fallar
```

**USA:**
```python
from BESTLIB.matrix import MatrixLayout  # ✅ Siempre funciona
```

---

## 📝 Código Correcto para Probar Nuevos Gráficos

```python
# ✅ FORMA CORRECTA
import pandas as pd
from BESTLIB.matrix import MatrixLayout  # Import directo desde matrix

# Crear datos
df = pd.DataFrame({
    'sepal_length': [5.1, 4.9, 4.7, 4.6, 5.0],
    'sepal_width': [3.5, 3.0, 3.2, 3.1, 3.6]
})

# Crear layout
layout = MatrixLayout("L")

# Agregar gráfico nuevo
layout.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,
    markers=True
)

# Mostrar
layout.display()
```

---

## 🔧 Si Aún Ves el Error

### Opción 1: Verificar que BESTLIB está instalado

```python
import sys
import os

# Verificar que BESTLIB está en el path
bestlib_path = None
for p in sys.path:
    if 'bestlib' in p.lower() or 'BESTLIB' in p:
        bestlib_path = p
        break

if bestlib_path:
    print(f"✅ BESTLIB encontrado en: {bestlib_path}")
else:
    print("❌ BESTLIB no está en el path")
    print("Paths disponibles:")
    for p in sys.path[:5]:
        print(f"  - {p}")
```

### Opción 2: Agregar BESTLIB al path manualmente

```python
import sys
import os

# Agregar BESTLIB al path (ajusta la ruta según tu caso)
bestlib_dir = "/content/bestlib"  # O la ruta donde esté BESTLIB
if os.path.exists(bestlib_dir):
    sys.path.insert(0, bestlib_dir)
    print(f"✅ BESTLIB agregado al path: {bestlib_dir}")
else:
    print(f"❌ BESTLIB no encontrado en: {bestlib_dir}")

# Ahora importar
from BESTLIB.matrix import MatrixLayout
```

### Opción 3: Reinstalar BESTLIB

```bash
# En Colab/Jupyter
!pip install -e . --force-reinstall

# Reiniciar kernel
# Runtime → Restart runtime
```

---

## ✅ Verificación Final

Ejecuta esto para verificar que todo funciona:

```python
from BESTLIB.matrix import MatrixLayout

# Verificar métodos disponibles
methods = [m for m in dir(MatrixLayout) if m.startswith('map_')]
print(f"✅ Métodos map_* disponibles: {len(methods)}")

# Verificar métodos nuevos
new_charts = ['map_line_plot', 'map_horizontal_bar', 'map_hexbin']
for chart in new_charts:
    if chart in methods:
        print(f"   ✅ {chart}")
    else:
        print(f"   ❌ {chart} NO disponible")

# Crear layout de prueba
layout = MatrixLayout("L")
print("✅ Layout creado correctamente")
```

---

## 📌 Nota Importante

**Siempre usa:**
```python
from BESTLIB.matrix import MatrixLayout
```

**NO uses:**
```python
from BESTLIB.layouts import MatrixLayout  # Puede fallar
from BESTLIB import MatrixLayout  # Puede intentar importar desde layouts
```

El import directo desde `BESTLIB.matrix` siempre funciona porque es el módulo legacy que está garantizado que existe.

---

**Si sigues teniendo problemas, comparte:**
1. El error completo
2. Cómo estás importando BESTLIB
3. Si estás en Colab, Jupyter, o VSCode

