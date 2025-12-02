# Correcciones de Bugs Críticos - BESTLIB

## Fecha: Diciembre 2025

Este documento detalla los bugs críticos encontrados y corregidos en la librería BESTLIB.

---

## Bug 1: Error "letras inexistentes en el layout"

### Síntoma
```
❌ Error: Se encontraron gráficos asignados a letras inexistentes en el layout: ['X']
```

Aparecía al crear un segundo dashboard después de haber creado uno previo con letras diferentes.

### Causa Raíz
- `MatrixLayout._map` era una **variable de clase** compartida por todas las instancias
- Al crear un nuevo dashboard, heredaba specs de dashboards anteriores vía `self._map = copy.deepcopy(self.__class__._map)`
- La validación `_validate_mapping_letters` comparaba el layout actual contra TODO el mapa global

### Solución Implementada
1. **Convertir `_map` a variable de instancia**: Cada `MatrixLayout` ahora tiene su propio `_map = {}` independiente
2. **Eliminar broadcast**: Removidos `_broadcast_spec` y `_broadcast_full_map` que propagaban specs a todas las instancias
3. **Convertir `_register_spec` a método de instancia**: Ya no modifica una variable de clase
4. **Filtrar mapping en render**: `_prepare_repr_data` ahora filtra el mapping para incluir solo letras del layout actual
5. **Ajustar validación**: `_validate_mapping_letters` ya no lanza error por letras extra, solo valida que las del layout tengan specs

### Archivos Modificados
- `BESTLIB/layouts/matrix.py`: Líneas 57-263
- `BESTLIB/layouts/reactive.py`: Múltiples referencias actualizadas

### Tests Agregados
- `tests/test_multiple_layouts.py`: 9 tests que verifican aislamiento entre instancias

---

## Bug 2: Boxplots enlazados con altura incorrecta y ejes perdidos

### Síntoma
Al seleccionar puntos en un scatter plot enlazado a un boxplot:
- El boxplot cambiaba de altura inesperadamente
- Los ejes X desaparecían
- Solo se veía la caja sin etiquetas

### Causa Raíz
- El callback `update_boxplot` generaba ~400 líneas de JavaScript manual
- Establecía `style.minHeight/maxHeight` fijos en la celda
- Calculaba escalas D3 manualmente sin usar el pipeline normal de render
- No preservaba las dimensiones originales ni los márgenes correctos

### Solución Implementada
1. **Eliminar JavaScript manual**: Removido todo el bloque de generación de JS inline
2. **Usar pipeline normal**: Ahora regenera el spec con `self._register_chart` y deja que el sistema normal renderice
3. **Preservar metadata**: `__linked_to__` se mantiene en el spec actualizado
4. **Simplificar callback**: De ~400 líneas a ~50 líneas

### Código Anterior (problemático)
```python
def update_boxplot(items, count):
    # ... 100+ líneas calculando box_data manualmente ...
    js_update = f"""
    (function() {{
        // ... 200+ líneas de JavaScript manual ...
        targetCell.style.minHeight = height + 'px';
        targetCell.style.maxHeight = height + 'px';
        // ... más código manual ...
    }})();
    """
    display(Javascript(js_update))
```

### Código Nuevo (correcto)
```python
def update_boxplot(items, count):
    # Extraer datos originales
    data_to_use = self._data
    if items and len(items) > 0:
        # ... procesar items ...
        data_to_use = pd.DataFrame(processed_items)
    
    # Regenerar spec con datos filtrados
    self._register_chart(
        letter, 'boxplot', data_to_use,
        category_col=category_col,
        value_col=column,
        **kwargs_update
    )
```

### Archivos Modificados
- `BESTLIB/layouts/reactive.py`: Método `add_boxplot`, líneas 1893-2214

### Tests Agregados
- `tests/test_reactive_integration.py`: Test específico `test_no_attribute_error_on_boxplot`

---

## Bug 3: Violin plots sin datos (error rojo en UI)

### Síntoma
```
Error en Violin Plot:
Se encontraron 3 violines pero ninguno tiene datos válidos
Verifica que los datos tengan la estructura correcta: {category: string, profile: [{y: number, w: number}]}
```

### Causa Raíz
- `ViolinChart.prepare_data` era un placeholder que solo devolvía `{'category': cat, 'values': [...]}`
- No calculaba perfiles de densidad (KDE)
- JavaScript esperaba `profile: [{y, w}]` pero recibía `values: [...]`

### Solución Implementada
1. **Implementar KDE real**: Usar `scipy.stats.gaussian_kde` para calcular densidades
2. **Normalizar densidades**: El máximo `w` es siempre 1.0
3. **Fallback a histograma**: Si scipy no está disponible, usar `np.histogram`
4. **Estructura correcta**: Devolver `{category, profile: [{y: float, w: float}]}`

### Código Implementado
```python
def prepare_data(self, data, value_col=None, category_col=None, bins=50, **kwargs):
    # Agrupar valores por categoría
    groups = defaultdict(list)
    # ... agrupar ...
    
    # Calcular perfiles de densidad
    violin_data = []
    for cat, values in groups.items():
        if HAS_SCIPY:
            kde = stats.gaussian_kde(values)
            y_points = np.linspace(y_min, y_max, bins)
            densities = kde(y_points)
            normalized = densities / max(densities)
            profile = [{'y': float(y), 'w': float(w)} for y, w in zip(y_points, normalized)]
        else:
            profile = self._histogram_fallback(values, bins)
        
        violin_data.append({'category': cat, 'profile': profile})
    
    return violin_data
```

### Archivos Modificados
- `BESTLIB/charts/violin.py`: Implementación completa de `prepare_data`
- `BESTLIB/layouts/reactive.py`: Método `add_violin` actualizado para usar `_register_chart`

### Tests Agregados
- `tests/test_violin_chart.py`: 13 tests que verifican perfiles no vacíos, estructura correcta, normalización

---

## Bug 4: `AttributeError: type object 'MatrixLayout' has no attribute '_map'`

### Síntoma
```python
AttributeError: type object 'MatrixLayout' has no attribute '_map'
```

Aparecía al llamar `add_boxplot` o `add_histogram` con `linked_to`.

### Causa Raíz
Código legacy que quedó después del refactor:
- Línea 1888: `if letter in MatrixLayout._map and linked_to:`
- Línea 2309: `MatrixLayout._register_spec(letter, boxplot_spec)`
- Líneas 1363, 1410, 1417: `MatrixLayout.map_histogram(...)`

Estos intentaban acceder a la variable de clase `_map` que ya no existe.

### Solución Implementada
1. **Reemplazar `MatrixLayout._map`** → `self._layout._map` (14 ocurrencias)
2. **Reemplazar `MatrixLayout._register_spec`** → `self._layout._register_spec` o `self._register_chart`
3. **Reemplazar `MatrixLayout.map_*`** → `self._register_chart` en métodos críticos
4. **Eliminar código duplicado**: Bloque legacy de 100+ líneas que calculaba `box_data` manualmente

### Archivos Modificados
- `BESTLIB/layouts/reactive.py`: 
  - 14 referencias a `MatrixLayout._map` corregidas
  - 9 referencias a `MatrixLayout.update_spec_metadata` corregidas
  - Código legacy eliminado (líneas 2213-2311)

---

## Bug 5: Conflictos de dependencias en Google Colab

### Síntoma
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
google-colab 1.0.0 requires ipykernel==6.17.1, but you have ipykernel 7.1.0 which is incompatible.
```

El runtime de Colab se reiniciaba después de instalar `pybestlib`.

### Causa Raíz
- `pyproject.toml` y `setup.py` declaraban `ipython>=8`, `ipykernel>=6`, `jupyterlab>=4`, `notebook>=7` como dependencias obligatorias
- Colab viene con versiones específicas de estos paquetes
- `pip install` intentaba actualizar todo el stack de Jupyter, rompiendo el entorno de Colab

### Solución Implementada
**Documentación clara** en lugar de cambios de código:
- Instrucciones específicas para Colab: usar `--no-deps`
- Instrucciones específicas para Jupyter local: instalación normal
- Snippet de verificación post-instalación

### Archivos Modificados
- `README.md`: Sección de instalación con instrucciones diferenciadas
- `docs/QUICK_REFERENCE.md`: Snippet de instalación al inicio

### Comando Correcto para Colab
```python
!pip install --no-deps git+https://github.com/NahiaEscalante/bestlib.git
```

---

## Resumen de Impacto

| Bug | Severidad | Estado | Tests |
|-----|-----------|--------|-------|
| Letras inexistentes | 🔴 Crítico | ✅ Corregido | 9 tests |
| Boxplot altura/ejes | 🔴 Crítico | ✅ Corregido | 6 tests |
| Violin sin datos | 🟡 Alto | ✅ Corregido | 13 tests |
| AttributeError _map | 🔴 Crítico | ✅ Corregido | 6 tests |
| Conflictos Colab | 🟡 Alto | ✅ Documentado | N/A |

**Total de tests agregados**: 34 tests nuevos

---

## Verificación

Para verificar que todos los bugs están corregidos:

```python
# Test 1: Múltiples dashboards sin interferencia
layout1 = ReactiveMatrixLayout("AB")
layout1.set_data(df)
layout1.add_scatter('A', x_col='x', y_col='y')
layout1.add_barchart('B', category_col='cat')

layout2 = ReactiveMatrixLayout("XY")  # No debe dar error de letras inexistentes
layout2.set_data(df)
layout2.add_scatter('X', x_col='x', y_col='y')
layout2.add_barchart('Y', category_col='cat')

# Test 2: Boxplot enlazado
demo = ReactiveMatrixLayout("SX")
demo.set_data(df)
demo.add_scatter('S', x_col='x', y_col='y', interactive=True)
demo.add_boxplot('X', column='x', linked_to='S')  # No debe dar AttributeError
demo.display()

# Test 3: Violin con datos reales
demo2 = ReactiveMatrixLayout("SV")
demo2.set_data(df)
demo2.add_scatter('S', x_col='x', y_col='y', interactive=True)
demo2.add_violin('V', value_col='x', category_col='cat', linked_to='S')  # Debe mostrar perfiles
demo2.display()
```

