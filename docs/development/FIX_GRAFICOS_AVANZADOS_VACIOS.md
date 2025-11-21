# Fix: Gráficos Avanzados Aparecen Vacíos

## Problema Identificado

Los gráficos avanzados (kde, distplot, rug, qqplot, ecdf, hist2d, polar, ridgeline, ribbon, funnel) se renderizaban pero aparecían vacíos sin datos visibles.

## Análisis Realizado

1. **Verificación de specs Python**: Los specs se generan correctamente con `data` o `series` según corresponda.
2. **Verificación de serialización JSON**: La función `sanitize_for_json()` convierte correctamente los datos a tipos JSON.
3. **Verificación de funciones D3**: Las funciones JavaScript leen correctamente `spec.data` o `spec.series`.

## Correcciones Aplicadas

### 1. Validaciones de Datos Vacíos

Se agregaron validaciones al inicio de cada función de renderizado para detectar cuando no hay datos:

- `renderKdeD3`: Verifica que `spec.data` exista y tenga elementos
- `renderDistplotD3`: Verifica que `spec.data.histogram` tenga elementos
- `renderRugD3`: Verifica que `spec.data` exista y tenga elementos
- `renderQqplotD3`: Verifica que `spec.data` exista y tenga elementos
- `renderEcdfD3`: Verifica que `spec.data` exista y tenga elementos
- `renderRidgelineD3`: Verifica que `spec.series` exista y tenga keys
- `renderRibbonD3`: Verifica que `spec.data` exista y tenga elementos
- `renderHist2dD3`: Verifica que `spec.data` exista y tenga elementos
- `renderPolarD3`: Verifica que `spec.data` exista y tenga elementos
- `renderFunnelD3`: Verifica que `spec.data` exista y tenga elementos

### 2. Corrección de Cálculo de Dominios

**Distplot**: Se mejoró el cálculo de dominios X e Y para manejar correctamente arrays vacíos o datos faltantes.

**Ribbon**: Se corrigió el cálculo del dominio Y para manejar correctamente `y1` e `y2`, evitando errores cuando los valores son `null` o `undefined`.

### 3. Corrección de Polar Plot

El gráfico polar estaba usando coordenadas cartesianas pre-calculadas (`d.x`, `d.y`) que no estaban escaladas al tamaño del SVG. Se corrigió para:

- Recalcular coordenadas desde `d.angle` y `d.radius` usando la escala `r`
- Manejar casos donde solo existan coordenadas cartesianas (fallback)
- Escalar correctamente al tamaño del SVG

### 4. Logging de Diagnóstico

Se agregó logging opcional (cuando `window._bestlib_debug = true`) en `renderChartD3` para diagnosticar problemas con la estructura de datos de los gráficos avanzados.

## Archivos Modificados

- `BESTLIB/matrix.js`: 
  - Funciones `renderKdeD3`, `renderDistplotD3`, `renderRugD3`, `renderQqplotD3`, `renderEcdfD3`, `renderRidgelineD3`, `renderRibbonD3`, `renderHist2dD3`, `renderPolarD3`, `renderFunnelD3`
  - Función `renderChartD3` (logging de diagnóstico)

## Próximos Pasos para Diagnóstico

Si los gráficos siguen apareciendo vacíos después de estos cambios:

1. **Activar modo debug**:
   ```javascript
   window._bestlib_debug = true;
   ```

2. **Verificar en consola del navegador**:
   - Los mensajes `[BESTLIB] renderChartD3: ...` mostrarán la estructura del spec
   - Los mensajes `[BESTLIB] render*D3: No hay datos` indicarán si los datos están llegando vacíos

3. **Verificar el spec en Python**:
   ```python
   from BESTLIB.charts import ChartRegistry
   
   chart = ChartRegistry.get('kde')
   spec = chart.get_spec(df, column='value')
   print(spec)  # Verificar que 'data' tenga elementos
   ```

4. **Verificar serialización JSON**:
   ```python
   import json
   from BESTLIB.utils.json import sanitize_for_json
   
   spec = chart.get_spec(df, column='value')
   sanitized = sanitize_for_json(spec)
   print(json.dumps(sanitized, indent=2))  # Verificar que los datos se serialicen correctamente
   ```

## Notas

- Las validaciones agregadas no rompen la funcionalidad existente
- El logging de diagnóstico solo se activa si `window._bestlib_debug = true`
- Las correcciones son mínimas y no modifican la API pública

