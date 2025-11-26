# Auditoría de Lógica de Preparación y Validación de Datos

**Fecha:** Diciembre 2024  
**Alcance:** BESTLIB/data/ y duplicaciones en otros módulos  
**Estado:** Auditoría completa de preparación/validación de datos

---

## Resumen Ejecutivo

### Módulos de Datos Centralizados (BESTLIB/data/)

- ✅ `preparators.py` - Funciones centralizadas de preparación de datos
- ✅ `validators.py` - Funciones centralizadas de validación
- ✅ `transformers.py` - Transformaciones DataFrame ↔ listas
- ✅ `aggregators.py` - Agregaciones de datos

### Duplicaciones Encontradas

- ⚠️ `BESTLIB/matrix.py` - Métodos `_prepare_data()`, `_validate_data()` locales
- ⚠️ `BESTLIB/reactive.py` - Métodos similares de preparación
- ⚠️ `BESTLIB/layouts/matrix.py` - Algunos métodos helper duplicados
- ✅ `BESTLIB/layouts/reactive.py` - Ya usa algunas funciones de `data/`

---

## Funciones Centralizadas en BESTLIB/data/

### preparators.py

Funciones disponibles:
- `prepare_scatter_data(data, x_col, y_col, category_col, size_col, color_col)`
- `prepare_bar_data(data, category_col, value_col)`
- `prepare_histogram_data(data, value_col, bins)`
- `prepare_boxplot_data(data, value_col, category_col)`
- `prepare_heatmap_data(data, x_col, y_col, value_col)`
- `prepare_line_data(data, x_col, y_col, series_col)`
- `prepare_pie_data(data, category_col, value_col)`

**Estado:** ✅ Bien organizadas y reutilizables

### validators.py

Funciones disponibles:
- `validate_data_structure(data, required_type)`
- `validate_columns(data, required_columns, optional_columns)`
- `validate_scatter_data(data, x_col, y_col, category_col)`
- `validate_bar_data(data, category_col, value_col)`

**Estado:** ✅ Funciones específicas por tipo de gráfico

### transformers.py

Funciones disponibles:
- `dataframe_to_dicts(df)` - Convierte DataFrame a lista de dicts
- `dicts_to_dataframe(dicts)` - Convierte lista de dicts a DataFrame
- `normalize_data(data)` - Normaliza datos a formato estándar

**Estado:** ✅ Helpers útiles para conversión

### aggregators.py

Funciones disponibles:
- `aggregate_by_category(data, category_col, value_col, agg_func)`
- `count_by_category(data, category_col)`
- `group_by_multiple(data, group_cols, value_col, agg_func)`

**Estado:** ✅ Agregaciones reutilizables

---

## Duplicaciones en BESTLIB/matrix.py (Legacy)

### Funciones duplicadas:

1. **`_prepare_data(data, x_col, y_col, category_col, value_col)`**
   - **Líneas:** ~99-169
   - **Propósito:** Convierte DataFrame a formato estándar
   - **Duplica:** `BESTLIB/data/preparators.py` y `transformers.py`
   - **Estado:** ⚠️ LEGACY - Mantener por compatibilidad pero no modificar

2. **`_validate_data(data, required_cols, required_type)`**
   - **Líneas:** ~172-244
   - **Propósito:** Valida estructura de datos y columnas
   - **Duplica:** `BESTLIB/data/validators.py`
   - **Estado:** ⚠️ LEGACY - Mantener por compatibilidad pero no modificar

3. **`_figsize_to_pixels(figsize)`**
   - **Líneas:** ~60-81
   - **Propósito:** Convierte figsize de pulgadas a píxeles
   - **Duplica:** `BESTLIB/utils/figsize.py`
   - **Estado:** ⚠️ LEGACY - Mantener por compatibilidad pero no modificar

**Recomendación:** NO modificar `matrix.py` ya que es legacy. La versión modular ya usa las funciones centralizadas.

---

## Uso en BESTLIB/layouts/matrix.py (Modular)

### Estado Actual:

✅ **Ya usa funciones centralizadas:**
- Importa de `..data.preparators` para scatter, bar, etc.
- Importa de `..data.validators` para validación
- Importa de `..utils.figsize` para conversión de figsize

**Código encontrado:**
```python
from ..data.preparators import prepare_scatter_data, prepare_bar_data, ...
from ..data.validators import validate_scatter_data, validate_bar_data
from ..utils.figsize import figsize_to_pixels, process_figsize_in_kwargs
```

**Estado:** ✅ EXCELENTE - Ya está usando la arquitectura modular correctamente

---

## Uso en BESTLIB/layouts/reactive.py (Modular)

### Estado Actual:

⚠️ **Mixto - Usa algunas funciones centralizadas pero tiene lógica local:**

**Funciones centralizadas usadas:**
- Importa `MatrixLayout` que ya usa `data/preparators`
- Delega preparación inicial a `MatrixLayout.map_*`

**Lógica local encontrada:**
- Preparación específica para datos enlazados (linked views)
- Transformaciones para DataFrames seleccionados
- Agregaciones para bar charts reactivos

**Estado:** ⚠️ ACEPTABLE - Tiene lógica específica de reactividad que no está en `data/`

**Recomendación:** Esto está bien, la lógica específica de reactividad puede quedarse en `reactive.py`

---

## Uso en BESTLIB/charts/*.py (Gráficos Modulares)

### Estado Actual:

✅ **Excelente - Todos usan funciones centralizadas:**

**Ejemplo - scatter.py:**
```python
from ..data.preparators import prepare_scatter_data
from ..data.validators import validate_scatter_data

class ScatterChart(ChartBase):
    def prepare_data(self, data, **kwargs):
        return prepare_scatter_data(data, x_col=kwargs['x_col'], ...)
    
    def validate_data(self, data, **kwargs):
        validate_scatter_data(data, x_col=kwargs['x_col'], ...)
```

**Estado:** ✅ PERFECTO - Arquitectura modular funcionando correctamente

---

## Plan de Unificación

### Fase 1: Estado Actual (Completado ✅)

- ✅ Módulos `data/` creados y funcionales
- ✅ `layouts/matrix.py` usa funciones centralizadas
- ✅ `charts/*.py` usan funciones centralizadas
- ✅ `__init__.py` expone funciones de `data/` en API pública

### Fase 2: Mantener Legacy Aislado (Actual)

- ✅ `matrix.py` y `reactive.py` legacy marcados como no modificar
- ✅ Duplicaciones en legacy documentadas pero no eliminadas (por compatibilidad)
- ✅ Toda nueva funcionalidad debe usar solo `data/`

### Fase 3: Eliminación de Legacy (v0.2.0)

- ⏳ Cuando se eliminen `matrix.py` y `reactive.py`, las duplicaciones desaparecerán automáticamente
- ⏳ Solo quedarán las versiones centralizadas en `data/`

---

## Verificación de Uso Correcto

### ✅ Casos de Uso Correctos:

1. **Nuevo gráfico en charts/**
   ```python
   from ..data.preparators import prepare_MY_data
   from ..data.validators import validate_MY_data
   
   class MyChart(ChartBase):
       def prepare_data(self, data, **kwargs):
           return prepare_MY_data(data, **kwargs)
   ```

2. **Layout modular**
   ```python
   from ..data import prepare_scatter_data
   
   def add_scatter(self, ...):
       prepared_data, original_data = prepare_scatter_data(data, x_col, y_col)
   ```

3. **API pública**
   ```python
   from BESTLIB import prepare_scatter_data, validate_scatter_data
   
   # Usuario puede usar directamente si quiere
   data_prep = prepare_scatter_data(df, 'x', 'y')
   ```

### ❌ Casos de Uso INCORRECTOS (a evitar):

1. **NO crear helpers locales que dupliquen `data/`**
   ```python
   # ❌ MAL - duplica lógica
   def _my_prepare_data(data):
       # lógica que ya existe en data/preparators
   ```

2. **NO ignorar funciones de `data/` en código nuevo**
   ```python
   # ❌ MAL - debería usar prepare_scatter_data()
   scatter_data = []
   for row in df.iterrows():
       scatter_data.append({'x': row['x'], 'y': row['y']})
   ```

---

## Conclusiones y Recomendaciones

### ✅ Estado Actual (Excelente)

1. ✅ Módulos `data/` bien organizados y centralizados
2. ✅ Código modular (`layouts/`, `charts/`) usa correctamente `data/`
3. ✅ Duplicaciones solo existen en código legacy que será eliminado
4. ✅ API pública expone funciones de `data/` para usuarios avanzados

### 📋 Acciones Completadas

1. ✅ Auditoría de duplicaciones
2. ✅ Verificación de uso correcto en código modular
3. ✅ Documentación de legacy vs modular
4. ✅ No se requieren cambios urgentes

### ⏳ Acciones Futuras (v0.2.0)

1. Al eliminar `matrix.py` y `reactive.py`, las duplicaciones desaparecerán automáticamente
2. Agregar más funciones a `data/` según se necesiten nuevos tipos de gráficos
3. Mantener documentación de `data/` actualizada

### 🎯 Recomendación Final

**NO hacer cambios ahora.** La arquitectura modular ya está funcionando correctamente. Las duplicaciones solo existen en código legacy que será eliminado en v0.2.0.

**Para nuevo desarrollo:**
- ✅ SIEMPRE usar funciones de `BESTLIB/data/`
- ✅ NUNCA duplicar lógica de preparación/validación
- ✅ Agregar nuevas funciones a `data/` si se necesitan

---

**Última actualización:** Diciembre 2024  
**Estado:** ✅ Auditoría completada - Arquitectura modular funcionando correctamente

