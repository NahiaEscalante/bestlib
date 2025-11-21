# Diagnóstico y Solución: Dashboard Interactivo BESTLIB

## Problema Reportado

El dashboard interactivo que funcionaba perfectamente ahora no muestra nada o se rompe al ejecutar `layout_completo.display()`.

## Diagnóstico

### ✅ Verificaciones Realizadas

1. **Imports funcionan correctamente**:
   - `from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel` ✅
   - `from BESTLIB.matrix import MatrixLayout` ✅
   - `from BESTLIB.charts import ChartRegistry` ✅

2. **Métodos disponibles**:
   - `add_scatter` ✅
   - `add_histogram` ✅
   - `add_barchart` ✅
   - `add_violin` ✅
   - `add_star_coordinates` ✅
   - `add_parallel_coordinates` ✅
   - `add_radviz` ✅
   - `set_data` ✅
   - `display` ✅

3. **MatrixLayout tiene todos los métodos**:
   - `map_scatter` ✅
   - `map_histogram` ✅
   - `map_barchart` ✅
   - `map_violin` ✅
   - `map_star_coordinates` ✅
   - `map_parallel_coordinates` ✅
   - `map_radviz` ✅

## Posibles Causas

### 1. Caché de Python/Jupyter

**Síntoma**: Los cambios no se reflejan, errores inconsistentes.

**Solución**:
```python
# En Jupyter/Colab, reinicia el kernel:
# Kernel → Restart Kernel

# O fuerza reimport:
import importlib
import BESTLIB
import BESTLIB.reactive
import BESTLIB.layouts.reactive
import BESTLIB.matrix
import BESTLIB.charts

importlib.reload(BESTLIB)
importlib.reload(BESTLIB.reactive)
importlib.reload(BESTLIB.layouts.reactive)
importlib.reload(BESTLIB.matrix)
importlib.reload(BESTLIB.charts)

# Luego reimporta:
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
from BESTLIB.matrix import MatrixLayout
from BESTLIB.charts import ChartRegistry
```

### 2. Versión Incorrecta de ReactiveMatrixLayout

**Síntoma**: Métodos faltantes o comportamiento diferente.

**Solución**:
```python
# Verificar qué versión se está usando:
from BESTLIB.reactive import ReactiveMatrixLayout
print(f"Versión: {ReactiveMatrixLayout.__module__}")
# Debe ser: BESTLIB.layouts.reactive

# Si no, fuerza import directo:
from BESTLIB.layouts.reactive import ReactiveMatrixLayout
from BESTLIB.reactive.selection import SelectionModel
```

### 3. Problema con display() en Jupyter/Colab

**Síntoma**: `display()` no muestra nada.

**Solución**:
```python
# En lugar de layout.display(), usa:
from IPython.display import display, HTML
display(layout._layout)  # O directamente el layout

# O verifica que el HTML se genera:
html = layout._layout._repr_html_()
print(f"HTML generado: {len(html)} caracteres")
```

### 4. Datos no configurados correctamente

**Síntoma**: Gráficos vacíos o errores de datos.

**Solución**:
```python
# Asegúrate de llamar set_data() ANTES de agregar gráficos:
layout = ReactiveMatrixLayout("AS\nHX", selection_model=SelectionModel())
layout.set_data(df)  # ← IMPORTANTE: Antes de add_*

# Luego agrega gráficos:
layout.add_scatter('A', x_col='x', y_col='y', interactive=True)
layout.add_histogram('H', column='x', linked_to='A')
```

## Script de Diagnóstico Completo

Ejecuta este script para identificar el problema:

```python
#!/usr/bin/env python3
"""
Script de diagnóstico para dashboard BESTLIB
"""
import sys

print("=" * 60)
print("🔍 DIAGNÓSTICO DE DASHBOARD BESTLIB")
print("=" * 60)

# Test 1: Imports
print("\n1️⃣ Test de Imports:")
try:
    from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
    from BESTLIB.matrix import MatrixLayout
    from BESTLIB.charts import ChartRegistry
    print("   ✅ Todos los imports exitosos")
    print(f"   - ReactiveMatrixLayout: {ReactiveMatrixLayout.__module__}")
    print(f"   - MatrixLayout: {MatrixLayout.__module__}")
    print(f"   - ChartRegistry: {ChartRegistry.__module__}")
except Exception as e:
    print(f"   ❌ Error en imports: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Crear layout básico
print("\n2️⃣ Test de Creación de Layout:")
try:
    selection = SelectionModel()
    layout = ReactiveMatrixLayout("AS\nHX", selection_model=selection)
    print("   ✅ Layout creado")
    print(f"   - Tipo: {type(layout)}")
    print(f"   - Tiene _layout: {hasattr(layout, '_layout')}")
    print(f"   - Tiene _data: {hasattr(layout, '_data')}")
except Exception as e:
    print(f"   ❌ Error creando layout: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Configurar datos
print("\n3️⃣ Test de Configuración de Datos:")
try:
    import pandas as pd
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10],
        'cat': ['A', 'B', 'A', 'B', 'A']
    })
    layout.set_data(df)
    print("   ✅ Datos configurados")
    print(f"   - Shape: {df.shape}")
except Exception as e:
    print(f"   ❌ Error configurando datos: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Agregar gráficos
print("\n4️⃣ Test de Agregar Gráficos:")
charts_to_test = [
    ('A', 'scatter', {'x_col': 'x', 'y_col': 'y', 'category_col': 'cat', 'interactive': True}),
    ('H', 'histogram', {'column': 'x', 'linked_to': 'A'}),
    ('B', 'barchart', {'category_col': 'cat', 'linked_to': 'A'}),
]

for letter, chart_type, kwargs in charts_to_test:
    try:
        if chart_type == 'scatter':
            layout.add_scatter(letter, **kwargs)
        elif chart_type == 'histogram':
            layout.add_histogram(letter, **kwargs)
        elif chart_type == 'barchart':
            layout.add_barchart(letter, **kwargs)
        print(f"   ✅ {chart_type} '{letter}' agregado")
    except Exception as e:
        print(f"   ❌ Error agregando {chart_type} '{letter}': {e}")
        import traceback
        traceback.print_exc()

# Test 5: Verificar _layout._map
print("\n5️⃣ Test de Verificación de _layout._map:")
try:
    if hasattr(layout._layout, '_map'):
        keys = list(layout._layout._map.keys())
        print(f"   ✅ _map tiene {len(keys)} gráficos: {keys}")
        for key in keys:
            spec = layout._layout._map[key]
            print(f"      - '{key}': type={spec.get('type', 'N/A')}")
    else:
        print("   ❌ _layout no tiene _map")
except Exception as e:
    print(f"   ❌ Error verificando _map: {e}")

# Test 6: Test de display (sin ejecutar realmente)
print("\n6️⃣ Test de Método display():")
try:
    has_display = hasattr(layout, 'display')
    print(f"   ✅ Método display disponible: {has_display}")
    if has_display:
        import inspect
        sig = inspect.signature(layout.display)
        print(f"   - Firma: {sig}")
        
        # Verificar que _layout tiene display
        has_layout_display = hasattr(layout._layout, 'display')
        print(f"   - _layout.display disponible: {has_layout_display}")
        
        # Verificar _repr_html_
        has_repr_html = hasattr(layout._layout, '_repr_html_')
        print(f"   - _layout._repr_html_ disponible: {has_repr_html}")
        
        if has_repr_html:
            try:
                html = layout._layout._repr_html_()
                print(f"   - HTML generado: {len(html)} caracteres")
                if len(html) < 100:
                    print("   ⚠️ HTML muy corto, puede haber un problema")
            except Exception as e:
                print(f"   ❌ Error generando HTML: {e}")
except Exception as e:
    print(f"   ❌ Error verificando display: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ DIAGNÓSTICO COMPLETO")
print("=" * 60)
print("\nSi todos los tests pasan pero display() no funciona:")
print("1. Reinicia el kernel de Jupyter/Colab")
print("2. Verifica que estás en un entorno Jupyter (no script Python)")
print("3. Intenta usar: from IPython.display import display; display(layout._layout)")
print("4. Verifica la consola del navegador para errores JavaScript")
```

## Solución Recomendada

### Paso 1: Reiniciar Kernel

En Jupyter/Colab:
```
Kernel → Restart Kernel
```

### Paso 2: Reimportar Limpio

```python
# Limpiar imports anteriores
import sys
modules_to_remove = [k for k in sys.modules.keys() if k.startswith('BESTLIB')]
for mod in modules_to_remove:
    del sys.modules[mod]

# Reimportar
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
from BESTLIB.matrix import MatrixLayout
from BESTLIB.charts import ChartRegistry
```

### Paso 3: Crear Dashboard Paso a Paso

```python
import pandas as pd

# 1. Crear datos
df = pd.DataFrame({
    'x': [1, 2, 3, 4, 5],
    'y': [2, 4, 6, 8, 10],
    'cat': ['A', 'B', 'A', 'B', 'A']
})

# 2. Crear layout
selection = SelectionModel()
layout = ReactiveMatrixLayout("AS\nHX", selection_model=selection)

# 3. Configurar datos PRIMERO
layout.set_data(df)

# 4. Agregar gráficos
layout.add_scatter('A', x_col='x', y_col='y', category_col='cat', interactive=True)
layout.add_histogram('H', column='x', linked_to='A')
layout.add_barchart('B', category_col='cat', linked_to='A')

# 5. Mostrar (UNA VEZ)
layout.display()
```

## Si Nada Funciona

1. **Verifica la versión de BESTLIB**:
   ```python
   import BESTLIB
   print(BESTLIB.__version__)
   ```

2. **Reinstala BESTLIB**:
   ```bash
   pip uninstall -y BESTLIB
   pip install -e .
   ```

3. **Verifica el entorno**:
   ```python
   import sys
   print(f"Python: {sys.version}")
   print(f"Jupyter: {'IPython' in sys.modules}")
   ```

4. **Reporta el error completo** con:
   - Mensaje de error exacto
   - Stack trace completo
   - Versión de Python
   - Entorno (Jupyter/Colab/VSCode)

