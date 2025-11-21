# Guía Completa: Usar BESTLIB en Google Colab

## 📋 Instalación en Google Colab

### Paso 1: Clonar el Repositorio

```python
# Si es la primera vez o quieres actualizar
!git clone https://github.com/tu-usuario/bestlib.git
# O si ya está clonado y quieres actualizar:
# !cd bestlib && git pull
```

**Nota**: Reemplaza `tu-usuario` con tu usuario de GitHub, o usa la URL completa de tu repositorio.

### Paso 2: Instalar en Modo Editable

```python
# Cambiar al directorio e instalar
!cd bestlib && pip install -e . --force-reinstall --no-deps
```

**Explicación**:
- `-e` = modo editable (los cambios en el código se reflejan sin reinstalar)
- `--force-reinstall` = fuerza la reinstalación para aplicar los cambios en `setup.py`
- `--no-deps` = no instala dependencias automáticamente (BESTLIB maneja imports opcionales)

### Paso 3: Instalar Dependencias Opcionales

```python
# Dependencias recomendadas para BESTLIB
!pip install pandas numpy scipy ipython ipywidgets scikit-learn
```

**Nota**: Estas son opcionales, pero necesarias para:
- `pandas`: Trabajar con DataFrames
- `numpy`: Cálculos numéricos (histogramas, KDE, etc.)
- `scipy`: KDE, Q-Q plots (opcional pero recomendado)
- `ipython`, `ipywidgets`: Para Jupyter/Colab
- `scikit-learn`: Para confusion matrix (opcional)

### Paso 4: Reiniciar el Runtime

**MUY IMPORTANTE**: Después de instalar, debes reiniciar el runtime:

1. Ve a: **Runtime → Restart runtime**
2. O ejecuta: `exit()` (esto cerrará la sesión)

**¿Por qué?**: Python carga los módulos en memoria. Al reinstalar, necesitas reiniciar para que Python cargue la nueva versión con los subpaquetes correctos.

### Paso 5: Verificar la Instalación

```python
# Verificar que BESTLIB está instalado correctamente
import BESTLIB
print(f"✅ BESTLIB ubicado en: {BESTLIB.__file__}")

# Verificar que charts se puede importar
from BESTLIB.charts import ChartRegistry
from BESTLIB.charts.kde import KdeChart
print("✅ Charts importado correctamente")

# Verificar que ChartRegistry conoce los gráficos
chart = ChartRegistry.get('kde')
print(f"✅ KDE registrado: {chart}")
```

## 🚀 Uso Básico

### Ejemplo 1: Gráfico Simple (Scatter)

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
layout = MatrixLayout("S")
layout.map_scatter('S', df, x_col='x', y_col='y', color_col='category')
layout.display()
```

### Ejemplo 2: Nuevos Gráficos (KDE, Distplot, etc.)

```python
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# Activar debug para ver errores si hay problemas
MatrixLayout.set_debug(True)

# Crear datos
df_value = pd.DataFrame({
    'value': np.random.normal(5.8, 0.8, 150)
})

# KDE
layout = MatrixLayout("K")
layout.map_kde("K", df_value, column="value")
layout.display()
```

### Ejemplo 3: Matriz con Múltiples Gráficos

```python
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# Cargar datos (ejemplo con Iris)
from sklearn.datasets import load_iris
iris = load_iris()
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['species'] = iris.target_names[iris.target]

# Preparar datos
df_value = df[['sepal_length']].rename(columns={'sepal_length': 'value'})
df_hist2d = df[['sepal_length', 'petal_length']].rename(
    columns={'sepal_length': 'x', 'petal_length': 'y'}
)

# Crear matriz 2x2
layout = MatrixLayout("""
KD
HE
""")

layout.map_kde("K", df_value, column="value")
layout.map_distplot("D", df_value, column="value", bins=30, kde=True, rug=True)
layout.map_hist2d("H", df_hist2d, x_col="x", y_col="y", bins=20)
layout.map_ecdf("E", df_value, column="value")

layout.display()
```

## 🔧 Solución de Problemas

### Problema 1: "ModuleNotFoundError: No module named 'BESTLIB.charts'"

**Solución**:
```python
# 1. Verificar que estás en el directorio correcto
!pwd
!ls -la bestlib/BESTLIB/charts/

# 2. Reinstalar
!cd bestlib && pip install -e . --force-reinstall

# 3. REINICIAR RUNTIME (Runtime → Restart runtime)

# 4. Verificar
from BESTLIB.charts import ChartRegistry
```

### Problema 2: "Los gráficos aparecen vacíos (data_length: 0)"

**Solución**:
```python
# Activar debug para ver errores reales
from BESTLIB.matrix import MatrixLayout
MatrixLayout.set_debug(True)

# Intentar de nuevo
layout = MatrixLayout("K")
layout.map_kde("K", df_value, column="value")
layout.display()

# Revisa la consola de Python para ver los errores específicos
```

### Problema 3: "Los gráficos muestran [object Object]"

**Solución**: Esto significa que D3.js no está cargado. BESTLIB debería cargarlo automáticamente en Colab, pero si persiste:

```python
# Verificar que los assets se cargan
from BESTLIB.render.assets import AssetManager
AssetManager.ensure_colab_assets_loaded()

# Luego renderizar
layout.display()
```

### Problema 4: "Los gráficos no se renderizan después de reinstalar"

**Solución**:
1. **Reinicia el runtime** (Runtime → Restart runtime)
2. **Vuelve a ejecutar** todas las celdas desde el principio
3. **Verifica** que no hay errores de importación

## 📝 Script Completo de Instalación (Copia y Pega)

```python
# ============================================================================
# INSTALACIÓN COMPLETA DE BESTLIB EN COLAB
# ============================================================================

# 1. Clonar repositorio (ajusta la URL)
!git clone https://github.com/tu-usuario/bestlib.git

# 2. Instalar BESTLIB
!cd bestlib && pip install -e . --force-reinstall --no-deps

# 3. Instalar dependencias
!pip install pandas numpy scipy ipython ipywidgets

# 4. Verificar instalación
import sys
sys.path.insert(0, '/content/bestlib')

import BESTLIB
print(f"✅ BESTLIB: {BESTLIB.__file__}")

from BESTLIB.charts import ChartRegistry
from BESTLIB.charts.kde import KdeChart
print("✅ Charts importado correctamente")

# 5. IMPORTANTE: Reiniciar runtime después de esto
# Runtime → Restart runtime

print("\n⚠️  IMPORTANTE: Reinicia el runtime ahora (Runtime → Restart runtime)")
print("⚠️  Luego ejecuta las celdas de uso normalmente")
```

## 🎯 Ejemplo Completo Funcional

```python
# ============================================================================
# EJEMPLO COMPLETO: Todos los Nuevos Gráficos
# ============================================================================

import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# Activar debug (opcional, para ver logs)
MatrixLayout.set_debug(True)

# Crear datos de ejemplo
np.random.seed(42)
df = pd.DataFrame({
    'sepal_length': np.random.normal(5.8, 0.8, 150),
    'sepal_width': np.random.normal(3.0, 0.4, 150),
    'petal_length': np.random.normal(3.7, 1.7, 150),
    'petal_width': np.random.normal(1.2, 0.8, 150),
    'species': np.random.choice(['setosa', 'versicolor', 'virginica'], 150)
})

# Preparar datos
df_value = df[['sepal_length']].rename(columns={'sepal_length': 'value'})
df_ridge = df[['species', 'sepal_width']].rename(
    columns={'species': 'category', 'sepal_width': 'value'}
)
df_hist2d = df[['sepal_length', 'petal_length']].rename(
    columns={'sepal_length': 'x', 'petal_length': 'y'}
)
df_polar = pd.DataFrame({
    'angle': np.linspace(0, 2*np.pi, len(df)),
    'radius': df['petal_length']
})
df_funnel = df['species'].value_counts().reset_index()
df_funnel.columns = ['stage', 'value']

# Crear layout 3x3
layout = MatrixLayout("""
KDR
QEH
PRF
""")

# Agregar gráficos
layout.map_kde("K", df_value, column="value")
layout.map_distplot("D", df_value, column="value", bins=30, kde=True, rug=True)
layout.map_rug("R", df_value, column="value", axis='x')
layout.map_qqplot("Q", df_value, column="value", dist='norm')
layout.map_ecdf("E", df_value, column="value")
layout.map_hist2d("H", df_hist2d, x_col="x", y_col="y", bins=20)
layout.map_polar("P", df_polar, angle_col="angle", radius_col="radius")
layout.map_ridgeline("I", df_ridge, column="value", category_col="category")  # Nota: 'I' en lugar de 'R' duplicado
layout.map_funnel("F", df_funnel, stage_col="stage", value_col="value")

# Renderizar
layout.display()
```

## ⚠️ Notas Importantes

1. **Siempre reinicia el runtime** después de instalar o reinstalar
2. **Ejecuta las celdas en orden** (instalación primero, luego uso)
3. **Si hay errores**, activa debug con `MatrixLayout.set_debug(True)`
4. **Revisa la consola del navegador** (F12) para ver logs de JavaScript
5. **Los gráficos nuevos requieren datos numéricos válidos**

## 🔍 Verificación Rápida

Si quieres verificar rápidamente que todo funciona:

```python
# Test rápido
from BESTLIB.charts.kde import KdeChart
import pandas as pd

df = pd.DataFrame({"value": [5.1, 4.9, 4.7, 4.6, 5.0]})
chart = KdeChart()
spec = chart.get_spec(df, column="value")

print(f"✅ Spec generado: type={spec.get('type')}")
print(f"✅ Data length: {len(spec.get('data', []))}")

if len(spec.get('data', [])) > 0:
    print("✅ ¡Todo funciona correctamente!")
else:
    print("⚠️  Data está vacío, revisa los logs con debug=True")
```

