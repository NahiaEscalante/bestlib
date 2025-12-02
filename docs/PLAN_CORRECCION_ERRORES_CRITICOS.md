# Plan de Corrección de Errores Críticos - BESTLIB

## Fecha: Diciembre 2025

Este documento detalla el análisis y plan de corrección para los 5 errores críticos reportados en los ejemplos.

---

## 🔍 ANÁLISIS DE ERRORES

### Error 1: Boxplot no se actualiza cuando hay selección en scatter enlazado

**Síntoma:**
- Usuario selecciona puntos en scatter plot con brush
- Boxplot enlazado NO cambia, permanece estático
- No hay comunicación entre scatter y boxplot

**Causa Raíz Identificada:**

1. **Falta de comunicación JavaScript → Python:**
   - El callback `update_boxplot` se registra correctamente en Python
   - PERO: No hay JavaScript que envíe eventos de selección desde el scatter al SelectionModel
   - El scatter genera eventos D3 de brush, pero no los propaga al backend Python

2. **`_register_chart` no actualiza el DOM:**
   - Cuando `update_boxplot` llama a `self._register_chart()`, solo actualiza `self._layout._map` (Python)
   - NO genera JavaScript para re-renderizar el boxplot en el navegador
   - El spec se actualiza en memoria pero el DOM nunca se entera

3. **Falta de mecanismo de actualización:**
   - Barchart tiene JavaScript manual (`display(Javascript(js_update))`) que actualiza el DOM
   - Boxplot NO tiene este mecanismo, solo actualiza el spec en Python

**Solución Propuesta:**

1. Agregar JavaScript de actualización en `update_boxplot` similar a `update_barchart`
2. Generar código D3 que re-renderice el boxplot con los nuevos datos
3. Usar `display(Javascript(...))` para ejecutar la actualización en el navegador

---

### Error 2: Barchart aumenta de altura con múltiples selecciones

**Síntoma:**
- Primera selección: barchart se actualiza correctamente
- Selecciones subsecuentes: el gráfico crece en altura (eje Y se expande)
- El contenedor aumenta de tamaño progresivamente

**Causa Raíz Identificada:**

1. **JavaScript manual manipula el DOM directamente:**
   ```javascript
   const svg = d3.select(targetCell).select('svg');
   svg.selectAll('*').remove();  // Elimina contenido
   // ... crea nuevo SVG ...
   ```

2. **No preserva dimensiones originales:**
   - Cada actualización recalcula `height` basado en `targetCell.clientHeight`
   - Si el contenedor creció en la iteración anterior, usa ese tamaño como base
   - Efecto acumulativo: altura aumenta en cada selección

3. **Escalas Y se recalculan sin límites:**
   ```javascript
   const yScale = d3.scaleLinear()
       .domain([0, d3.max(newData, d => d.value)])  // Máximo cambia
       .range([height - margin.bottom, margin.top]);
   ```
   - Si `height` aumenta, el rango Y también aumenta
   - Barras se hacen más altas, empujando el contenedor

**Solución Propuesta:**

1. **Opción A (Preferida):** Reemplazar JavaScript manual con regeneración de spec completo
   - Similar a lo que se hizo con boxplot
   - Usar `self._register_chart()` + forzar re-render completo del layout
   - Delegar rendering a la lógica estándar de `matrix.js`

2. **Opción B (Parche):** Fijar dimensiones en el JavaScript manual
   - Guardar `originalHeight` en la primera creación
   - Usar siempre `originalHeight` en actualizaciones
   - Prevenir crecimiento acumulativo

---

### Error 3: Histogram lanza `ChartError: value_col es requerido`

**Síntoma:**
```python
dashboard.add_histogram('H', column='sepal_length', ...)
# ChartError: value_col es requerido para histogram
```

**Causa Raíz Identificada:**

1. **Inconsistencia en nombres de parámetros:**
   - `add_histogram()` recibe parámetro `column`
   - `_register_chart()` pasa `column=column` a `ChartRegistry.get('histogram').get_spec()`
   - `HistogramChart.get_spec()` espera `value_col`, NO `column`
   - `HistogramChart.validate_data()` verifica `value_col` y lanza error

2. **Código en `reactive.py` línea 1883-1897:**
   ```python
   self._register_chart(
       letter,
       'histogram',
       initial_data,
       column=column,  # ❌ INCORRECTO: debería ser value_col
       bins=bins,
       **kwargs_with_linked
   )
   ```

3. **Múltiples lugares con el mismo error:**
   - Línea 1363: `spec = self._register_chart(..., column=column, ...)`
   - Línea 1410: `self._register_chart(..., column=column, ...)`
   - Línea 1420: `self._register_chart(..., column=column, ...)`
   - Línea 1883: `self._register_chart(..., column=column, ...)`

**Solución Propuesta:**

Reemplazar `column=column` con `value_col=column` en todas las llamadas a `_register_chart` para histogramas.

---

### Error 4: Barcharts enlazados no muestran gráfico, solo etiqueta

**Síntoma:**
- Se crea layout con scatter + barchart
- Scatter se muestra correctamente
- Barchart solo muestra la letra 'B' o 'Y', sin gráfico

**Causa Raíz Identificada:**

1. **Barchart no se crea inicialmente:**
   - El método `add_barchart` con `linked_to` NO crea el gráfico inicial
   - Solo registra el callback `update_barchart`
   - Espera que el usuario haga una selección para crear el gráfico

2. **Código problemático en `add_barchart` (líneas 382-1007):**
   ```python
   def add_barchart(self, letter, category_col=None, value_col=None, linked_to=None, ...):
       # ... validaciones ...
       
       if linked_to:
           # ❌ Solo registra callback, NO crea gráfico inicial
           def update_barchart(items, count):
               # ... genera JavaScript ...
           
           primary_selection.on_change(update_barchart)
           return self  # ❌ Sale sin crear gráfico
       
       # Este código solo se ejecuta si NO hay linked_to
       self._register_chart(letter, 'bar', ...)
   ```

3. **Comparar con `add_boxplot` (que SÍ funciona):**
   - `add_boxplot` crea el gráfico inicial ANTES de registrar el callback
   - Usa `self._register_chart()` con todos los datos
   - Luego registra `update_boxplot` para actualizaciones

**Solución Propuesta:**

1. Crear el barchart inicial con todos los datos ANTES de registrar el callback
2. El callback solo debe ACTUALIZAR el gráfico existente
3. Seguir el patrón de `add_boxplot`:
   ```python
   # 1. Crear gráfico inicial
   self._register_chart(letter, 'bar', self._data, category_col=category_col, ...)
   
   # 2. Registrar callback para actualizaciones
   if linked_to:
       def update_barchart(items, count):
           # ... actualizar con datos filtrados ...
       primary_selection.on_change(update_barchart)
   ```

---

### Error 5: Boxplot en ejemplo 5 no se actualiza (mismo que Error 1)

**Síntoma:**
Idéntico al Error 1.

**Causa Raíz:**
La misma que Error 1.

**Solución:**
La misma que Error 1.

---

## 📋 PLAN DE CORRECCIÓN (Orden de Ejecución)

### Paso 1: Corregir Error 3 (Histogram - más simple)
**Prioridad:** 🔴 CRÍTICA (bloquea ejemplo 3)

**Acciones:**
1. Buscar todas las llamadas a `_register_chart` con `chart_type='histogram'`
2. Reemplazar `column=column` con `value_col=column`
3. Verificar que `HistogramChart.get_spec()` recibe el parámetro correcto

**Archivos a modificar:**
- `BESTLIB/layouts/reactive.py`: Líneas 1363, 1410, 1420, 1883 (y cualquier otra)

**Test de verificación:**
```python
dashboard = ReactiveMatrixLayout("SH")
dashboard.set_data(df)
dashboard.add_scatter('S', x_col='x', y_col='y', interactive=True)
dashboard.add_histogram('H', column='x', linked_to='S')  # No debe lanzar ChartError
dashboard.display()
```

---

### Paso 2: Corregir Error 4 (Barchart no se muestra inicialmente)
**Prioridad:** 🔴 CRÍTICA (afecta múltiples ejemplos)

**Acciones:**
1. Refactorizar `add_barchart` para crear gráfico inicial siempre
2. Mover la llamada a `_register_chart` ANTES del bloque `if linked_to:`
3. Asegurar que el callback solo actualice el gráfico existente

**Archivos a modificar:**
- `BESTLIB/layouts/reactive.py`: Método `add_barchart` (líneas 382-1007)

**Estructura propuesta:**
```python
def add_barchart(self, letter, category_col=None, value_col=None, linked_to=None, ...):
    # Validaciones...
    
    # 1. SIEMPRE crear gráfico inicial con todos los datos
    initial_data = self._data
    self._register_chart(
        letter, 'bar', initial_data,
        category_col=category_col,
        value_col=value_col,
        **kwargs
    )
    
    # 2. Si está enlazado, registrar callback para actualizaciones
    if linked_to:
        def update_barchart(items, count):
            # Filtrar datos según selección
            filtered_data = self._extract_filtered_data(items)
            
            # Regenerar spec con datos filtrados
            self._register_chart(
                letter, 'bar', filtered_data,
                category_col=category_col,
                value_col=value_col,
                **kwargs
            )
            
            # Forzar actualización del DOM
            self._force_chart_update(letter)
        
        primary_selection.on_change(update_barchart)
    
    return self
```

**Test de verificación:**
```python
layout = ReactiveMatrixLayout("AB")
layout.set_data(df)
layout.add_scatter('A', x_col='x', y_col='y', category_col='cat')
layout.add_barchart('B', category_col='cat')  # Debe mostrarse inmediatamente
layout.display()
```

---

### Paso 3: Corregir Error 1 y 5 (Boxplot no se actualiza)
**Prioridad:** 🔴 CRÍTICA (afecta ejemplos 1 y 5)

**Acciones:**
1. Agregar mecanismo de actualización del DOM en `update_boxplot`
2. Generar JavaScript para re-renderizar el boxplot
3. Usar `display(Javascript(...))` similar a `update_barchart`

**Archivos a modificar:**
- `BESTLIB/layouts/reactive.py`: Método `add_boxplot`, callback `update_boxplot` (líneas 2134-2192)

**Código propuesto:**
```python
def update_boxplot(items, count):
    """Actualiza el boxplot cuando cambia la selección"""
    try:
        # 1. Extraer datos filtrados
        data_to_use = self._extract_filtered_data(items) if items else self._data
        
        # 2. Regenerar spec con datos filtrados
        self._register_chart(
            letter, 'boxplot', data_to_use,
            category_col=category_col,
            value_col=column,
            **kwargs_update
        )
        
        # 3. NUEVO: Generar JavaScript para actualizar el DOM
        spec = self._layout._map[letter]
        js_update = self._generate_boxplot_update_js(letter, spec)
        
        # 4. Ejecutar JavaScript en el navegador
        from IPython.display import Javascript, display
        display(Javascript(js_update), display_id=f'boxplot-update-{letter}', update=True)
        
    except Exception as e:
        print(f"⚠️ Error actualizando boxplot: {e}")
```

**Método helper nuevo:**
```python
def _generate_boxplot_update_js(self, letter, spec):
    """Genera JavaScript para actualizar un boxplot en el DOM"""
    import json
    
    box_data_json = json.dumps(spec['data'])
    
    js = f"""
    (function() {{
        // Buscar celda del boxplot
        const cells = document.querySelectorAll('.matrix-cell');
        let targetCell = null;
        for (const cell of cells) {{
            if (cell.textContent.includes('{letter}')) {{
                targetCell = cell;
                break;
            }}
        }}
        
        if (!targetCell) return;
        
        // Obtener dimensiones originales
        const svg = d3.select(targetCell).select('svg');
        const originalWidth = parseInt(svg.attr('width')) || 400;
        const originalHeight = parseInt(svg.attr('height')) || 300;
        
        // Limpiar y re-renderizar
        svg.selectAll('*').remove();
        
        const boxData = {box_data_json};
        const margin = {{top: 40, right: 30, bottom: 60, left: 60}};
        const width = originalWidth;
        const height = originalHeight;
        
        // ... código D3 para renderizar boxplot ...
        // (similar al de matrix.js pero inline)
        
    }})();
    """
    
    return js
```

**Test de verificación:**
```python
demo = ReactiveMatrixLayout("SX")
demo.set_data(df)
demo.add_scatter('S', x_col='x', y_col='y', interactive=True)
demo.add_boxplot('X', column='x', category_col='cat', linked_to='S')
demo.display()
# Seleccionar puntos → boxplot DEBE actualizarse
```

---

### Paso 4: Corregir Error 2 (Barchart crece en altura)
**Prioridad:** 🟡 ALTA (afecta UX pero no bloquea funcionalidad)

**Acciones:**
1. **Opción A (Recomendada):** Eliminar JavaScript manual de `update_barchart`
   - Reemplazar con el mismo enfoque del Paso 3 (regenerar spec + forzar render)
   - Delegar rendering completo a la lógica estándar

2. **Opción B (Parche rápido):** Fijar dimensiones en JavaScript manual
   - Guardar `originalHeight` en primera ejecución
   - Usar siempre ese valor en actualizaciones

**Archivos a modificar:**
- `BESTLIB/layouts/reactive.py`: Callback `update_barchart` (líneas 659-997)

**Código propuesto (Opción A):**
```python
def update_barchart(items, count):
    """Actualiza el barchart cuando cambia la selección"""
    try:
        # 1. Extraer datos filtrados
        data_to_use = self._extract_filtered_data(items) if items else self._data
        
        # 2. Regenerar spec
        self._register_chart(
            letter, 'bar', data_to_use,
            category_col=category_col,
            value_col=value_col,
            **kwargs
        )
        
        # 3. Generar JavaScript de actualización
        spec = self._layout._map[letter]
        js_update = self._generate_barchart_update_js(letter, spec)
        
        # 4. Ejecutar en navegador
        from IPython.display import Javascript, display
        display(Javascript(js_update), display_id=f'barchart-update-{letter}', update=True)
        
    except Exception as e:
        print(f"⚠️ Error actualizando barchart: {e}")
```

**Test de verificación:**
```python
demo = ReactiveMatrixLayout("SB")
demo.set_data(df)
demo.add_scatter('S', x_col='x', y_col='y', interactive=True)
demo.add_barchart('B', category_col='cat', linked_to='S')
demo.display()
# Hacer 5 selecciones diferentes → altura debe permanecer constante
```

---

## 🔧 HELPERS COMUNES A IMPLEMENTAR

### Helper 1: `_extract_filtered_data`
```python
def _extract_filtered_data(self, items):
    """
    Extrae datos filtrados desde items de selección.
    Maneja _original_rows, _original_row, y items directos.
    """
    if not items:
        return self._data
    
    processed_items = []
    for item in items:
        if isinstance(item, dict):
            if '_original_rows' in item:
                processed_items.extend(item['_original_rows'])
            elif '_original_row' in item:
                processed_items.append(item['_original_row'])
            else:
                processed_items.append(item)
        else:
            processed_items.append(item)
    
    if HAS_PANDAS and processed_items:
        import pandas as pd
        return pd.DataFrame(processed_items)
    
    return processed_items
```

### Helper 2: `_force_chart_update`
```python
def _force_chart_update(self, letter):
    """
    Fuerza la actualización del DOM para un chart específico.
    Genera y ejecuta JavaScript para re-renderizar.
    """
    spec = self._layout._map.get(letter)
    if not spec:
        return
    
    chart_type = spec.get('type')
    
    if chart_type == 'boxplot':
        js = self._generate_boxplot_update_js(letter, spec)
    elif chart_type == 'bar':
        js = self._generate_barchart_update_js(letter, spec)
    elif chart_type == 'histogram':
        js = self._generate_histogram_update_js(letter, spec)
    else:
        return
    
    from IPython.display import Javascript, display
    display(Javascript(js), display_id=f'{chart_type}-update-{letter}', update=True)
```

---

## 📊 RESUMEN DE IMPACTO

| Error | Severidad | Ejemplos Afectados | Esfuerzo | Riesgo |
|-------|-----------|-------------------|----------|--------|
| Error 3 (Histogram) | 🔴 Crítico | 3 | Bajo | Bajo |
| Error 4 (Barchart inicial) | 🔴 Crítico | 2, 4 | Medio | Medio |
| Error 1/5 (Boxplot update) | 🔴 Crítico | 1, 5 | Alto | Alto |
| Error 2 (Barchart altura) | 🟡 Alto | 2 | Medio | Bajo |

**Orden de ejecución recomendado:** 3 → 4 → 1/5 → 2

**Tiempo estimado:** 4-6 horas de desarrollo + 2 horas de testing

---

## ✅ CRITERIOS DE ÉXITO

1. **Error 3:** `add_histogram` con `linked_to` no lanza `ChartError`
2. **Error 4:** Barcharts enlazados se muestran inmediatamente al crear el layout
3. **Error 1/5:** Boxplots se actualizan visualmente cuando hay selección en scatter
4. **Error 2:** Barcharts mantienen altura constante en múltiples selecciones
5. **Todos los ejemplos:** Los 5 ejemplos de `ejemplo_completo_corregido.py` funcionan sin errores

---

## 🧪 SUITE DE TESTS A CREAR

```python
# tests/test_linked_views_integration.py

def test_histogram_with_linked_to_no_error():
    """Error 3: histogram debe aceptar column y linked_to"""
    layout = ReactiveMatrixLayout("SH")
    layout.set_data(df)
    layout.add_scatter('S', x_col='x', y_col='y', interactive=True)
    layout.add_histogram('H', column='x', linked_to='S')  # No debe fallar
    assert 'H' in layout._layout._map

def test_barchart_shows_initially():
    """Error 4: barchart debe mostrarse sin necesidad de selección"""
    layout = ReactiveMatrixLayout("AB")
    layout.set_data(df)
    layout.add_scatter('A', x_col='x', y_col='y')
    layout.add_barchart('B', category_col='cat', linked_to='A')
    
    # Verificar que el spec existe
    assert 'B' in layout._layout._map
    spec = layout._layout._map['B']
    assert spec['type'] == 'bar'
    assert len(spec['data']) > 0  # Debe tener datos iniciales

def test_boxplot_updates_on_selection():
    """Error 1/5: boxplot debe actualizarse cuando cambia selección"""
    layout = ReactiveMatrixLayout("SX")
    layout.set_data(df)
    layout.add_scatter('S', x_col='x', y_col='y', interactive=True)
    layout.add_boxplot('X', column='x', category_col='cat', linked_to='S')
    
    # Simular selección
    selection = layout._primary_view_models['S']
    selection.set_items([{'x': 1, 'y': 2, 'cat': 'A'}])
    
    # Verificar que el spec se actualizó
    spec = layout._layout._map['X']
    # (Verificar que los datos cambiaron)

def test_barchart_height_stable():
    """Error 2: barchart debe mantener altura constante"""
    layout = ReactiveMatrixLayout("SB")
    layout.set_data(df)
    layout.add_scatter('S', x_col='x', y_col='y', interactive=True)
    layout.add_barchart('B', category_col='cat', linked_to='S')
    
    selection = layout._primary_view_models['S']
    
    # Hacer 5 selecciones
    for i in range(5):
        selection.set_items([{'x': i, 'y': i, 'cat': 'A'}])
    
    # Verificar que el spec no tiene dimensiones crecientes
    # (Esto es difícil de testear sin navegador, pero podemos verificar
    # que el JavaScript generado usa dimensiones fijas)
```

---

## 🚨 RIESGOS Y MITIGACIONES

### Riesgo 1: JavaScript inline puede no funcionar en todos los entornos
**Mitigación:** Testear en Jupyter Lab, Jupyter Notebook y Google Colab

### Riesgo 2: Race conditions en actualizaciones simultáneas
**Mitigación:** Usar flags `_bestlib_updating_{letter}` como en barchart actual

### Riesgo 3: Dimensiones del DOM pueden no estar disponibles
**Mitigación:** Guardar dimensiones originales en el spec al crear el gráfico

### Riesgo 4: Refactor de barchart puede romper funcionalidad existente
**Mitigación:** Crear tests de regresión antes de modificar

---

## 📝 NOTAS ADICIONALES

- **Patrón común:** Todos los charts enlazados deben seguir el mismo patrón:
  1. Crear gráfico inicial con todos los datos
  2. Registrar callback para actualizaciones
  3. En callback: regenerar spec + forzar actualización del DOM

- **Centralización:** Considerar crear una clase base `LinkedChart` que maneje este patrón

- **Documentación:** Actualizar `BUGFIXES.md` con estos nuevos bugs y soluciones

- **Deuda técnica:** El JavaScript manual es frágil. Considerar:
  - Usar Jupyter Comm para comunicación bidireccional
  - Implementar un sistema de eventos más robusto
  - Migrar a Jupyter Widgets para mejor integración

