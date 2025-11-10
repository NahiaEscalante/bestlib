# 🚀 Guía de Instalación para Google Colab

## Problema

Google Colab tiene versiones específicas de paquetes instaladas. Si instalamos BESTLIB con dependencias automáticas, puede causar conflictos de versiones.

## Solución: Instalación Sin Dependencias ⭐

BESTLIB no instala dependencias automáticamente. Colab ya tiene todas las dependencias necesarias, por lo que solo necesitamos instalar BESTLIB:

```python
# Instalar BESTLIB sin dependencias (Colab ya tiene todo lo necesario)
!pip install --upgrade --no-deps git+https://github.com/NahiaEscalante/bestlib.git@widget_mod
```

**Ventajas:**
- ✅ No fuerza upgrades de paquetes críticos
- ✅ Compatible con las versiones de Colab
- ✅ Evita conflictos de dependencias
- ✅ Más rápido
- ✅ No modifica el entorno de Colab

## Verificación de Instalación

Después de instalar, verifica que todo funciona:

```python
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

print("✅ Instalación exitosa!")
print(f"📊 pandas: {pd.__version__}")
print(f"🔢 numpy: {np.__version__}")

try:
    import ipywidgets as widgets
    print(f"🎛️ ipywidgets: {widgets.__version__}")
except ImportError:
    print("⚠️ ipywidgets no está instalado")
```

## Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'BESTLIB'"

1. Verifica que la instalación se completó sin errores
2. Reinicia el runtime: **Runtime** → **Restart runtime**
3. Vuelve a ejecutar las celdas de instalación

### Error: "ipywidgets not found"

```python
!pip install ipywidgets --quiet
```

Luego reinicia el runtime.

### Error: Conflictos de dependencias

1. Asegúrate de usar `--no-deps` al instalar BESTLIB
2. Si persiste, reinicia el runtime completamente: **Runtime** → **Disconnect and delete runtime**
3. Vuelve a ejecutar la instalación con `--no-deps`

### Error: "Cannot connect to kernel"

Esto puede ocurrir si se forzaron upgrades de `ipykernel` o `ipython`. 

**Solución:**
1. Ve a **Runtime** → **Disconnect and delete runtime**
2. Crea un nuevo runtime
3. Instala BESTLIB con `--no-deps`: `!pip install --upgrade --no-deps git+https://github.com/NahiaEscalante/bestlib.git@widget_mod`

## Dependencias en Colab

Colab ya tiene instaladas las siguientes dependencias:

- ✅ `pandas` (versión instalada por Colab)
- ✅ `numpy` (versión instalada por Colab)
- ✅ `ipython` (versión instalada por Colab)
- ✅ `jupyter` (varios componentes)
- ✅ `ipywidgets` (generalmente presente)

BESTLIB es compatible con estas versiones. **No necesitas instalar dependencias adicionales** porque BESTLIB no las instala automáticamente y el código maneja las importaciones de forma opcional.

## Notas Importantes

1. **BESTLIB no instala dependencias automáticamente** - Esto evita conflictos
2. **Colab ya tiene todas las dependencias** - No necesitas instalar nada adicional
3. **Usa `--no-deps` siempre** - Esto evita que pip intente instalar/actualizar dependencias
4. **Reinicia el runtime** después de instalar si hay problemas
5. **El código maneja importaciones opcionales** - BESTLIB funcionará incluso si falta alguna dependencia (con funcionalidades limitadas)

## Ejemplo Completo para Colab

```python
# Paso 1: Instalar BESTLIB (sin dependencias)
!pip install --upgrade --no-deps git+https://github.com/NahiaEscalante/bestlib.git@widget_mod

# Paso 2: Importar BESTLIB
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

print("✅ BESTLIB listo para usar!")
print(f"📊 pandas: {pd.__version__}")
print(f"🔢 numpy: {np.__version__}")

# Verificar ipywidgets (opcional, pero recomendado para funcionalidades avanzadas)
try:
    import ipywidgets as widgets
    print(f"🎛️ ipywidgets: {widgets.__version__}")
except ImportError:
    print("⚠️ ipywidgets no está instalado. Algunas funcionalidades pueden no estar disponibles.")
    print("   Para instalarlo: !pip install ipywidgets")
```

---

**¿Problemas?** Abre un issue en el repositorio de GitHub con el error específico.

