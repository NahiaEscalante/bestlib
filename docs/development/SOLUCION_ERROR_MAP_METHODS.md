# 🔧 Solución: AttributeError con map_line_plot y otros métodos nuevos

## ❌ Error que estás viendo:

```python
AttributeError: 'MatrixLayout' object has no attribute 'map_line_plot'
```

## ✅ Solución: Recargar el módulo

El problema es que Python/Jupyter tiene el módulo en caché. Necesitas recargarlo.

### Opción 1: Reiniciar el Kernel (Recomendado)

En Jupyter/Colab:
1. **Kernel → Restart Kernel** (o presiona el botón de reiniciar)
2. Vuelve a ejecutar todas las celdas desde el principio

### Opción 2: Recargar el módulo sin reiniciar

Agrega esto al inicio de tu notebook:

```python
import importlib
import sys

# Si ya importaste BESTLIB, recárgalo
if 'BESTLIB' in sys.modules:
    import BESTLIB
    importlib.reload(BESTLIB)
    if 'BESTLIB.matrix' in sys.modules:
        importlib.reload(sys.modules['BESTLIB.matrix'])
    if 'BESTLIB.layouts.matrix' in sys.modules:
        importlib.reload(sys.modules['BESTLIB.layouts.matrix'])

# Ahora importa normalmente
from BESTLIB.matrix import MatrixLayout
# O mejor aún:
from BESTLIB import MatrixLayout
```

### Opción 3: Usar importlib.reload directamente

```python
from BESTLIB.matrix import MatrixLayout
import importlib
import BESTLIB.matrix
importlib.reload(BESTLIB.matrix)
from BESTLIB.matrix import MatrixLayout  # Re-importar después de reload
```

## 📝 Código de ejemplo corregido

```python
# Opción A: Reiniciar kernel y usar esto
from BESTLIB import MatrixLayout  # Mejor usar desde __init__.py
import pandas as pd

df = pd.read_csv('iris.csv')  # O tu DataFrame

layout = MatrixLayout("L")
layout.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,  # Nota: strokeWidth (camelCase), no stroke_width
    markers=True
)
layout.display()
```

## ⚠️ Notas importantes:

1. **Usa `strokeWidth` (camelCase)**, no `stroke_width` (snake_case)
2. **Reinicia el kernel** después de instalar/actualizar BESTLIB
3. **Usa `from BESTLIB import MatrixLayout`** en lugar de `from BESTLIB.matrix import MatrixLayout` para mejor compatibilidad

## ✅ Verificación

Para verificar que los métodos están disponibles:

```python
from BESTLIB import MatrixLayout

# Listar todos los métodos map_*
methods = [m for m in dir(MatrixLayout) if m.startswith('map_')]
print("Métodos disponibles:")
for m in sorted(methods):
    print(f"  - {m}")
```

Deberías ver:
- `map_line_plot`
- `map_horizontal_bar`
- `map_hexbin`
- `map_errorbars`
- `map_fill_between`
- `map_step`

## 🔄 Si el problema persiste:

1. **Desinstala y reinstala BESTLIB:**
   ```bash
   pip uninstall bestlib -y
   pip install -e .
   ```

2. **Verifica que estás en el directorio correcto:**
   ```python
   import BESTLIB
   print(BESTLIB.__file__)  # Debe apuntar a tu instalación local
   ```

3. **Verifica la versión del código:**
   ```python
   import inspect
   from BESTLIB.matrix import MatrixLayout
   print(inspect.getfile(MatrixLayout))
   # Debe mostrar: .../BESTLIB/matrix.py o .../BESTLIB/layouts/matrix.py
   ```

## 📚 Ejemplo completo funcionando:

```python
# Reinicia el kernel primero, luego ejecuta esto:

from BESTLIB import MatrixLayout
import pandas as pd

# Cargar datos
df = pd.read_csv('iris.csv')

# Line Plot
layout1 = MatrixLayout("L")
layout1.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,
    markers=True,
    xLabel="Sepal Length",
    yLabel="Sepal Width"
)
layout1.display()

# Horizontal Bar
layout2 = MatrixLayout("B")
layout2.map_horizontal_bar(
    "B",
    df,
    category_col="species",
    xLabel="Count",
    yLabel="Species"
)
layout2.display()
```

---

**Solución más rápida: Reinicia el kernel y vuelve a ejecutar** 🚀

