# 🔍 ANÁLISIS EXHAUSTIVO DE FALENCIAS - BESTLIB 2025 (COMPLETO)

**Fecha:** 2025-01-27  
**Análisis:** Identificación sistemática de TODOS los problemas en el proyecto

---

## 📊 RESUMEN EJECUTIVO

- **🔴 CRÍTICAS:** 8 problemas
- **🟡 MEDIAS:** 15 problemas  
- **🟢 MENORES:** 12 problemas
- **TOTAL:** 35 problemas identificados

---

## 🔴 PROBLEMAS CRÍTICOS

### 🔴 FALENCIA #1: matrix.py usa `pd` directamente sin obtenerlo de `get_pandas()`

**Archivo:** `BESTLIB/matrix.py`  
**Línea:** 111  
**Severidad:** CRÍTICA

**Problema:**
```python
if has_pandas() and isinstance(data, get_pandas().DataFrame):
    df_work = pd.DataFrame(index=data.index)  # ⚠️ pd no está definido
```

**Impacto:**
- `NameError` si pandas no está importado directamente
- Inconsistente con el resto del código que usa `get_pandas()`

**Solución:**
```python
if has_pandas():
    pd = get_pandas()
    if isinstance(data, pd.DataFrame):
        df_work = pd.DataFrame(index=data.index)
```

---

### 🔴 FALENCIA #2: matrix.py usa `pd.` en múltiples lugares sin validar

**Archivo:** `BESTLIB/matrix.py`  
**Líneas:** 586, 683, 806, 1213, 1222, 1984, 1988  
**Severidad:** CRÍTICA

**Problema:**
Uso directo de `pd.DataFrame()`, `pd.notna()` sin obtener `pd` de `get_pandas()` primero.

**Solución:**
Obtener `pd = get_pandas()` antes de cada uso o validar que no sea `None`.

---

### 🔴 FALENCIA #3: reactive/selection.py usa HAS_PANDAS directamente

**Archivo:** `BESTLIB/reactive/selection.py`  
**Líneas:** 14-16, 32, 38, 211, 224, 258  
**Severidad:** CRÍTICA

**Problema:**
```python
HAS_PANDAS = False
pd = None
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None
```

Define `HAS_PANDAS` localmente en lugar de usar `has_pandas()` de `utils.imports`.

**Solución:**
```python
from ..utils.imports import has_pandas, get_pandas
# Eliminar definición local de HAS_PANDAS
# Usar has_pandas() y get_pandas() donde sea necesario
```

---

### 🔴 FALENCIA #4: charts/scatter.py usa HAS_PANDAS directamente

**Archivo:** `BESTLIB/charts/scatter.py`  
**Líneas:** 12-33, 91, 118  
**Severidad:** CRÍTICA

**Problema:**
Similar a #3, define `HAS_PANDAS` localmente con lógica compleja de limpieza de `sys.modules`.

**Solución:**
Reemplazar con `has_pandas()` y `get_pandas()` de `utils.imports`.

---

### 🔴 FALENCIA #5: data/preparators.py usa HAS_PANDAS directamente

**Archivo:** `BESTLIB/data/preparators.py`  
**Líneas:** 5-27, múltiples usos  
**Severidad:** CRÍTICA

**Problema:**
Define `HAS_PANDAS` localmente y lo usa en 13 lugares diferentes.

**Solución:**
Reemplazar con `has_pandas()` y `get_pandas()` de `utils.imports`.

---

### 🔴 FALENCIA #6: utils/figsize.py no valida tipos de parámetros

**Archivo:** `BESTLIB/utils/figsize.py`  
**Línea:** 6-27  
**Severidad:** CRÍTICA

**Problema:**
```python
def figsize_to_pixels(figsize):
    if figsize is None:
        return None
    if isinstance(figsize, (tuple, list)) and len(figsize) == 2:
        width, height = figsize  # ⚠️ Puede fallar si width/height no son numéricos
```

No valida que `width` y `height` sean numéricos antes de operar.

**Solución:**
```python
def figsize_to_pixels(figsize: Optional[Tuple[float, float]]) -> Optional[Tuple[int, int]]:
    if figsize is None:
        return None
    if not isinstance(figsize, (tuple, list)) or len(figsize) != 2:
        raise TypeError(f"figsize must be tuple/list of 2 numbers, received: {type(figsize).__name__}")
    width, height = figsize
    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
        raise TypeError(f"figsize values must be numeric, received: width={type(width).__name__}, height={type(height).__name__}")
    # ... resto del código
```

---

### 🔴 FALENCIA #7: utils/figsize.py no valida kwargs en process_figsize_in_kwargs()

**Archivo:** `BESTLIB/utils/figsize.py`  
**Línea:** 30-42  
**Severidad:** CRÍTICA

**Problema:**
```python
def process_figsize_in_kwargs(kwargs):
    if 'figsize' in kwargs:
        figsize_px = figsize_to_pixels(kwargs['figsize'])
```

No valida que `kwargs` sea un diccionario.

**Solución:**
```python
def process_figsize_in_kwargs(kwargs: Dict[str, Any]) -> None:
    if not isinstance(kwargs, dict):
        raise TypeError(f"kwargs must be dict, received: {type(kwargs).__name__}")
    # ... resto del código
```

---

### 🔴 FALENCIA #8: charts/bar.py no valida parámetros en métodos

**Archivo:** `BESTLIB/charts/bar.py`  
**Líneas:** 18, 28, 32  
**Severidad:** CRÍTICA

**Problema:**
```python
def validate_data(self, data, category_col=None, **kwargs):
    if not category_col:  # ⚠️ No valida que category_col sea str
        raise ChartError("category_col es requerido para bar chart")
```

No valida tipos de parámetros antes de usar.

**Solución:**
```python
def validate_data(self, data: Any, category_col: Optional[str] = None, **kwargs) -> None:
    if not isinstance(category_col, str) or not category_col:
        raise ChartError("category_col must be non-empty str")
    # ... resto del código
```

---

## 🟡 PROBLEMAS MEDIOS

### 🟡 FALENCIA #9: charts/bar.py falta type hints

**Archivo:** `BESTLIB/charts/bar.py`  
**Severidad:** MEDIA

**Problema:**
Todos los métodos carecen de type hints completos.

**Solución:**
Agregar type hints a `validate_data()`, `prepare_data()`, `get_spec()`.

---

### 🟡 FALENCIA #10: data/preparators.py falta type hints

**Archivo:** `BESTLIB/data/preparators.py`  
**Severidad:** MEDIA

**Problema:**
Todas las funciones `prepare_*_data()` carecen de type hints.

**Solución:**
Agregar type hints a todas las funciones públicas.

---

### 🟡 FALENCIA #11: data/preparators.py no valida parámetros en prepare_scatter_data()

**Archivo:** `BESTLIB/data/preparators.py`  
**Línea:** 33  
**Severidad:** MEDIA

**Problema:**
```python
def prepare_scatter_data(data, x_col=None, y_col=None, ...):
    # No valida que data no sea None
    # No valida tipos de x_col, y_col, etc.
```

**Solución:**
Agregar validación de `data is None` y tipos de columnas.

---

### 🟡 FALENCIA #12: data/preparators.py no valida parámetros en prepare_bar_data()

**Archivo:** `BESTLIB/data/preparators.py`  
**Línea:** 103  
**Severidad:** MEDIA

**Problema:**
Similar a #11, falta validación de parámetros.

---

### 🟡 FALENCIA #13: data/preparators.py no valida parámetros en prepare_histogram_data()

**Archivo:** `BESTLIB/data/preparators.py`  
**Línea:** 163  
**Severidad:** MEDIA

**Problema:**
```python
def prepare_histogram_data(data, value_col=None, bins=10):
    # No valida que bins sea int positivo
```

**Solución:**
```python
if not isinstance(bins, int) or bins <= 0:
    raise ValueError(f"bins must be positive int, received: {bins!r}")
```

---

### 🟡 FALENCIA #14: data/preparators.py no valida parámetros en prepare_boxplot_data()

**Archivo:** `BESTLIB/data/preparators.py`  
**Línea:** 262  
**Severidad:** MEDIA

**Problema:**
Falta validación de tipos de parámetros.

---

### 🟡 FALENCIA #15: data/preparators.py no valida parámetros en prepare_heatmap_data()

**Archivo:** `BESTLIB/data/preparators.py`  
**Línea:** 337  
**Severidad:** MEDIA

**Problema:**
Falta validación de que `x_col`, `y_col`, `value_col` sean strings.

---

### 🟡 FALENCIA #16: data/preparators.py no valida parámetros en prepare_line_data()

**Archivo:** `BESTLIB/data/preparators.py`  
**Línea:** 400  
**Severidad:** MEDIA

**Problema:**
Falta validación de parámetros requeridos.

---

### 🟡 FALENCIA #17: data/preparators.py no valida parámetros en prepare_pie_data()

**Archivo:** `BESTLIB/data/preparators.py`  
**Línea:** 442  
**Severidad:** MEDIA

**Problema:**
Falta validación de `category_col`.

---

### 🟡 FALENCIA #18: data/preparators.py no valida parámetros en prepare_grouped_bar_data()

**Archivo:** `BESTLIB/data/preparators.py`  
**Línea:** 529  
**Severidad:** MEDIA

**Problema:**
Falta validación de `main_col`, `sub_col`.

---

### 🟡 FALENCIA #19: charts/scatter.py falta type hints

**Archivo:** `BESTLIB/charts/scatter.py`  
**Severidad:** MEDIA

**Problema:**
Todos los métodos carecen de type hints completos.

---

### 🟡 FALENCIA #20: charts/scatter.py no valida tipos de parámetros en validate_data()

**Archivo:** `BESTLIB/charts/scatter.py`  
**Línea:** 43  
**Severidad:** MEDIA

**Problema:**
```python
def validate_data(self, data, x_col=None, y_col=None, **kwargs):
    if not x_col or not y_col:  # ⚠️ No valida que sean str
        raise ChartError("x_col e y_col son requeridos")
```

**Solución:**
```python
if not isinstance(x_col, str) or not x_col:
    raise ChartError("x_col must be non-empty str")
if not isinstance(y_col, str) or not y_col:
    raise ChartError("y_col must be non-empty str")
```

---

### 🟡 FALENCIA #21: charts/scatter.py no valida tipos en prepare_data()

**Archivo:** `BESTLIB/charts/scatter.py`  
**Línea:** 64  
**Severidad:** MEDIA

**Problema:**
Falta validación de tipos de parámetros opcionales (`size_col`, `color_col`, etc.).

---

### 🟡 FALENCIA #22: charts/scatter.py no valida maxPoints en get_spec()

**Archivo:** `BESTLIB/charts/scatter.py`  
**Línea:** 116  
**Severidad:** MEDIA

**Problema:**
```python
max_points = kwargs.get('maxPoints', None)
if max_points and isinstance(max_points, int) and max_points > 0:
```

No valida que `maxPoints` sea positivo si se proporciona.

---

### 🟡 FALENCIA #23: reactive/selection.py falta type hints

**Archivo:** `BESTLIB/reactive/selection.py`  
**Severidad:** MEDIA

**Problema:**
`_items_to_dataframe()` y métodos de clase carecen de type hints.

---

## 🟢 PROBLEMAS MENORES

### 🟢 FALENCIA #24: utils/figsize.py falta type hints

**Archivo:** `BESTLIB/utils/figsize.py`  
**Severidad:** MENOR

**Problema:**
Ambas funciones carecen de type hints.

---

### 🟢 FALENCIA #25: utils/figsize.py falta docstring Raises:

**Archivo:** `BESTLIB/utils/figsize.py`  
**Severidad:** MENOR

**Problema:**
Docstrings no documentan excepciones que pueden lanzar.

---

### 🟢 FALENCIA #26: charts/bar.py falta docstring Raises:

**Archivo:** `BESTLIB/charts/bar.py`  
**Severidad:** MENOR

**Problema:**
Docstrings no documentan `ChartError` que se lanza.

---

### 🟢 FALENCIA #27: charts/scatter.py falta docstring Raises:

**Archivo:** `BESTLIB/charts/scatter.py`  
**Severidad:** MENOR

**Problema:**
Docstrings no documentan todas las excepciones posibles.

---

### 🟢 FALENCIA #28: data/preparators.py falta docstring Raises:

**Archivo:** `BESTLIB/data/preparators.py`  
**Severidad:** MENOR

**Problema:**
Funciones no documentan `DataError` que pueden lanzar.

---

### 🟢 FALENCIA #29: reactive/selection.py falta docstring Raises:

**Archivo:** `BESTLIB/reactive/selection.py`  
**Severidad:** MENOR

**Problema:**
`_items_to_dataframe()` no documenta excepciones.

---

### 🟢 FALENCIA #30: matrix.py falta validación en _figsize_to_pixels()

**Archivo:** `BESTLIB/matrix.py`  
**Línea:** 49  
**Severidad:** MENOR

**Problema:**
Similar a utils/figsize.py, falta validación de tipos.

---

### 🟢 FALENCIA #31: matrix.py falta validación en _process_figsize_in_kwargs()

**Archivo:** `BESTLIB/matrix.py`  
**Línea:** 73  
**Severidad:** MENOR

**Problema:**
No valida que `kwargs` sea dict.

---

### 🟢 FALENCIA #32: matrix.py falta type hints en métodos estáticos

**Archivo:** `BESTLIB/matrix.py`  
**Severidad:** MENOR

**Problema:**
`_figsize_to_pixels()` y `_process_figsize_in_kwargs()` carecen de type hints.

---

### 🟢 FALENCIA #33: charts/bar.py falta validación de data is None

**Archivo:** `BESTLIB/charts/bar.py`  
**Línea:** 18  
**Severidad:** MENOR

**Problema:**
`validate_data()` no verifica si `data` es `None`.

---

### 🟢 FALENCIA #34: charts/scatter.py falta validación de data is None

**Archivo:** `BESTLIB/charts/scatter.py`  
**Línea:** 43  
**Severidad:** MENOR

**Problema:**
Similar a #33.

---

### 🟢 FALENCIA #35: Inconsistencia en manejo de pandas entre módulos

**Archivo:** Múltiples  
**Severidad:** MENOR

**Problema:**
Algunos módulos usan `has_pandas()`/`get_pandas()`, otros definen `HAS_PANDAS` localmente.

**Solución:**
Normalizar TODOS los módulos para usar `has_pandas()` y `get_pandas()` de `utils.imports`.

---

## 📋 RESUMEN POR ARCHIVO

### BESTLIB/matrix.py
- **Críticas:** 2 (#1, #2)
- **Menores:** 3 (#30, #31, #32)
- **Total:** 5 problemas

### BESTLIB/reactive/selection.py
- **Críticas:** 1 (#3)
- **Medias:** 1 (#23)
- **Menores:** 1 (#29)
- **Total:** 3 problemas

### BESTLIB/charts/scatter.py
- **Críticas:** 1 (#4)
- **Medias:** 3 (#19, #20, #21, #22)
- **Menores:** 2 (#27, #34)
- **Total:** 6 problemas

### BESTLIB/data/preparators.py
- **Críticas:** 1 (#5)
- **Medias:** 8 (#10, #11, #12, #13, #14, #15, #16, #17, #18)
- **Menores:** 1 (#28)
- **Total:** 10 problemas

### BESTLIB/utils/figsize.py
- **Críticas:** 2 (#6, #7)
- **Menores:** 2 (#24, #25)
- **Total:** 4 problemas

### BESTLIB/charts/bar.py
- **Críticas:** 1 (#8)
- **Medias:** 1 (#9)
- **Menores:** 2 (#26, #33)
- **Total:** 4 problemas

### General
- **Menores:** 1 (#35)
- **Total:** 1 problema

---

## ✅ PRIORIDADES DE CORRECCIÓN

### 🔴 CRÍTICAS (Implementar primero)
1. Normalizar uso de pandas en todos los módulos (#1, #2, #3, #4, #5)
2. Validar tipos en utils/figsize.py (#6, #7)
3. Validar parámetros en charts/bar.py (#8)

### 🟡 MEDIAS (Implementar después)
4. Agregar type hints a todos los métodos (#9, #10, #19, #23)
5. Validar parámetros en data/preparators.py (#11-18)
6. Validar parámetros en charts/scatter.py (#20-22)

### 🟢 MENORES (Mejoras de calidad)
7. Agregar docstrings Raises: (#25-29)
8. Validar tipos en métodos auxiliares (#30-34)
9. Normalizar manejo de pandas (#35)

---

## 📝 NOTAS ADICIONALES

1. **Pandas Handling:** Hay 3 patrones diferentes de manejo de pandas:
   - `has_pandas()`/`get_pandas()` (correcto)
   - `HAS_PANDAS` local (incorrecto)
   - `pd` directo sin validar (incorrecto)

2. **Type Hints:** Aproximadamente 60% de los métodos públicos carecen de type hints completos.

3. **Validación:** Muchos métodos no validan tipos de parámetros antes de usar, lo que puede causar errores confusos.

4. **Documentación:** Falta documentación de excepciones (`Raises:`) en la mayoría de los métodos.

---

**Fin del análisis completo**

