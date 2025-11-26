# Guía de Migración desde Código Legacy

**Versión:** 0.1.0 → 0.2.0  
**Fecha:** Diciembre 2024  
**Estado:** Guía completa de migración desde API legacy a API moderna

---

## ⚠️ Código Legacy que será Eliminado en v0.2.0

Los siguientes módulos y APIs serán eliminados en la versión 0.2.0:

1. ❌ `BESTLIB/matrix.py` (importación directa)
2. ❌ `BESTLIB/reactive.py` (importación directa)
3. ❌ `BESTLIB/linked.LinkedViews`
4. ❌ `BESTLIB/compat/*` (wrappers)

---

## 📋 Tabla de Migración Rápida

| Legacy (ELIMINAR) | Moderno (USAR) |
|-------------------|----------------|
| `from BESTLIB.matrix import MatrixLayout` | `from BESTLIB import MatrixLayout` |
| `from BESTLIB.reactive import ReactiveMatrixLayout` | `from BESTLIB import ReactiveMatrixLayout` |
| `from BESTLIB.reactive import SelectionModel` | `from BESTLIB import SelectionModel` |
| `from BESTLIB.linked import LinkedViews` | `from BESTLIB import ReactiveMatrixLayout` |
| `from BESTLIB.compat import map_scatter` | `from BESTLIB import MatrixLayout` |

---

## 1. Migración de Imports Directos

### ❌ Legacy: Import desde `BESTLIB.matrix`

```python
# ❌ ELIMINAR ESTO
from BESTLIB.matrix import MatrixLayout
```

### ✅ Moderno: Import desde API pública

```python
# ✅ USAR ESTO
from BESTLIB import MatrixLayout
```

**Razón:** La API pública garantiza estabilidad. Los módulos internos pueden cambiar.

---

### ❌ Legacy: Import desde `BESTLIB.reactive`

```python
# ❌ ELIMINAR ESTO
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
```

### ✅ Moderno: Import desde API pública

```python
# ✅ USAR ESTO
from BESTLIB import ReactiveMatrixLayout, SelectionModel
```

---

## 2. Migración de LinkedViews

### ❌ Legacy: Usar `LinkedViews`

```python
# ❌ ELIMINAR ESTO
from BESTLIB.linked import LinkedViews

linked = LinkedViews()
linked.add_scatter('scatter1', data, x_field='x', y_field='y', 
                  category_field='species', interactive=True)
linked.add_barchart('bar1', category_field='species')
linked.display()
```

### ✅ Moderno: Usar `ReactiveMatrixLayout`

```python
# ✅ USAR ESTO
from BESTLIB import ReactiveMatrixLayout, SelectionModel

# Crear modelo de selección
selection = SelectionModel()

# Crear layout reactivo con ASCII
layout = ReactiveMatrixLayout("SB", selection_model=selection)
layout.set_data(data)

# Agregar gráficos
layout.add_scatter('S', x_col='x', y_col='y', 
                  category_col='species', interactive=True)
layout.add_barchart('B', category_col='species', linked_to='S')

# Mostrar
layout.display()
```

**Beneficios:**
- ✅ Más flexible con layouts ASCII
- ✅ Mejor integración con sistema reactivo
- ✅ Más funcionalidades (30+ gráficos)

---

## 3. Migración de Wrappers de Compatibilidad

### ❌ Legacy: Usar `compat.map_*`

```python
# ❌ ELIMINAR ESTO
from BESTLIB.compat import map_scatter, map_barchart

map_scatter('S', data, x_col='x', y_col='y')
map_barchart('B', data, category_col='category')
layout = MatrixLayout("SB")
layout.display()
```

### ✅ Moderno: Usar métodos de `MatrixLayout` directamente

```python
# ✅ USAR ESTO
from BESTLIB import MatrixLayout

MatrixLayout.map_scatter('S', data, x_col='x', y_col='y')
MatrixLayout.map_barchart('B', data, category_col='category')

layout = MatrixLayout("SB")
layout.display()
```

---

## 4. Migración de Métodos `map_*` Legacy

Los métodos `map_*` en `MatrixLayout` aún están disponibles pero recomendamos migrar a `ReactiveMatrixLayout` o usar `ChartRegistry` para mayor flexibilidad.

### ⚠️ Funciona pero menos recomendado:

```python
from BESTLIB import MatrixLayout

MatrixLayout.map_scatter('S', data, x_col='x', y_col='y')
layout = MatrixLayout("S")
layout.display()
```

### ✅ Más recomendado (para casos complejos):

```python
from BESTLIB import ReactiveMatrixLayout

layout = ReactiveMatrixLayout("S")
layout.set_data(data)
layout.add_scatter('S', x_col='x', y_col='y', interactive=True)
layout.display()
```

### ✅ Alternativa avanzada (usar ChartRegistry):

```python
from BESTLIB import MatrixLayout, ChartRegistry

# Obtener chart y generar spec
scatter_chart = ChartRegistry.get('scatter')
spec = scatter_chart.get_spec(data, x_col='x', y_col='y')

# Mapear al layout
MatrixLayout._map['S'] = spec
layout = MatrixLayout("S")
layout.display()
```

---

## 5. Ejemplos Completos de Migración

### Ejemplo 1: Scatter Plot Simple

#### ❌ Legacy

```python
from BESTLIB.matrix import MatrixLayout
import pandas as pd

df = pd.read_csv('data.csv')
MatrixLayout.map_scatter('S', df, x_col='x', y_col='y', 
                         category_col='species')
layout = MatrixLayout("S")
layout.display()
```

#### ✅ Moderno

```python
from BESTLIB import MatrixLayout
import pandas as pd

df = pd.read_csv('data.csv')
MatrixLayout.map_scatter('S', df, x_col='x', y_col='y', 
                         category_col='species')
layout = MatrixLayout("S")
layout.display()
```

**Cambio:** Solo el import (de `BESTLIB.matrix` → `BESTLIB`)

---

### Ejemplo 2: Vistas Enlazadas

#### ❌ Legacy

```python
from BESTLIB.linked import LinkedViews
import pandas as pd

df = pd.read_csv('data.csv')

linked = LinkedViews()
linked.add_scatter('scatter1', df, x_field='x', y_field='y', 
                  category_field='species', interactive=True)
linked.add_barchart('bar1', category_field='species')
linked.display()
```

#### ✅ Moderno

```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel
import pandas as pd

df = pd.read_csv('data.csv')

# Crear modelo de selección
selection = SelectionModel()

# Layout con ASCII art
layout = ReactiveMatrixLayout("SB", selection_model=selection)
layout.set_data(df)

# Agregar gráficos
layout.add_scatter('S', x_col='x', y_col='y', 
                  category_col='species', interactive=True)
layout.add_barchart('B', category_col='species', linked_to='S')

layout.display()

# Acceder a selección
print(f"Seleccionados: {selection.get_count()}")
print(layout.selected_data)  # DataFrame con datos seleccionados
```

**Cambios:**
1. `LinkedViews` → `ReactiveMatrixLayout`
2. Usar layout ASCII (`"SB"`) en lugar de IDs de vistas
3. `x_field` → `x_col` (nombres de parámetros consistentes)
4. Acceso a datos seleccionados más directo

---

### Ejemplo 3: Dashboard Complejo

#### ❌ Legacy

```python
from BESTLIB.matrix import MatrixLayout
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel

# ... código usando imports legacy
```

#### ✅ Moderno

```python
from BESTLIB import MatrixLayout, ReactiveMatrixLayout, SelectionModel
import pandas as pd

df = pd.read_csv('data.csv')

# Layout ASCII 2x2
layout = ReactiveMatrixLayout("""
    SB
    HX
""", selection_model=SelectionModel())

layout.set_data(df)

# Scatter interactivo
layout.add_scatter('S', x_col='x', y_col='y', 
                  category_col='species', interactive=True)

# Bar chart enlazado
layout.add_barchart('B', category_col='species', linked_to='S')

# Histogram enlazado
layout.add_histogram('H', column='x', bins=20, linked_to='S')

# Boxplot enlazado
layout.add_boxplot('X', column='y', category_col='species', linked_to='S')

layout.display()
```

---

## 6. Verificar Warnings de Deprecación

Cuando uses código legacy, BESTLIB emitirá warnings:

```python
DeprecationWarning: BESTLIB.matrix es código legacy y será eliminado en v0.2.0.
Usa 'from BESTLIB import MatrixLayout' en su lugar.
```

**Acción:** Lee estos warnings y migra tu código cuanto antes.

---

## 7. Checklist de Migración

### Para cada archivo que usa BESTLIB:

- [ ] Buscar `from BESTLIB.matrix import`
  - Cambiar a: `from BESTLIB import MatrixLayout`

- [ ] Buscar `from BESTLIB.reactive import`
  - Cambiar a: `from BESTLIB import ReactiveMatrixLayout, SelectionModel`

- [ ] Buscar `from BESTLIB.linked import LinkedViews`
  - Migrar a: `ReactiveMatrixLayout` (ver ejemplos arriba)

- [ ] Buscar `from BESTLIB.compat import`
  - Eliminar completamente, usar API pública

- [ ] Ejecutar código y verificar que NO haya `DeprecationWarning`

- [ ] Leer [docs/API_PUBLICA.md](docs/API_PUBLICA.md) para API completa

---

## 8. Timeline de Eliminación

### v0.1.x (Actual)

- ✅ API moderna disponible
- ⚠️ API legacy funciona pero emite warnings
- ✅ Compatibilidad hacia atrás mantenida

### v0.1.5+ (Próximo)

- Warnings más prominentes
- Guías de migración en la documentación
- Ejemplos actualizados

### v0.2.0-beta (Preparación)

- Warnings convertidos en errores (con flag `BESTLIB_STRICT`)
- Última oportunidad para migrar

### v0.2.0 (Final)

- ❌ Código legacy eliminado completamente
- ✅ Solo API moderna disponible
- ✅ Codebase más limpio y mantenible

---

## 9. Soporte y Ayuda

### Si tienes problemas migrando:

1. **Lee la documentación:**
   - [docs/API_PUBLICA.md](docs/API_PUBLICA.md) - API completa
   - [ARQUITECTURA.md](ARQUITECTURA.md) - Estructura del proyecto
   - [AUDITORIA_LEGACY.md](AUDITORIA_LEGACY.md) - Detalles técnicos

2. **Revisa los ejemplos:**
   - `examples/demo_completo_bestlib.ipynb`
   - `examples/test_completo_iris.ipynb`

3. **Ejecuta los tests:**
   - `pytest tests/` (cuando estén disponibles)

---

## 10. Resumen

### ✅ Lo que DEBES hacer:

1. Usar `from BESTLIB import MatrixLayout, ReactiveMatrixLayout, SelectionModel`
2. Migrar de `LinkedViews` a `ReactiveMatrixLayout`
3. Eliminar imports de `BESTLIB.compat`
4. Leer warnings de deprecación y actuar

### ❌ Lo que NO debes hacer:

1. Importar directamente desde `BESTLIB.matrix` o `BESTLIB.reactive`
2. Usar `LinkedViews`
3. Usar `BESTLIB.compat.*`
4. Ignorar `DeprecationWarning`

---

**Última actualización:** Diciembre 2024  
**Próxima revisión:** v0.2.0-beta

**¿Preguntas?** Consulta [docs/API_PUBLICA.md](docs/API_PUBLICA.md)

