# 🔒 Fix: Expansión Infinita de Matriz - Solución CSS + JS

## 📅 Fecha: 2025-01-13

## 🎯 Problema Principal

El dashboard 3x3 presentaba múltiples problemas de expansión:

1. **Scatter Plot 'A'**: Se expandía horizontalmente (solo el eje X) después del brush
2. **Boxplot 'X'**: Los ejes desaparecían/se volvían transparentes, y luego se expandía
3. **Barchart 'B'**: Estaba extremadamente estirado verticalmente desde el inicio
4. **Problema general**: El `max_width=850` no estaba funcionando correctamente

## 🔍 Causa Raíz

El problema tenía dos capas:

### 1. CSS no limitaba el contenedor
El `max_width` se pasaba a JavaScript pero **no se aplicaba como estilo CSS** en el contenedor `matrix-layout`. Esto permitía que el CSS Grid se expandiera sin límite.

### 2. JavaScript leía el ancho expandido
Cuando se actualizaba un gráfico después del brush:
1. El contenedor ya se había expandido
2. `container.clientWidth` devolvía el valor expandido
3. Los gráficos se re-renderizaban con ese ancho mayor
4. Esto causaba más expansión → **ciclo infinito**

## ✅ Solución Implementada

### Cambio 1: Aplicar `max-width` como estilo CSS inline

**Archivo**: `BESTLIB/matrix.py`

```python
# En _prepare_repr_data() - líneas 1731-1734
# Generar estilo inline para el contenedor si hay max_width
inline_style = ""
if self._max_width is not None:
    inline_style = f' style="max-width: {self._max_width}px; margin: 0 auto; box-sizing: border-box;"'
```

**Resultado**: El div del matrix-layout ahora se genera como:
```html
<div id="matrix-xyz" class="matrix-layout" style="max-width: 850px; margin: 0 auto; box-sizing: border-box;"></div>
```

Esto **limita físicamente** el contenedor en el DOM, evitando que el CSS Grid se expanda.

### Cambio 2: JavaScript lee el `max-width` del CSS

**Archivo**: `BESTLIB/matrix.js`

```javascript
// En getChartDimensions() - líneas 723-735
// 🔒 CRÍTICO: Si el contenedor padre tiene max-width en CSS, RESPETARLO SIEMPRE
let cssMaxWidth = null;
if (parentContainer) {
  const computedStyle = window.getComputedStyle(parentContainer);
  const maxWidthStr = computedStyle.maxWidth;
  if (maxWidthStr && maxWidthStr !== 'none') {
    cssMaxWidth = parseInt(maxWidthStr);
    if (isNaN(cssMaxWidth) || !isFinite(cssMaxWidth) || cssMaxWidth <= 0) {
      cssMaxWidth = null;
    }
  }
}
```

**Resultado**: JavaScript ahora lee el `max-width` directamente del CSS computado del navegador, asegurando que siempre respeta el límite definido.

### Cambio 3: Detección dinámica de número de columnas

```javascript
// líneas 773-787
// Calcular número de columnas del grid dinámicamente
let numColumns = 3; // Valor por defecto

// Intentar obtener el número de columnas del grid desde computedStyle
if (parentContainer) {
  const computedStyle = window.getComputedStyle(parentContainer);
  const gridCols = computedStyle.gridTemplateColumns;
  if (gridCols && gridCols !== 'none') {
    // Contar el número de tracks en el grid (separados por espacios)
    const tracks = gridCols.trim().split(/\s+/);
    if (tracks.length > 0) {
      numColumns = tracks.length;
    }
  }
}
```

**Resultado**: Detecta automáticamente si es 2x2, 3x3, o cualquier otra configuración.

### Cambio 4: Cálculo preciso de ancho máximo por celda

```javascript
// líneas 789-796
// Calcular ancho máximo por celda
const gap = 20; // gap por defecto
const cellPadding = 20; // padding estimado por celda
const estimatedMaxCellWidth = (containerMaxWidth / numColumns) - gap - cellPadding;

// 🔒 APLICAR EL LÍMITE ESTRICTAMENTE
width = Math.min(width, estimatedMaxCellWidth);
```

**Fórmula**:
```
ancho_por_celda = (max_width_total / num_columnas) - gap - padding
```

**Ejemplo para 3x3 con max_width=850**:
```
ancho_por_celda = (850 / 3) - 20 - 20 = 243 px
```

### Cambio 5: Logs de depuración mejorados

```javascript
// línea 798
console.log(`[BESTLIB] Límite max_width aplicado: cssMaxWidth=${cssMaxWidth}, containerMaxWidth=${containerMaxWidth}, numColumns=${numColumns}, maxCellWidth=${estimatedMaxCellWidth.toFixed(0)}, containerClientWidth=${container.clientWidth}, finalWidth=${width.toFixed(0)}`);
```

## 🧪 Cómo Probar

### 1. Reiniciar el kernel de Colab

### 2. Dashboard 3x3 con `max_width`

```python
layout_completo = ReactiveMatrixLayout("""
AHB
XPV
CYR
""", selection_model=SelectionModel(), max_width=850)

layout_completo.set_data(df)
# ... agregar gráficos ...
layout_completo.display()
```

### 3. Abrir la consola del navegador (F12 → Console)

### 4. Hacer brush en el scatter plot 'A'

### 5. Revisar los logs en la consola

Deberías ver algo como:
```
[BESTLIB] Límite max_width aplicado: cssMaxWidth=850, containerMaxWidth=850, numColumns=3, maxCellWidth=243, containerClientWidth=300, finalWidth=243
```

## ✅ Comportamiento Esperado

### Antes del Fix
- ❌ Scatter Plot 'A' se expandía horizontalmente
- ❌ Boxplot 'X' perdía ejes y se expandía
- ❌ Barchart 'B' estaba estirado verticalmente
- ❌ La matriz crecía sin límite

### Después del Fix
- ✅ Scatter Plot 'A' mantiene su ancho (máx ~243px en 3x3 con max_width=850)
- ✅ Boxplot 'X' mantiene sus ejes y no se expande
- ✅ Barchart 'B' tiene proporciones correctas
- ✅ La matriz respeta el límite de 850px

## 📊 Archivos Modificados

1. **`BESTLIB/matrix.py`**
   - `_prepare_repr_data()`: Agrega estilo inline con max-width
   - `_repr_html_()`: Usa el estilo inline
   - `_repr_mimebundle_()`: Usa el estilo inline
   - `display()`: Usa el estilo inline

2. **`BESTLIB/matrix.js`**
   - `getChartDimensions()`: Lee max-width del CSS, detecta columnas dinámicamente, aplica límite estricto

## 🔧 Configuración Recomendada

Para dashboards grandes (3x3 o más):

```python
# Ajustar max_width según el tamaño del dashboard
layout = ReactiveMatrixLayout("""
AHB
XPV
CYR
""", max_width=950)  # Aumentar si necesitas gráficos más grandes
```

**Regla general**:
- **2x2**: `max_width=650-750`
- **3x3**: `max_width=850-950`
- **4x4**: `max_width=1100-1200`

## 🎯 Siguiente Paso

Por favor, prueba con tu código y comparte:
1. **Capturas del dashboard 3x3 antes y después del brush**
2. **Los logs de la consola**
3. **Si persiste algún problema de expansión o ejes**

---

**Nota**: Si el barchart 'B' sigue viéndose estirado, podría ser un problema con la proporción `figsize` o con el contenido del gráfico (muchas categorías). Podemos ajustar eso por separado.

