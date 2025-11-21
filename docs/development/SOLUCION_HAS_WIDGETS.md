# 🔧 Solución para el Error `HAS_WIDGETS` no definido

## 📋 Problema

El error muestra que estás usando una versión instalada de BESTLIB (legacy) en lugar de la versión de desarrollo migrada:

```
/usr/local/lib/python3.12/dist-packages/BESTLIB/reactive.py in selection_widget(self)
-> 3065         if not HAS_WIDGETS:
NameError: name 'HAS_WIDGETS' is not defined
```

## ✅ Solución

### Opción 1: Usar la versión de desarrollo (RECOMENDADA)

**En Jupyter Notebook/Lab:**

1. **Agregar el path de desarrollo al inicio del notebook:**
```python
import sys
sys.path.insert(0, '/Users/nahiaescalante/Documents/2025/Visualizacion/bestlib')

# Ahora importar BESTLIB
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
```

2. **O usar `%load_ext autoreload` para recargar automáticamente:**
```python
%load_ext autoreload
%autoreload 2

import sys
sys.path.insert(0, '/Users/nahiaescalante/Documents/2025/Visualizacion/bestlib')
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
```

### Opción 2: Reinstalar en modo desarrollo

**En la terminal (antes de abrir Jupyter):**

```bash
cd /Users/nahiaescalante/Documents/2025/Visualizacion/bestlib

# Si tienes permisos de sistema, usar --user
pip3 install --user -e .

# O si estás en un entorno virtual
pip install -e .
```

**Luego reiniciar Jupyter** para que use la nueva versión.

### Opción 3: Verificar qué versión se está usando

**En Jupyter:**

```python
import BESTLIB
print(f"Ubicación: {BESTLIB.__file__}")

from BESTLIB.reactive import ReactiveMatrixLayout
print(f"Módulo: {ReactiveMatrixLayout.__module__}")

# Si muestra 'layouts.reactive', estás usando la versión correcta ✅
# Si muestra 'reactive', estás usando la versión legacy ⚠️
```

## ✅ Estado Actual

- ✅ `HAS_WIDGETS` ya está definido en `BESTLIB/layouts/reactive.py`
- ✅ El código migrado funciona correctamente
- ⚠️ Necesitas asegurarte de usar la versión de desarrollo en Jupyter

## 🧪 Prueba Rápida

```python
# En Jupyter, ejecutar esto para verificar:
import sys
sys.path.insert(0, '/Users/nahiaescalante/Documents/2025/Visualizacion/bestlib')

from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

# Crear layout
layout = ReactiveMatrixLayout("S", selection_model=SelectionModel())

# Probar selection_widget (ahora debería funcionar)
display(layout.selection_widget)  # ✅ Debería funcionar sin error
```

## 📝 Nota

El código migrado (`BESTLIB/layouts/reactive.py`) ya tiene:
- ✅ `HAS_WIDGETS` definido
- ✅ `HAS_PANDAS` definido
- ✅ Todos los imports necesarios

El problema es solo que Jupyter está usando la versión instalada (legacy) en lugar de la versión de desarrollo.

