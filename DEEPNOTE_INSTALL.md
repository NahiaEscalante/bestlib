# 🚀 Guía de Instalación para DeepNote

DeepNote es una plataforma de notebooks colaborativos similar a Google Colab. Esta guía te ayudará a instalar y usar BESTLIB en DeepNote.

## ✅ ¿Por qué DeepNote?

| Característica | DeepNote | Google Colab |
|---------------|----------|--------------|
| Soporte D3.js | ✅ Excelente | ✅ Excelente |
| Entorno Jupyter | ✅ Estándar | ✅ Estándar |
| Comunicación JS↔Python | ✅ Comms Jupyter | ✅ Comms Colab |
| Instalación de paquetes | ✅ Fácil | ✅ Fácil |
| Colaboración | ✅ En tiempo real | ⚠️ Limitada |
| **Recomendación** | **👍 Excelente opción** | **👍 También excelente** |

---

## 📦 Instalación Paso a Paso

### Paso 1: Instalar BESTLIB

En la primera celda de tu notebook en DeepNote, ejecuta:

```python
# Instalar BESTLIB desde GitHub (sin dependencias para evitar conflictos)
!pip install --upgrade --no-deps git+https://github.com/NahiaEscalante/bestlib.git@widget_mod
```

**Nota:** Usamos `--no-deps` porque DeepNote ya tiene las dependencias necesarias instaladas.

### Paso 2: Verificar Dependencias

DeepNote generalmente tiene todas las dependencias, pero verifica:

```python
# Verificar dependencias
import sys

# Verificar pandas
try:
    import pandas as pd
    print(f"✅ pandas: {pd.__version__}")
except ImportError:
    print("⚠️ pandas no está instalado")
    !pip install pandas --quiet

# Verificar numpy
try:
    import numpy as np
    print(f"✅ numpy: {np.__version__}")
except ImportError:
    print("⚠️ numpy no está instalado")
    !pip install numpy --quiet

# Verificar ipywidgets (importante para funcionalidades interactivas)
try:
    import ipywidgets as widgets
    print(f"✅ ipywidgets: {widgets.__version__}")
except ImportError:
    print("⚠️ ipywidgets no está instalado - instalando...")
    !pip install ipywidgets --quiet
    print("✅ ipywidgets instalado")
```

### Paso 3: Importar BESTLIB

```python
# Importar BESTLIB
# 🔒 La inicialización de DeepNote se hace automáticamente al importar
from BESTLIB.matrix import MatrixLayout
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

print("✅ BESTLIB instalado y listo para usar!")
print("✅ Inicialización de DeepNote completada automáticamente")
```

**Nota:** BESTLIB detecta automáticamente si estás en DeepNote y:
- ✅ Habilita `widgetsnbextension` automáticamente
- ✅ Activa `jupyterlab manager` para ipywidgets
- ✅ Registra los comms entre JS ↔ Python
- ✅ Configura el renderizado correcto

---

## 🎯 Ejemplo Completo de Instalación

Copia y pega este código en la primera celda de tu notebook:

```python
# ============================================
# INSTALACIÓN DE BESTLIB EN DEEPNOTE
# ============================================

# 1. Instalar BESTLIB (sin dependencias)
print("📦 Instalando BESTLIB...")
!pip install --upgrade --no-deps git+https://github.com/NahiaEscalante/bestlib.git@widget_mod

# 2. Verificar/instalar dependencias si es necesario
print("\n🔍 Verificando dependencias...")

# pandas
try:
    import pandas as pd
    print(f"✅ pandas: {pd.__version__}")
except ImportError:
    print("📥 Instalando pandas...")
    !pip install pandas --quiet
    import pandas as pd
    print(f"✅ pandas instalado: {pd.__version__}")

# numpy
try:
    import numpy as np
    print(f"✅ numpy: {np.__version__}")
except ImportError:
    print("📥 Instalando numpy...")
    !pip install numpy --quiet
    import numpy as np
    print(f"✅ numpy instalado: {np.__version__}")

# ipywidgets (importante para funcionalidades reactivas)
try:
    import ipywidgets as widgets
    print(f"✅ ipywidgets: {widgets.__version__}")
except ImportError:
    print("📥 Instalando ipywidgets...")
    !pip install ipywidgets --quiet
    import ipywidgets as widgets
    print(f"✅ ipywidgets instalado: {widgets.__version__}")

# 3. Importar BESTLIB
print("\n📚 Importando BESTLIB...")
from BESTLIB.matrix import MatrixLayout
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

print("\n🎉 ¡BESTLIB está listo para usar!")
print("\n💡 Ejemplo rápido:")
print("   layout = MatrixLayout('A')")
print("   layout.map_scatter('A', df, x_col='x', y_col='y')")
print("   layout.display()")
```

---

## 🎨 Ejemplo de Uso Básico

Después de la instalación, puedes usar BESTLIB normalmente:

```python
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# Crear datos de ejemplo
df = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100),
    'category': np.random.choice(['A', 'B', 'C'], 100)
})

# Crear layout
layout = MatrixLayout("""
AS
HX
""")

# Agregar gráficos
layout.map_scatter('A', df, x_col='x', y_col='y', color_col='category')
layout.map_scatter('S', df, x_col='x', y_col='y', color_col='category')
layout.map_histogram('H', df, column='x', bins=20)
layout.map_boxplot('X', df, column='y', category_col='category')

# Mostrar
# 🔒 En DeepNote, layout.display() funciona correctamente
# También puedes usar display(layout) si prefieres
layout.display()
```

**Nota importante para DeepNote:**
- `layout.display()` funciona correctamente y renderiza el contenido visual
- También puedes usar `display(layout)` - ambos métodos funcionan
- La inicialización de widgets y comms se hace automáticamente

---

## 🔄 Ejemplo con ReactiveMatrixLayout

Para funcionalidades reactivas (vistas enlazadas):

```python
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

# Crear layout reactivo
layout = ReactiveMatrixLayout("""
AS
HX
""", selection_model=SelectionModel())

layout.set_data(df)

# Agregar gráficos con enlaces
layout.add_scatter('A', x_col='x', y_col='y', color_col='category')
layout.add_scatter('S', x_col='x', y_col='y', color_col='category')
layout.add_histogram('H', column='x', linked_to='A', bins=20)
layout.add_boxplot('X', column='y', category_col='category', linked_to='S')

# Mostrar
layout.display()
```

---

## 🔧 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'BESTLIB'"

**Solución:**
1. Verifica que la instalación se completó sin errores
2. Reinicia el kernel: **Kernel** → **Restart Kernel**
3. Vuelve a ejecutar la celda de instalación

### Error: "ipywidgets not found"

**Solución:**
```python
!pip install ipywidgets --quiet
```

Luego reinicia el kernel y vuelve a importar.

### Error: "Cannot connect to kernel" o problemas de comunicación

**Solución:**
1. Verifica que el kernel esté corriendo
2. Reinicia el kernel: **Kernel** → **Restart Kernel**
3. Asegúrate de que `ipywidgets` esté instalado:
   ```python
   !pip install ipywidgets --quiet
   ```

### Los gráficos no se muestran

**Solución:**
1. Asegúrate de llamar `.display()` al final:
   ```python
   layout.display()
   ```
2. Verifica que el output de la celda no esté oculto
3. Intenta mostrar el layout explícitamente:
   ```python
   from IPython.display import display
   display(layout)
   ```

### Error: "Comm target not registered"

**Solución:**
1. Reinicia el kernel completamente
2. Ejecuta la instalación nuevamente
3. Verifica que `ipywidgets` esté instalado:
   ```python
   import ipywidgets
   print(ipywidgets.__version__)
   ```

---

## 📋 Dependencias en DeepNote

DeepNote generalmente tiene instaladas las siguientes dependencias:

- ✅ `pandas` (versión instalada por DeepNote)
- ✅ `numpy` (versión instalada por DeepNote)
- ✅ `ipython` (versión instalada por DeepNote)
- ✅ `jupyter` (varios componentes)
- ⚠️ `ipywidgets` (puede necesitar instalación manual)

**BESTLIB es compatible con estas versiones.** Usamos `--no-deps` para evitar conflictos de versiones.

---

## 🎯 Diferencias con Colab

| Aspecto | DeepNote | Colab |
|---------|----------|-------|
| Sistema de comms | Jupyter estándar | Google Colab comms |
| Detección automática | ✅ Sí | ✅ Sí |
| Instalación | `--no-deps` recomendado | `--no-deps` recomendado |
| ipywidgets | Puede necesitar instalación | Generalmente ya instalado |
| Reinicio de kernel | Kernel → Restart | Runtime → Restart runtime |

---

## 💡 Tips y Mejores Prácticas

### 1. **Instalación en Primera Celda**
Siempre instala BESTLIB en la primera celda del notebook para evitar problemas de importación.

### 2. **Reiniciar Kernel Después de Instalación**
Después de instalar, reinicia el kernel para asegurar que los cambios se apliquen:
- **Kernel** → **Restart Kernel**

### 3. **Verificar Versiones**
Si tienes problemas, verifica las versiones:
```python
import pandas as pd
import numpy as np
import ipywidgets as widgets
print(f"pandas: {pd.__version__}")
print(f"numpy: {np.__version__}")
print(f"ipywidgets: {widgets.__version__}")
```

### 4. **Usar `--no-deps`**
Siempre usa `--no-deps` al instalar BESTLIB para evitar conflictos con las versiones de DeepNote.

### 5. **Manejo de Errores**
Si algo no funciona:
1. Reinicia el kernel
2. Vuelve a ejecutar la instalación
3. Verifica que todas las dependencias estén instaladas
4. Revisa los mensajes de error en la consola del navegador (F12)

---

## 📚 Recursos Adicionales

- **Documentación completa:** Ver `README.md` en el repositorio
- **Ejemplos:** Ver carpeta `examples/` en el repositorio
- **Guía de Colab:** Ver `COLAB_INSTALL.md` (similar pero para Colab)
- **Estructura modular:** Ver `ESTRUCTURA_MODULAR_ANALISIS.md`

---

## ✅ Checklist de Instalación

Antes de empezar a usar BESTLIB, verifica:

- [ ] BESTLIB instalado con `--no-deps`
- [ ] `pandas` disponible
- [ ] `numpy` disponible
- [ ] `ipywidgets` instalado (si usas funcionalidades reactivas)
- [ ] Kernel reiniciado después de la instalación
- [ ] Importación exitosa: `from BESTLIB.matrix import MatrixLayout`
- [ ] Primer gráfico renderizado correctamente

---

## 🎉 ¡Listo!

Una vez completada la instalación, puedes usar todas las funcionalidades de BESTLIB en DeepNote:

- ✅ Gráficos interactivos con D3.js
- ✅ Layouts ASCII personalizables
- ✅ Vistas enlazadas reactivas
- ✅ Comunicación bidireccional Python ↔ JavaScript
- ✅ Selección de datos y callbacks

**¿Problemas?** Abre un issue en el repositorio de GitHub con:
- El error específico
- Versiones de pandas, numpy, ipywidgets
- Pasos para reproducir el problema

