# 🎯 Ejemplo: Uso de ChartRegistry

Este ejemplo muestra cómo importar y usar `ChartRegistry` correctamente.

## ⚠️ Solución al Error: `NameError: name 'ChartRegistry' is not defined`

**Causa del error:**
El error ocurre cuando intentas usar `ChartRegistry` sin haberlo importado correctamente en la celda del notebook.

**Solución:**
Asegúrate de ejecutar la celda de importación ANTES de usar `ChartRegistry`.

## 📝 Ejemplo 1: Importación Correcta

```python
# CELDA 1: Importar ChartRegistry
from BESTLIB import ChartRegistry

# Verificar que se importó correctamente
print(f"✅ ChartRegistry importado: {ChartRegistry is not None}")
print(f"📊 Tipos disponibles: {ChartRegistry.list_types()}")

# CELDA 2: Usar ChartRegistry (después de importar)
scatter = ChartRegistry.get('scatter')
print(f"✅ Scatter chart obtenido: {scatter}")
```

## 📝 Ejemplo 2: Uso Completo con ChartRegistry

```python
# ============================================
# CELDA 1: Importar librerías
# ============================================
from BESTLIB import ChartRegistry, MatrixLayout
import pandas as pd
import numpy as np

# Verificar importación
print("✅ Imports exitosos:")
print(f"  - ChartRegistry: {ChartRegistry is not None}")
print(f"  - Tipos disponibles: {ChartRegistry.list_types()}")

# ============================================
# CELDA 2: Crear datos
# ============================================
np.random.seed(42)
df = pd.DataFrame({
    'edad': np.random.randint(20, 60, 100),
    'salario': np.random.randint(3000, 15000, 100),
    'departamento': np.random.choice(['IT', 'Sales', 'Finance'], 100)
})

# ============================================
# CELDA 3: Obtener gráfico desde registry
# ============================================
# Obtener scatter chart desde registry
scatter = ChartRegistry.get('scatter')

# Generar spec usando el método get_spec()
scatter_spec = scatter.get_spec(
    data=df,
    x_col='edad',
    y_col='salario',
    category_col='departamento',
    interactive=True,
    axes=True
)

# Configurar en MatrixLayout
MatrixLayout.map({
    'S': scatter_spec
})

# Crear y mostrar layout
layout = MatrixLayout("S")
layout.display()
```

## 📝 Ejemplo 3: Múltiples Gráficos con ChartRegistry

```python
# ============================================
# CELDA 1: Importar (IMPORTANTE: Ejecutar primero)
# ============================================
from BESTLIB import ChartRegistry, MatrixLayout
import pandas as pd
import numpy as np

# ============================================
# CELDA 2: Datos
# ============================================
np.random.seed(42)
df = pd.DataFrame({
    'edad': np.random.randint(20, 60, 200),
    'salario': np.random.randint(3000, 15000, 200),
    'departamento': np.random.choice(['IT', 'Sales', 'Finance'], 200)
})

# ============================================
# CELDA 3: Crear specs usando ChartRegistry
# ============================================
# Scatter
scatter = ChartRegistry.get('scatter')
scatter_spec = scatter.get_spec(
    data=df,
    x_col='edad',
    y_col='salario',
    category_col='departamento',
    interactive=True,
    axes=True
)

# Bar chart
bar = ChartRegistry.get('bar')
bar_spec = bar.get_spec(
    data=df,
    category_col='departamento',
    axes=True
)

# Histogram
hist = ChartRegistry.get('histogram')
hist_spec = hist.get_spec(
    data=df,
    column='edad',
    bins=20,
    axes=True
)

# Pie chart
pie = ChartRegistry.get('pie')
pie_spec = pie.get_spec(
    data=df,
    category_col='departamento'
)

# ============================================
# CELDA 4: Configurar layout
# ============================================
MatrixLayout.map({
    'S': scatter_spec,
    'B': bar_spec,
    'H': hist_spec,
    'P': pie_spec
})

layout = MatrixLayout("""
SB
HP
""")

layout.display()
```

## 🔍 Verificación de Importación

Si tienes problemas, usa este código para diagnosticar:

```python
# Diagnóstico de importación
try:
    from BESTLIB import ChartRegistry
    print("✅ ChartRegistry importado correctamente")
    print(f"   Tipo: {type(ChartRegistry)}")
    print(f"   Métodos: {[m for m in dir(ChartRegistry) if not m.startswith('_')]}")
    print(f"   Tipos registrados: {ChartRegistry.list_types()}")
except ImportError as e:
    print(f"❌ Error al importar: {e}")
    print("\n💡 Soluciones:")
    print("1. Verifica que estés en el directorio correcto")
    print("2. Asegúrate de que BESTLIB esté en sys.path")
    print("3. Reinicia el kernel del notebook")
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    import traceback
    traceback.print_exc()
```

## 📋 Tabla de Tipos Disponibles en ChartRegistry

| Tipo | Nombre en Registry | Parámetros Principales |
|------|-------------------|------------------------|
| Scatter Plot | `'scatter'` | `x_col`, `y_col`, `category_col`, `interactive`, `axes` |
| Bar Chart | `'bar'` | `category_col`, `value_col`, `axes` |
| Histogram | `'histogram'` | `column`, `bins`, `axes` |
| Boxplot | `'boxplot'` | `column`, `category_col`, `axes` |
| Heatmap | `'heatmap'` | `data_matrix` o DataFrame numérico |
| Line Chart | `'line'` | `x_col`, `y_col`, `axes` |
| Pie Chart | `'pie'` | `category_col` |
| Violin Plot | `'violin'` | `column`, `category_col` |
| Grouped Bar | `'grouped_bar'` | `category_col`, `group_col`, `value_col` |

## ✅ Checklist de Solución de Problemas

Si `ChartRegistry` no está definido:

1. ✅ **Ejecuta la celda de importación primero:**
   ```python
   from BESTLIB import ChartRegistry
   ```

2. ✅ **Verifica que el import funcionó:**
   ```python
   print(ChartRegistry)  # Debe mostrar: <class 'BESTLIB.charts.registry.ChartRegistry'>
   ```

3. ✅ **Si falla, verifica la estructura del proyecto:**
   ```python
   import sys
   import os
   from pathlib import Path
   
   # Agregar ruta si es necesario
   project_root = Path(__file__).parent.parent  # Ajustar según tu estructura
   if str(project_root) not in sys.path:
       sys.path.insert(0, str(project_root))
   
   from BESTLIB import ChartRegistry
   ```

4. ✅ **Reinicia el kernel** si el problema persiste

## 🚀 Ejemplo Completo Listo para Ejecutar

```python
# ============================================
# PASO 1: Importar (EJECUTAR PRIMERO)
# ============================================
from BESTLIB import ChartRegistry, MatrixLayout
import pandas as pd
import numpy as np

# Verificar
assert ChartRegistry is not None, "ChartRegistry no se importó"
print("✅ Todo listo para usar ChartRegistry")

# ============================================
# PASO 2: Crear datos
# ============================================
np.random.seed(42)
df = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100),
    'cat': np.random.choice(['A', 'B', 'C'], 100)
})

# ============================================
# PASO 3: Usar ChartRegistry
# ============================================
scatter = ChartRegistry.get('scatter')
spec = scatter.get_spec(
    data=df,
    x_col='x',
    y_col='y',
    category_col='cat',
    interactive=True
)

MatrixLayout.map({'S': spec})
layout = MatrixLayout("S")
layout.display()
```

## 💡 Notas Importantes

1. **Orden de ejecución**: Siempre ejecuta la celda de importación ANTES de usar `ChartRegistry`
2. **Kernel**: Si cambias la estructura del proyecto, reinicia el kernel
3. **Path**: Asegúrate de que BESTLIB esté en `sys.path`
4. **Verificación**: Usa `ChartRegistry.list_types()` para ver qué gráficos están disponibles

