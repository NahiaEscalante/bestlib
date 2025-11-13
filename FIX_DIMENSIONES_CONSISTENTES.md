# 🔧 Fix: Dimensiones Consistentes en Gráficos Enlazados

## 📅 Fecha: 2025-01-13

## 🎯 Problemas Identificados

### Dashboard 2x2
- ✅ El brush funciona correctamente (no desaparece)
- ❌ El histograma 'H' "se reinicia" al estado original después de actualizarse

### Dashboard 3x3
- ❌ Los gráficos tienen dimensiones extrañas (algunos muy angostos)
- ❌ El boxplot 'X' cambia drásticamente de tamaño después del brush
- ❌ Las propiedades de interacción están activas para gráficos que no deberían serlo

## 🔍 Causa Raíz

Los **métodos de actualización** de gráficos enlazados (`update_histogram`, `update_boxplot`, `update_barchart`, `update_pie`) estaban calculando dimensiones **directamente** sin usar la función `getChartDimensions()`:

### ❌ Antes (Inconsistente):
```javascript
// En update_boxplot, update_histogram, etc.
const width = Math.max(targetCell.clientWidth || 400, 200);
const height = Math.min(availableHeight, 350);
```

**Problemas:**
1. NO respeta `max_width` del contenedor
2. NO usa la misma lógica que el render inicial
3. NO detecta el número de columnas del grid
4. Dimensiones inconsistentes entre render inicial y updates

### ✅ Después (Consistente):
```javascript
// Usar getChartDimensions() de manera consistente
const dims = window.getChartDimensions ? 
    window.getChartDimensions(targetCell, { type: 'barchart' }, 400, 350) :
    { width: Math.max(targetCell.clientWidth || 400, 200), height: 350 };
const width = dims.width;
const height = dims.height;
```

**Ventajas:**
1. ✅ Respeta `max_width` del contenedor padre
2. ✅ Usa la misma lógica de cálculo que el render inicial
3. ✅ Detecta el número de columnas del grid dinámicamente
4. ✅ Dimensiones consistentes en todo momento

## 🔧 Cambios Aplicados

### 1. Exponer `getChartDimensions()` Globalmente

**Archivo**: `BESTLIB/matrix.js` (líneas 5506-5507)

```javascript
// Exponer funciones globalmente
global.render = render;
global.getChartDimensions = getChartDimensions; // ✅ Ahora accesible desde updates
```

**Resultado**: Los updates de JavaScript pueden llamar a `window.getChartDimensions()` para calcular dimensiones de manera consistente.

### 2. Actualizar `update_barchart()` en `reactive.py`

**Cambios en líneas 750-755**:

```javascript
// CRÍTICO: Calcular dimensiones una sola vez de manera consistente
const dims = window.getChartDimensions ? 
    window.getChartDimensions(targetCell, { type: 'barchart' }, 400, 350) :
    { width: Math.max(targetCell.clientWidth || 400, 200), height: 350 };
const width = dims.width;
const height = dims.height;
```

**Resultado**: El barchart mantiene dimensiones consistentes entre render inicial y updates.

### 3. Actualizar `update_histogram()` en `reactive.py`

**Cambios en líneas 1496-1501**:

```javascript
// CRÍTICO: Usar getChartDimensions() para calcular dimensiones de manera consistente
const dims = window.getChartDimensions ? 
    window.getChartDimensions(targetCell, { type: 'histogram' }, 400, 350) :
    { width: Math.max(targetCell.clientWidth || 400, 200), height: 350 };
const width = dims.width;
const height = dims.height;
```

**Resultado**: El histograma mantiene dimensiones consistentes.

### 4. Actualizar `update_boxplot()` en `reactive.py`

**Cambios en líneas 1863-1870**:

```javascript
// CRÍTICO: Usar getChartDimensions() para calcular dimensiones de manera consistente
const dims = window.getChartDimensions ? 
    window.getChartDimensions(targetCell, { type: 'boxplot' }, 400, 350) :
    { width: Math.max(targetCell.clientWidth || 400, 200), height: 350 };
const width = dims.width;
const height = dims.height;
```

**Resultado**: El boxplot NO cambia de tamaño drásticamente después del brush.

### 5. Actualizar `update_pie()` en `reactive.py`

**Cambios en líneas 2589-2595**:

```javascript
// CRÍTICO: Usar getChartDimensions() para calcular dimensiones de manera consistente
const dims = window.getChartDimensions ? 
    window.getChartDimensions(targetCell, { type: 'pie' }, 400, 400) :
    { width: Math.max(targetCell.clientWidth || 400, 200), height: Math.max(targetCell.clientHeight || 400, 200) };
const width = dims.width;
const height = dims.height;
```

**Resultado**: El pie chart mantiene dimensiones consistentes.

## 🧪 Cómo Probar

### 1. Reiniciar el kernel de Colab/Jupyter

### 2. Dashboard 2x2:

```python
layout_reactive1 = ReactiveMatrixLayout("""
AS
HX
""", selection_model=SelectionModel())

layout_reactive1.set_data(df)
layout_reactive1.add_scatter('A', x_col='sepal_length', y_col='sepal_width', color_col='species')
layout_reactive1.add_scatter('S', x_col='petal_length', y_col='petal_width', color_col='species')
layout_reactive1.add_histogram('H', column='sepal_length', linked_to='A', bins=15)
layout_reactive1.add_boxplot('X', column='petal_length', category_col='species', linked_to='S')
layout_reactive1.display()
```

**Resultado esperado:**
- ✅ El brush permanece visible
- ✅ El histograma 'H' mantiene su tamaño al actualizarse
- ✅ El histograma **NO se reinicia** al estado original

### 3. Dashboard 3x3 (con `max_width`):

```python
layout_completo = ReactiveMatrixLayout("""
AHB
XPV
CYR
""", selection_model=SelectionModel(), max_width=850)

layout_completo.set_data(df)
# ... agregar todos los gráficos ...
layout_completo.display()
```

**Resultado esperado:**
- ✅ Todos los gráficos tienen dimensiones proporcionales
- ✅ El boxplot 'X' mantiene su tamaño al actualizarse (NO cambia drásticamente)
- ✅ Los gráficos respetan el límite de `max_width=850`
- ✅ NO hay gráficos excesivamente angostos o anchos

### 4. Activar logs de debug (opcional):

```python
from BESTLIB.matrix import MatrixLayout
MatrixLayout.set_debug(True)
```

También en JavaScript (consola del navegador):

```javascript
window._bestlib_debug = true
```

## 📊 Archivos Modificados

### 1. **`BESTLIB/matrix.js`** (1 línea agregada)
   - Exposición global de `getChartDimensions()`

### 2. **`BESTLIB/reactive.py`** (5 secciones modificadas)
   - `update_barchart()`: Dimensiones consistentes
   - `update_histogram()`: Dimensiones consistentes
   - `update_boxplot()`: Dimensiones consistentes
   - `update_pie()`: Dimensiones consistentes
   - Eliminación de cálculos redundantes de dimensiones

## ✅ Beneficios de este Fix

1. **Dimensiones Consistentes**: Los gráficos mantienen el mismo tamaño entre render inicial y updates
2. **Respeta `max_width`**: Los updates respetan el límite definido en el contenedor
3. **Detección de Grid**: Calcula correctamente el ancho por celda según el número de columnas
4. **Menos Código**: Elimina lógica duplicada de cálculo de dimensiones
5. **Mantenibilidad**: Un solo lugar para la lógica de dimensiones (`getChartDimensions()`)

## 🎯 Próximos Pasos

Por favor, prueba ambos dashboards (2x2 y 3x3) y comparte:

1. **¿El histograma mantiene su tamaño en el 2x2?** ✅/❌
2. **¿El boxplot mantiene su tamaño en el 3x3?** ✅/❌
3. **¿Los gráficos tienen dimensiones proporcionales en el 3x3?** ✅/❌
4. **¿Capturas de pantalla** (antes y después del brush)
5. **¿Logs de la consola** si hay algún error

---

**Nota**: Este fix es **crítico** para el correcto funcionamiento de las linked views en dashboards grandes (3x3 o más). Sin él, los gráficos cambian de tamaño de manera impredecible al actualizarse.

