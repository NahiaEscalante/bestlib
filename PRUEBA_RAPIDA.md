# 🚀 Prueba Rápida: Nuevos Gráficos

## 📝 Código para Copiar y Pegar en Jupyter/Colab

### Paso 1: Prueba Básica de Line Plot

```python
import pandas as pd
from BESTLIB.matrix import MatrixLayout

# Crear datos simples
df = pd.DataFrame({
    'sepal_length': [5.1, 4.9, 4.7, 4.6, 5.0],
    'sepal_width': [3.5, 3.0, 3.2, 3.1, 3.6]
})

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

### Paso 2: Si ves `[object Object]`, ejecuta esto para diagnosticar

```python
# Verificar el spec
spec = layout._map.get('L', {})
print("Tipo:", spec.get('type'))
print("Tiene series:", 'series' in spec)
if 'series' in spec:
    series = spec['series']
    print("Series:", list(series.keys()))
    if series:
        first_series = list(series.values())[0]
        print("Puntos en primera serie:", len(first_series))
        if first_series:
            print("Primer punto:", first_series[0])
```

### Paso 3: Abrir Consola del Navegador

1. Presiona **F12** (o **Cmd+Option+I** en Mac)
2. Ve a la pestaña **Console**
3. Busca errores en rojo
4. Ejecuta esto en la consola:
   ```javascript
   // Verificar que D3 está cargado
   console.log('D3 disponible:', typeof d3 !== 'undefined');
   
   // Verificar que renderLinePlotD3 existe
   console.log('renderLinePlotD3 disponible:', typeof renderLinePlotD3 !== 'undefined');
   ```

### Paso 4: Prueba con Gráfico Legacy (debe funcionar)

```python
# Este DEBE funcionar
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

---

## 🔍 Diagnóstico Rápido

Si el gráfico legacy funciona pero el nuevo no:

1. **El problema está en el formato del spec**
2. **O en la función de renderizado JavaScript**

**Solución temporal:** Usa el gráfico legacy `map_line()` en lugar de `map_line_plot()`:

```python
layout = MatrixLayout("L")
layout.map_line(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width"
)
layout.display()
```

---

## ✅ Checklist

- [ ] El spec tiene `type: 'line_plot'`
- [ ] El spec tiene `series` (no `data`)
- [ ] `series` tiene al menos una serie con datos
- [ ] Cada punto tiene `x` e `y` numéricos
- [ ] D3.js está cargado (`typeof d3 !== 'undefined'`)
- [ ] `renderLinePlotD3` existe (`typeof renderLinePlotD3 !== 'undefined'`)
- [ ] No hay errores en la consola del navegador

---

**Si todo el checklist está ✅ pero aún ves `[object Object]`, comparte:**
1. Los errores de la consola
2. El output del diagnóstico del spec
3. La versión de BESTLIB

