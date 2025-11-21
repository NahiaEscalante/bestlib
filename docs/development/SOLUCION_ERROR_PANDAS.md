# Solución: Error de Importación de Pandas

## Error Reportado

```
AttributeError: partially initialized module 'pandas' has no attribute '_pandas_parser_CAPI' 
(most likely due to a circular import)
```

## Causa

Este error **NO está relacionado con los cambios de BESTLIB**. Es un problema común en Google Colab y entornos Jupyter cuando:

1. **Pandas está corrupto o mal instalado**
2. **Hay múltiples versiones de pandas instaladas**
3. **El kernel de Python necesita reiniciarse**
4. **Hay un conflicto de módulos en el entorno**

## Soluciones

### Solución 1: Reiniciar el Kernel (RECOMENDADO)

En Google Colab:
1. Ve a **Runtime → Restart runtime**
2. O ejecuta: `exit()` y reinicia el kernel

En Jupyter Notebook:
1. Ve a **Kernel → Restart Kernel**
2. O presiona `Ctrl+M` y luego `0` `0`

Luego vuelve a ejecutar tus imports:

```python
import pandas as pd
import numpy as np
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
from BESTLIB.matrix import MatrixLayout
MatrixLayout.set_debug(True)
```

### Solución 2: Reinstalar Pandas

En Google Colab, ejecuta esto en una celda:

```python
!pip uninstall -y pandas
!pip install pandas
```

Luego reinicia el runtime y vuelve a importar.

### Solución 3: Importar BESTLIB ANTES de Pandas

A veces cambiar el orden de imports ayuda:

```python
# Importar BESTLIB primero
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
from BESTLIB.matrix import MatrixLayout

# Luego importar pandas
import pandas as pd
import numpy as np

MatrixLayout.set_debug(True)
```

### Solución 4: Verificar Instalación de Pandas

```python
import sys
print(f"Python: {sys.version}")
print(f"Pandas path: {sys.modules.get('pandas', 'No importado')}")

# Intentar importar pandas
try:
    import pandas as pd
    print(f"✅ Pandas version: {pd.__version__}")
except Exception as e:
    print(f"❌ Error: {e}")
    print("💡 Solución: Reinicia el runtime y reinstala pandas")
```

### Solución 5: Limpiar Cache de Python

En Google Colab:

```python
import sys
import importlib

# Limpiar cache de pandas si existe
if 'pandas' in sys.modules:
    del sys.modules['pandas']
    
# Limpiar cache de BESTLIB si existe
for module_name in list(sys.modules.keys()):
    if module_name.startswith('BESTLIB'):
        del sys.modules[module_name]

# Ahora importar
import pandas as pd
import numpy as np
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
from BESTLIB.matrix import MatrixLayout
```

## Verificación

Después de aplicar una solución, verifica que todo funciona:

```python
# Test básico
import pandas as pd
import numpy as np
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
from BESTLIB.matrix import MatrixLayout

print("✅ Todos los imports funcionaron correctamente")

# Test de MatrixLayout
MatrixLayout.set_debug(True)
print(f"✅ MatrixLayout._debug = {MatrixLayout._debug}")

# Test de métodos
print(f"✅ map_histogram disponible: {hasattr(MatrixLayout, 'map_histogram')}")
print(f"✅ map_pie disponible: {hasattr(MatrixLayout, 'map_pie')}")
print(f"✅ map_boxplot disponible: {hasattr(MatrixLayout, 'map_boxplot')}")
```

## Nota Importante

**Este error NO es causado por BESTLIB**. BESTLIB importa pandas de forma segura dentro de bloques `try-except`, por lo que no puede causar este tipo de errores.

El problema es del entorno de Python/Colab. La solución más común y efectiva es **reiniciar el runtime/kernel**.

## Si el Problema Persiste

Si después de reiniciar el runtime el problema continúa:

1. **Verifica la versión de pandas**:
   ```python
   !pip show pandas
   ```

2. **Reinstala pandas desde cero**:
   ```python
   !pip uninstall -y pandas numpy
   !pip install pandas numpy
   ```

3. **Verifica que no hay conflictos**:
   ```python
   import sys
   print([m for m in sys.modules.keys() if 'pandas' in m.lower()])
   ```

4. **Crea un nuevo notebook/runtime** si nada funciona

