# Análisis Completo del Pipeline de Datos: Python → JavaScript

## Resumen Ejecutivo

Este documento analiza el flujo completo de datos desde que el usuario llama `layout.map_rug()` hasta que el gráfico se renderiza en el navegador.

## Pipeline Completo

### 1. Llamada del Usuario (Python)

```python
layout.map_rug("R", df, column="value")
```

**Ubicación**: `BESTLIB/matrix.py:1869` o `BESTLIB/layouts/matrix.py:310`

**Flujo**:
- `map_rug()` es un `@classmethod` que:
  1. Llama a `ChartRegistry.get('rug')` para obtener la clase `RugChart`
  2. Crea instancia: `chart = RugChart()`
  3. Llama `chart.get_spec(data, column=column, axis=axis, **kwargs)`
  4. Guarda el spec en `MatrixLayout._map[letter] = spec`

### 2. ChartRegistry y Chart.get_spec()

**Ubicación**: `BESTLIB/charts/rug.py:98`

**Flujo**:
- `get_spec()` llama a:
  1. `validate_data()` - Valida que los datos sean correctos
  2. `prepare_data()` - Prepara los datos en formato estándar
  3. Construye el spec final con `type`, `data`, `options`, etc.

**Formato del spec generado**:
```python
{
    'type': 'rug',
    'data': [{'x': 5.1, 'y': 0}, {'x': 4.9, 'y': 0}, ...],  # ← Problema aquí
    'options': {
        'color': '#4a90e2',
        'size': 2,
        'opacity': 0.6,
        'axis': 'x',
        'xLabel': 'value'  # Si se proporciona
    },
    'encoding': {'x': {'field': 'value'}}
}
```

### 3. Almacenamiento en MatrixLayout._map

**Ubicación**: `BESTLIB/matrix.py:1883`

**Nota importante**: `_map` es un diccionario de clase (`@classmethod`), por lo que todos los specs se almacenan en `MatrixLayout._map[letter]`.

### 4. Preparación para Renderizado (_prepare_repr_data)

**Ubicación**: `BESTLIB/matrix.py:2165`

**Flujo**:
1. Carga JS y CSS (cacheado)
2. Combina `MatrixLayout._map` con metadata:
   ```python
   mapping_merged = {**MatrixLayout._map, **meta}
   ```
3. Sanitiza para JSON:
   ```python
   mapping_js = json.dumps(_sanitize_for_json(mapping_merged))
   ```

### 5. Sanitización JSON (_sanitize_for_json)

**Ubicación**: `BESTLIB/matrix.py:2476`

**Problemas potenciales**:
- ✅ Convierte `numpy.int64` → `int`
- ✅ Convierte `numpy.float64` → `float`
- ✅ Convierte `numpy.ndarray` → `list`
- ⚠️ **Problema**: Si `prepare_data()` devuelve estructuras anidadas complejas, pueden perderse campos
- ⚠️ **Problema**: Los nombres de campos deben ser strings válidos para JSON

**Ejemplo de conversión**:
```python
# Antes (Python)
{'x': np.float64(5.1), 'y': np.int32(0)}

# Después (JSON)
{'x': 5.1, 'y': 0}
```

### 6. Serialización y Entrega al JS

**Ubicación**: `BESTLIB/matrix.py:2252` (`_generate_render_js`)

**Flujo**:
1. El mapping se serializa a JSON string
2. Se inyecta en el HTML como:
   ```javascript
   const mapping = JSON.parse('{"R": {"type": "rug", "data": [...]}, ...}');
   ```
3. Se llama a `render(divId, asciiLayout, mapping)`

### 7. Renderizado en JavaScript

**Ubicación**: `BESTLIB/matrix.js:212` (`render()`)

**Flujo**:
1. `render()` parsea el layout ASCII
2. Para cada celda, busca el spec en `mapping[letter]`
3. Determina si es D3 chart: `isD3Spec(spec)`
4. Si es D3, llama a `renderChartD3(container, spec, d3, divId)`

### 8. renderChartD3() y renderRugD3()

**Ubicación**: `BESTLIB/matrix.js:1291` (`renderChartD3`)

**Flujo**:
1. `renderChartD3()` hace switch por `spec.type`
2. Para `type === 'rug'`, llama a `renderRugD3(container, spec, d3, divId)`
3. `renderRugD3()` lee:
   - `spec.data` - Array de objetos `{x: ..., y: ...}`
   - `spec.options.color` - Color de los ticks
   - `spec.options.size` - Tamaño de los ticks
   - `spec.options.axis` - 'x' o 'y'

## Puntos de Falla Identificados

### 🔴 Problema 1: Formato de datos en prepare_rug_data()

**Ubicación**: `BESTLIB/charts/rug.py:56`

**Problema actual**:
```python
rug_data.append({
    'x': float(val),
    'y': 0  # ← Este campo 'y' no es necesario para rug
})
```

**Formato deseado**:
```python
rug_data.append({
    'x': float(val)  # Solo 'x' es necesario
})
```

**Impacto**: El campo `y: 0` es redundante y puede confundir el renderizado.

### 🔴 Problema 2: Lectura inconsistente de opciones en JS

**Ubicación**: `BESTLIB/matrix.js:7470-7474`

**Problema actual**:
```javascript
const color = options.color || spec.color || '#4a90e2';
```

**Problema**: Algunos gráficos leen directamente `spec.color` en lugar de `spec.options.color`.

**Solución**: Unificar a:
```javascript
const opt = spec.options || {};
const color = opt.color || spec.color || '#4a90e2';  // Fallback para compatibilidad
```

### 🔴 Problema 3: Ejes y labels inconsistentes

**Ubicación**: Varios gráficos en `BESTLIB/matrix.js`

**Problemas**:
- Cada gráfico implementa sus propios ejes
- Labels no están centrados consistentemente
- Y-label no está rotado correctamente
- Márgenes inconsistentes

**Solución**: Crear funciones reutilizables:
- `renderXAxis(svg, xScale, height, margin, xLabel)`
- `renderYAxis(svg, yScale, width, margin, yLabel)`

### 🔴 Problema 4: Márgenes y centrado inconsistentes

**Problema**: Cada gráfico calcula márgenes de forma diferente.

**Solución**: Usar márgenes estándar:
```javascript
const margin = {top: 25, right: 25, bottom: 45, left: 55};
```

### 🟡 Problema 5: Nombres de campos (snake_case vs camelCase)

**Análisis**:
- Python usa `snake_case`: `xLabel`, `yLabel`, `strokeWidth`
- JavaScript también usa `camelCase`: `xLabel`, `yLabel`, `strokeWidth`
- ✅ **Consistente**: Ambos usan camelCase para opciones

**No hay problema aquí**.

### 🟡 Problema 6: Spec.options vs spec directo

**Análisis**:
- Los gráficos nuevos guardan opciones en `spec.options`
- Los gráficos antiguos pueden tener opciones directamente en `spec`
- ⚠️ **Necesita fallback**: Leer de `spec.options.*` primero, luego `spec.*`

## Formato Estándar del Spec

### Spec Correcto para Rug

```json
{
  "type": "rug",
  "data": [
    {"x": 5.1},
    {"x": 4.9},
    {"x": 4.7}
  ],
  "options": {
    "color": "#4a90e2",
    "size": 2,
    "opacity": 0.6,
    "axis": "x",
    "strokeWidth": 2,
    "xLabel": "Value"
  }
}
```

### Spec Correcto para Otros Gráficos Nuevos

```json
{
  "type": "kde",
  "data": [
    {"x": 4.0, "y": 0.1},
    {"x": 4.5, "y": 0.2},
    ...
  ],
  "options": {
    "color": "#4a90e2",
    "strokeWidth": 2,
    "fill": true,
    "opacity": 0.3,
    "xLabel": "Value",
    "yLabel": "Density"
  }
}
```

## Campos que se Pierden en el Pipeline

### ✅ No se pierden campos importantes

El pipeline preserva:
- `type` ✅
- `data` ✅
- `options.*` ✅
- `encoding` ✅ (aunque no se usa en JS)

### ⚠️ Campos que pueden perderse

- `encoding` - Se genera en Python pero no se usa en JS
- Campos personalizados en `kwargs` que no están en `options` - Se pierden si no se agregan explícitamente

## Recomendaciones

1. **Corregir `prepare_rug_data()`**: Devolver solo `{'x': value}` sin `y: 0`
2. **Unificar lectura de opciones**: Siempre leer de `spec.options.*` con fallback a `spec.*`
3. **Crear funciones reutilizables**: `renderXAxis()` y `renderYAxis()`
4. **Estandarizar márgenes**: Usar el mismo objeto `margin` en todos los gráficos nuevos
5. **Añadir debug logging**: `console.log("[BESTLIB] renderRugD3()", spec)` para diagnóstico

## Checklist de Verificación

- [x] Pipeline analizado completamente
- [x] Puntos de falla identificados
- [x] Formato estándar del spec documentado
- [x] Campos que se pierden identificados
- [x] Recomendaciones proporcionadas

