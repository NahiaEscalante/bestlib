# Auditoría de Código Legacy en BESTLIB

**Fecha:** Diciembre 2024  
**Estado:** Auditoría completa de módulos legacy y sus usos

---

## Módulos Legacy Identificados

### 1. BESTLIB/matrix.py (2720 líneas)
**Estado:** LEGACY - Será eliminado en v0.2.0  
**Reemplazo:** BESTLIB/layouts/matrix.py

**Usos internos encontrados:**
- `BESTLIB/linked.py`: Importa desde `.matrix` (línea 9)
- `BESTLIB/reactive.py`: Importa con fallback (líneas 84-96)
- `BESTLIB/layouts/matrix.py`: Fallback a legacy (líneas 325, 454, 473, 495)

**Acción tomada:**
- Añadido header de WARNING grande
- Añadido `warnings.warn` con DeprecationWarning al importar
- Marcado como "no modificar, solo mantener para compatibilidad"

---

### 2. BESTLIB/reactive.py (4005 líneas)
**Estado:** LEGACY - Será eliminado en v0.2.0  
**Reemplazo:** BESTLIB/layouts/reactive.py + BESTLIB/reactive/

**Usos internos encontrados:**
- `BESTLIB/reactive/__init__.py`: Importa como fallback (líneas 23, 28, 49)
- `BESTLIB/matrix.py`: Importa SelectionModel (línea 2307)

**Acción tomada:**
- Añadido header de WARNING grande
- Añadido `warnings.warn` con DeprecationWarning al importar
- Marcado como "no modificar, solo mantener para compatibilidad"

---

### 3. BESTLIB/linked.py (805 líneas)
**Estado:** DEPRECATED - Será eliminado en v0.2.0  
**Reemplazo:** ReactiveMatrixLayout

**Usos internos encontrados:**
- `BESTLIB/__init__.py`: Importa para API pública (línea 92)
- Solo se usa si el usuario lo importa explícitamente

**Acción tomada:**
- Añadido header de WARNING grande
- Añadido `warnings.warn` con DeprecationWarning
- Documentada migración a ReactiveMatrixLayout

---

## Imports Cruzados (Modular ← → Legacy)

### De Modular a Legacy (ELIMINAR)

1. **BESTLIB/layouts/matrix.py → BESTLIB/matrix.py**
   - Líneas: 325, 454, 473, 495
   - Razón: Fallback para métodos que no se encontraron
   - **Acción requerida:** Eliminar estos fallbacks una vez que todo esté migrado

2. **BESTLIB/reactive/__init__.py → BESTLIB/reactive.py**
   - Líneas: 23, 28, 49
   - Razón: Fallback lazy import
   - **Acción requerida:** Eliminar estos fallbacks

### De Legacy a Legacy (OK por ahora)

1. **BESTLIB/linked.py → BESTLIB/matrix.py**
   - Línea: 9
   - Razón: LinkedViews depende de MatrixLayout legacy
   - **Acción:** OK por ahora, ambos son legacy

2. **BESTLIB/reactive.py → BESTLIB/matrix.py**
   - Líneas: 84-96
   - Razón: ReactiveMatrixLayout legacy depende de MatrixLayout
   - **Acción:** OK por ahora, ambos son legacy

### De Legacy a Modular (OK - vía imports públicos)

1. **BESTLIB/reactive.py → BESTLIB.matrix (public)**
   - Línea: 84
   - Usa: `from BESTLIB.matrix import MatrixLayout`
   - **Acción:** OK, usa la API pública

2. **BESTLIB/reactive.py → BESTLIB.layouts.matrix**
   - Línea: 88
   - Usa: `from BESTLIB.layouts.matrix import MatrixLayout`
   - **Acción:** OK, pero preferible usar API pública

---

## Uso Externo (Scripts de ejemplo y tests)

### Scripts que usan imports legacy:

```
examples/new_charts_test.py:8:        from BESTLIB.matrix import MatrixLayout
test_has_widgets.py:6:                from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
VALIDACION_KDE_COMPLETA.py:7:         from BESTLIB.matrix import MatrixLayout
TEST_NUEVOS_GRAFICOS.py:11:           from BESTLIB.matrix import MatrixLayout
SCRIPT_VALIDACION_FINAL.py:14:       import BESTLIB
SCRIPT_PRUEBA_COMPLETA.py:6:         from BESTLIB.matrix import MatrixLayout
SCRIPT_DIAGNOSTICO_DASHBOARD.py:15:  from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
SCRIPT_DIAGNOSTICO_DASHBOARD.py:16:  from BESTLIB.matrix import MatrixLayout
PRUEBA_CORRECCIONES_AVANZADOS.py:8:  from BESTLIB.matrix import MatrixLayout
EJEMPLO_MATRIZ_COMPLETA.py:8:        from BESTLIB.matrix import MatrixLayout
EJEMPLO_COLAB_COMPLETO.py:11:        from BESTLIB.matrix import MatrixLayout
EJEMPLOS_INDIVIDUALES.py:8:          from BESTLIB.matrix import MatrixLayout
```

**Acción tomada:**
- Estos scripts ahora recibirán DeprecationWarning
- Deben migrar a: `from BESTLIB import MatrixLayout`
- Los warnings les indicarán cómo migrar

---

## Wrappers de Compatibilidad

### BESTLIB/compat/

**Estado:** Mantener como thin shim  
**Propósito:** Proporcionar funciones `map_*` legacy que deleguen a la implementación modular

**Archivos:**
- `chart_wrappers.py`: Wrappers para `map_scatter`, `map_barchart`, etc.
- `matrix_wrapper.py`: Wrapper para MatrixLayout legacy

**Acción requerida:**
- Asegurar que sean thin wrappers (delegar inmediatamente a modular)
- No duplicar lógica de datos o renderizado
- Solo traducir API antigua → API moderna

---

## Plan de Eliminación de Legacy

### Fase 1: Preparación (Actual - v0.1.x)
- ✅ Marcar módulos legacy con warnings
- ✅ Documentar API pública moderna
- ✅ Proveer ejemplos de migración
- ⏳ Actualizar ejemplos y scripts para usar API moderna

### Fase 2: Deprecation (v0.1.5+)
- Hacer warnings más visibles
- Añadir guías de migración en errores
- Actualizar toda la documentación

### Fase 3: Preparación para Eliminación (v0.2.0-beta)
- Eliminar imports cruzados de modular → legacy
- Convertir legacy modules en stubs que solo lancen ImportError con guía
- Eliminar todo código duplicado

### Fase 4: Eliminación (v0.2.0)
- Eliminar completamente:
  - `BESTLIB/matrix.py`
  - `BESTLIB/reactive.py`
  - `BESTLIB/linked.py`
- Mantener solo:
  - `BESTLIB/layouts/`
  - `BESTLIB/reactive/`
  - `BESTLIB/charts/`
  - `BESTLIB/data/`
  - `BESTLIB/core/`
  - `BESTLIB/render/`
  - `BESTLIB/utils/`
  - `BESTLIB/compat/` (thin shim mínimo)

---

## Checklist de Migración para Usuarios

### Si usas: `from BESTLIB.matrix import MatrixLayout`
**Cambiar a:**
```python
from BESTLIB import MatrixLayout
```

### Si usas: `from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel`
**Cambiar a:**
```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel
```

### Si usas: `LinkedViews`
**Cambiar a:**
```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel

# En lugar de:
# linked = LinkedViews()
# linked.add_scatter('scatter1', data, interactive=True)
# linked.add_barchart('bar1', category_field='category')
# linked.display()

# Usar:
selection = SelectionModel()
layout = ReactiveMatrixLayout("SB", selection_model=selection)
layout.set_data(data)
layout.add_scatter('S', x_col='x', y_col='y', category_col='category', interactive=True)
layout.add_barchart('B', category_col='category', linked_to='S')
layout.display()
```

---

## Resumen de Acciones Completadas

1. ✅ Auditoría completa de imports legacy
2. ✅ Marcado de `matrix.py`, `reactive.py`, `linked.py` como legacy/deprecated
3. ✅ Añadido DeprecationWarnings a imports directos
4. ✅ Documentado qué imports son legacy y cuál es su reemplazo
5. ✅ Identificado todos los scripts que usan imports legacy
6. ✅ Simplificado `BESTLIB/__init__.py` para usar solo versión modular

---

## Próximos Pasos

1. ⏳ Actualizar scripts de ejemplo para usar API moderna
2. ⏳ Eliminar fallbacks de modular → legacy
3. ⏳ Reducir `compat/` a thin shims mínimos
4. ⏳ Crear tests de compatibilidad

---

**Última actualización:** Diciembre 2024  
**Completado por:** Sistema de limpieza de código BESTLIB

