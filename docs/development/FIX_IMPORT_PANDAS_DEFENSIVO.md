# Fix: Import Defensivo de Pandas

## Problema

Cuando pandas está corrupto o parcialmente inicializado en el entorno (común en Google Colab), BESTLIB fallaba al importar porque intentaba importar pandas al nivel del módulo y el error se propagaba.

**Error**:
```
AttributeError: partially initialized module 'pandas' has no attribute '_pandas_parser_CAPI' 
(most likely due to a circular import)
```

## Solución Aplicada

Se implementó un **import defensivo de pandas** en todos los módulos de BESTLIB que lo usan:

1. **`BESTLIB/layouts/matrix.py`**
2. **`BESTLIB/matrix.py`**
3. **`BESTLIB/layouts/reactive.py`**
4. **`BESTLIB/reactive.py`**

### Estrategia de Import Defensivo

```python
# Import de pandas de forma defensiva para evitar errores de importación circular
HAS_PANDAS = False
pd = None
try:
    # Verificar que pandas no esté parcialmente inicializado
    import sys
    if 'pandas' in sys.modules:
        # Si pandas ya está en sys.modules pero corrupto, intentar limpiarlo
        try:
            pd_test = sys.modules['pandas']
            # Intentar acceder a un atributo básico para verificar si está corrupto
            _ = pd_test.__version__
        except (AttributeError, ImportError):
            # Pandas está corrupto, limpiarlo
            del sys.modules['pandas']
            # También limpiar submódulos relacionados
            modules_to_remove = [k for k in sys.modules.keys() if k.startswith('pandas.')]
            for mod in modules_to_remove:
                try:
                    del sys.modules[mod]
                except:
                    pass
    
    # Ahora intentar importar pandas
    import pandas as pd
    # Verificar que pandas esté completamente inicializado
    _ = pd.__version__
    HAS_PANDAS = True
except (ImportError, AttributeError, ModuleNotFoundError, Exception):
    # Si pandas no está disponible o está corrupto, continuar sin él
    HAS_PANDAS = False
    pd = None
```

### Características del Fix

1. **Detección de pandas corrupto**: Verifica si pandas está en `sys.modules` pero corrupto
2. **Limpieza automática**: Si pandas está corrupto, lo elimina de `sys.modules` y sus submódulos
3. **Reimportación limpia**: Intenta importar pandas de nuevo después de limpiar
4. **Verificación**: Verifica que pandas esté completamente inicializado accediendo a `__version__`
5. **Fallback seguro**: Si todo falla, continúa sin pandas (`HAS_PANDAS = False`)

## Beneficios

✅ **BESTLIB puede importarse incluso si pandas está corrupto**
✅ **Limpia automáticamente pandas corrupto antes de importar**
✅ **No rompe la funcionalidad si pandas no está disponible**
✅ **Permite que el usuario reinicie pandas después de importar BESTLIB**

## Uso

Ahora puedes importar BESTLIB incluso si pandas está corrupto:

```python
# Esto funcionará incluso si pandas está corrupto
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
from BESTLIB.matrix import MatrixLayout

# Si pandas estaba corrupto, BESTLIB se importó sin él
# Ahora puedes limpiar y reinstalar pandas si es necesario
import sys
if 'pandas' in sys.modules:
    del sys.modules['pandas']
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith('pandas.')]
    for mod in modules_to_remove:
        try:
            del sys.modules[mod]
        except:
            pass

# Reinstalar pandas si es necesario
# !pip uninstall -y pandas
# !pip install pandas

# Ahora importar pandas
import pandas as pd
import numpy as np

# BESTLIB funcionará correctamente
layout = MatrixLayout("A")
layout.map_scatter('A', df, x_col='x', y_col='y')
layout.display()
```

## Archivos Modificados

1. **`BESTLIB/layouts/matrix.py`**: Import defensivo de pandas
2. **`BESTLIB/matrix.py`**: Import defensivo de pandas
3. **`BESTLIB/layouts/reactive.py`**: Import defensivo de pandas
4. **`BESTLIB/reactive.py`**: Import defensivo de pandas

## Nota Importante

Este fix **no soluciona el problema de pandas corrupto**, pero permite que BESTLIB se importe correctamente incluso en ese escenario. Si pandas está corrupto, el usuario aún necesitará:

1. Reiniciar el runtime/kernel, O
2. Reinstalar pandas: `!pip uninstall -y pandas && !pip install pandas`

Pero ahora BESTLIB no fallará al importarse debido a pandas corrupto.

