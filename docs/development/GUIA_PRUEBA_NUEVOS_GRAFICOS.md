# 🔍 Guía de Prueba y Diagnóstico: Nuevos Gráficos

## ❌ Problema: `[object Object]` en lugar del gráfico

Si ves `[object Object]`, significa que:
- ✅ El JavaScript se está ejecutando
- ❌ El gráfico no se está renderizando correctamente

---

## 📋 Paso 1: Verificar que el Spec se Genera Correctamente

Ejecuta esto en una celda de Jupyter/Colab:

```python
import pandas as pd
import numpy as np
from BESTLIB.matrix import MatrixLayout

# Crear datos de prueba
df = pd.DataFrame({
    'sepal_length': [5.1, 4.9, 4.7, 4.6, 5.0],
    'sepal_width': [3.5, 3.0, 3.2, 3.1, 3.6],
    'petal_length': [1.4, 1.4, 1.3, 1.5, 1.4],
    'petal_width': [0.2, 0.2, 0.2, 0.2, 0.2]
})

# Crear layout y generar spec
layout = MatrixLayout("L")
spec = layout.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,
    markers=True
)

# Verificar el spec
print("✅ Tipo:", spec.get('type'))
print("✅ Tiene 'series':", 'series' in spec)
if 'series' in spec:
    series = spec['series']
    print(f"✅ Número de series: {len(series)}")
    for key, data in series.items():
        print(f"   - Serie '{key}': {len(data)} puntos")
        if data:
            print(f"     Primer punto: x={data[0].get('x')}, y={data[0].get('y')}")
print("✅ Keys en spec:", list(spec.keys())[:15])
```

**Resultado esperado:**
```
✅ Tipo: line_plot
✅ Tiene 'series': True
✅ Número de series: 1
   - Serie 'default': 5 puntos
     Primer punto: x=5.1, y=3.5
✅ Keys en spec: ['type', 'series', 'encoding', 'options', ...]
```

**Si falla aquí:** El problema está en la generación del spec. Revisa los errores.

---

## 📋 Paso 2: Verificar que el Layout se Crea Correctamente

```python
layout = MatrixLayout("L")
layout.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,
    markers=True
)

# Verificar que el spec está en el mapping
print("✅ Spec en _map:", 'L' in layout._map)
if 'L' in layout._map:
    spec = layout._map['L']
    print("✅ Tipo del spec:", spec.get('type'))
    print("✅ Tiene series:", 'series' in spec)
```

**Resultado esperado:**
```
✅ Spec en _map: True
✅ Tipo del spec: line_plot
✅ Tiene series: True
```

---

## 📋 Paso 3: Abrir Consola del Navegador

**En Jupyter/Colab:**
1. Presiona `F12` o `Ctrl+Shift+I` (Windows/Linux) o `Cmd+Option+I` (Mac)
2. Ve a la pestaña **Console**
3. Ejecuta `layout.display()` de nuevo
4. Busca errores en rojo

**Errores comunes:**
- `renderLinePlotD3 is not defined` → `matrix.js` no se cargó
- `d3 is not defined` → D3.js no se cargó
- `Cannot read property 'series' of undefined` → El spec no tiene 'series'
- `series is not defined` → El spec no tiene el formato correcto

---

## 📋 Paso 4: Prueba Completa con Debug

```python
import pandas as pd
from BESTLIB.matrix import MatrixLayout

# Activar debug
MatrixLayout.set_debug(True)

# Crear datos
df = pd.read_csv("/mnt/data/iris.csv")  # O tu dataset

# Crear layout
layout = MatrixLayout("L")

# Agregar gráfico
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

**Con debug activado, verás:**
- Mensajes de carga de assets
- Errores de comunicación
- Información sobre el spec generado

---

## 📋 Paso 5: Verificar el HTML/JS Generado

```python
layout = MatrixLayout("L")
layout.map_line_plot("L", df, x_col="sepal_length", y_col="sepal_width")

# Obtener el HTML generado (sin ejecutar)
data = layout._prepare_repr_data()
print("HTML generado:")
print(data['html_content'][:500])  # Primeros 500 caracteres
print("\nJS generado:")
print(data['js_code'][:500])  # Primeros 500 caracteres
```

**Verifica que:**
- El HTML tiene el `<div id="...">`
- El JS incluye `matrix.js`
- El mapping incluye el spec con `type: 'line_plot'`

---

## 📋 Paso 6: Prueba con Gráfico Legacy (Comparación)

```python
# Este DEBE funcionar (gráfico legacy)
layout2 = MatrixLayout("B")
species_counts = df['species'].value_counts().reset_index()
species_counts.columns = ['species', 'count']
layout2.map_barchart(
    'B',
    species_counts,
    category_col='species',
    value_col='count'
)
layout2.display()
```

**Si este funciona pero el nuevo no:**
- El problema está en el formato del spec del nuevo gráfico
- O en la función de renderizado `renderLinePlotD3`

---

## 📋 Paso 7: Verificar el Spec en el Mapping

```python
layout = MatrixLayout("L")
layout.map_line_plot("L", df, x_col="sepal_length", y_col="sepal_width")

# Inspeccionar el spec directamente
import json
spec = layout._map.get('L', {})
print("Spec completo:")
print(json.dumps(spec, indent=2, default=str)[:1000])  # Primeros 1000 caracteres
```

**Verifica que:**
- `type` es `'line_plot'`
- `series` existe y tiene datos
- Cada serie tiene puntos con `x` e `y`

---

## 🔧 Soluciones Comunes

### Problema 1: `[object Object]` aparece

**Causa:** El spec no tiene el formato correcto o `renderLinePlotD3` no se está ejecutando.

**Solución:**
1. Abre la consola del navegador (F12)
2. Busca errores JavaScript
3. Verifica que `renderLinePlotD3` existe: `typeof renderLinePlotD3`
4. Verifica que el spec tiene `type: 'line_plot'` y `series`

### Problema 2: Gráfico en blanco

**Causa:** D3.js no se cargó o `ensureD3()` falló.

**Solución:**
1. Verifica en consola: `typeof d3`
2. Si es `undefined`, D3.js no se cargó
3. En Colab, asegúrate de que `AssetManager.ensure_colab_assets_loaded()` se ejecutó

### Problema 3: Error "No hay series para mostrar"

**Causa:** El spec no tiene `series` o está vacío.

**Solución:**
1. Verifica que `prepare_line_data()` devuelve `{'series': {...}}`
2. Verifica que el spec incluye `series` directamente (no dentro de `data`)

---

## ✅ Código de Prueba Completo

```python
import pandas as pd
from BESTLIB.matrix import MatrixLayout

# Activar debug
MatrixLayout.set_debug(True)

# Crear datos
df = pd.read_csv("/mnt/data/iris.csv")  # O tu dataset

# ==========================================
# TEST 1: Line Plot (Nuevo)
# ==========================================
print("=" * 60)
print("TEST 1: Line Plot")
print("=" * 60)

layout1 = MatrixLayout("L")
spec1 = layout1.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,
    markers=True
)

print("✅ Spec generado")
print(f"   Tipo: {spec1.get('type')}")
print(f"   Tiene series: {'series' in spec1}")
if 'series' in spec1:
    print(f"   Series: {list(spec1['series'].keys())}")

layout1.display()

# ==========================================
# TEST 2: Horizontal Bar (Nuevo)
# ==========================================
print("\n" + "=" * 60)
print("TEST 2: Horizontal Bar")
print("=" * 60)

layout2 = MatrixLayout("B")
species_counts = df['species'].value_counts().reset_index()
species_counts.columns = ['species', 'count']
spec2 = layout2.map_horizontal_bar(
    "B",
    species_counts,
    category_col="species",
    value_col="count"
)

print("✅ Spec generado")
print(f"   Tipo: {spec2.get('type')}")
print(f"   Tiene data: {'data' in spec2}")
if 'data' in spec2:
    print(f"   Datos: {len(spec2['data'])} barras")

layout2.display()

# ==========================================
# TEST 3: Bar Chart Legacy (Comparación)
# ==========================================
print("\n" + "=" * 60)
print("TEST 3: Bar Chart Legacy (debe funcionar)")
print("=" * 60)

layout3 = MatrixLayout("C")
spec3 = layout3.map_barchart(
    "C",
    species_counts,
    category_col="species",
    value_col="count"
)

print("✅ Spec generado")
print(f"   Tipo: {spec3.get('type')}")

layout3.display()
```

---

## 🐛 Si Nada Funciona

1. **Reinicia el kernel** (Kernel → Restart)
2. **Reimporta BESTLIB:**
   ```python
   import importlib
   import BESTLIB
   importlib.reload(BESTLIB)
   from BESTLIB.matrix import MatrixLayout
   ```
3. **Verifica la versión de BESTLIB:**
   ```python
   import BESTLIB
   print(BESTLIB.__version__)
   ```
4. **Reinstala BESTLIB:**
   ```bash
   pip install -e . --force-reinstall
   ```

---

**Si sigues viendo `[object Object]`, comparte:**
1. Los errores de la consola del navegador
2. El output del código de diagnóstico
3. La versión de BESTLIB que estás usando

