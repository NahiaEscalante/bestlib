# API Pública de BESTLIB

**Versión:** 0.1.0  
**Fecha:** Diciembre 2024  
**Estado:** Definición oficial para mantener compatibilidad hacia atrás

---

## Resumen Ejecutivo

Este documento define la **API pública oficial** de BESTLIB que debe mantenerse compatible hacia atrás. Cualquier función, clase o método listado aquí está garantizado para funcionar en futuras versiones menores (0.x.y).

---

## 1. Imports Principales

### 1.1 Layouts

```python
from BESTLIB import MatrixLayout
from BESTLIB import ReactiveMatrixLayout
```

**`MatrixLayout`**
- Clase principal para crear layouts estáticos con gráficos
- Ubicación interna: `BESTLIB/layouts/matrix.py` (modular)
- Legacy: `BESTLIB/matrix.py` (mantener solo para compatibilidad)

**`ReactiveMatrixLayout`**
- Clase para layouts reactivos con vistas enlazadas
- Ubicación interna: `BESTLIB/layouts/reactive.py` (modular)
- Legacy: `BESTLIB/reactive.py` (mantener solo para compatibilidad)

### 1.2 Sistema Reactivo

```python
from BESTLIB import SelectionModel
from BESTLIB import ReactiveData
from BESTLIB import ReactiveEngine
from BESTLIB import LinkManager
```

**`SelectionModel`**
- Modelo para gestionar selecciones reactivas
- Ubicación: `BESTLIB/reactive/selection.py`

**`ReactiveData`**
- Contenedor de datos reactivos
- Ubicación: `BESTLIB/reactive/selection.py`

**`ReactiveEngine`**
- Motor de reactividad
- Ubicación: `BESTLIB/reactive/engine.py`

**`LinkManager`**
- Gestor de enlaces entre vistas
- Ubicación: `BESTLIB/reactive/linking.py`

### 1.3 Vistas Enlazadas (Legacy/Deprecated)

```python
from BESTLIB import LinkedViews  # DEPRECATED: usar ReactiveMatrixLayout
```

**`LinkedViews`**
- Sistema antiguo de vistas enlazadas
- Ubicación: `BESTLIB/linked.py`
- **Estado:** DEPRECATED - será eliminado en v0.2.0
- **Migración:** Usar `ReactiveMatrixLayout` en su lugar

### 1.4 Sistema de Gráficos

```python
from BESTLIB import ChartRegistry
from BESTLIB import ChartBase
```

**`ChartRegistry`**
- Registry global de tipos de gráficos
- Ubicación: `BESTLIB/charts/registry.py`
- **Uso:** Registrar y obtener tipos de gráficos personalizados

**`ChartBase`**
- Clase base abstracta para crear gráficos personalizados
- Ubicación: `BESTLIB/charts/base.py`

### 1.5 Excepciones

```python
from BESTLIB import BestlibError
from BESTLIB import LayoutError
from BESTLIB import ChartError
from BESTLIB import DataError
from BESTLIB import RenderError
from BESTLIB import CommunicationError
```

Todas ubicadas en: `BESTLIB/core/exceptions.py`

### 1.6 Core (Opcional para usuarios avanzados)

```python
from BESTLIB import CommManager
from BESTLIB import EventManager
```

**`CommManager`**
- Gestor de comunicación bidireccional JS ↔ Python
- Ubicación: `BESTLIB/core/comm.py`

**`EventManager`**
- Gestor de eventos
- Ubicación: `BESTLIB/core/events.py`

---

## 2. API de MatrixLayout

### 2.1 Construcción

```python
layout = MatrixLayout(ascii_layout, figsize=None, row_heights=None, 
                      col_widths=None, gap=None, cell_padding=None, 
                      max_width=None)
```

**Parámetros:**
- `ascii_layout` (str): Layout ASCII definiendo la estructura
- `figsize` (tuple, opcional): Tamaño global (width, height) en pulgadas
- `row_heights` (list, opcional): Alturas por fila
- `col_widths` (list, opcional): Anchos por columna
- `gap` (int, opcional): Espaciado entre celdas en píxeles
- `cell_padding` (int, opcional): Padding de celdas
- `max_width` (int, opcional): Ancho máximo del layout

### 2.2 Métodos Estáticos de Mapeo (map_*)

Todos estos métodos son estáticos y configuran gráficos:

```python
MatrixLayout.map_scatter(letter, data, x_col, y_col, category_col=None, **kwargs)
MatrixLayout.map_barchart(letter, data, category_col, value_col=None, **kwargs)
MatrixLayout.map_histogram(letter, data, value_col, bins=20, **kwargs)
MatrixLayout.map_boxplot(letter, data, category_col=None, value_col=None, **kwargs)
MatrixLayout.map_heatmap(letter, data, x_col, y_col, value_col, **kwargs)
MatrixLayout.map_correlation_heatmap(letter, data, **kwargs)
MatrixLayout.map_line(letter, data, x_col, y_col, series_col=None, **kwargs)
MatrixLayout.map_pie(letter, data, category_col, value_col=None, **kwargs)
MatrixLayout.map_violin(letter, data, value_col, category_col=None, **kwargs)
MatrixLayout.map_radviz(letter, data, features, class_col, **kwargs)
MatrixLayout.map_star_coordinates(letter, data, features, class_col, **kwargs)
MatrixLayout.map_parallel_coordinates(letter, data, dimensions, category_col=None, **kwargs)
MatrixLayout.map_grouped_barchart(letter, data, main_col, sub_col, value_col=None, **kwargs)
```

**Nota:** Estos métodos son parte de la API pública, pero internamente deberían delegar a la implementación modular en `charts/` y `data/`.

### 2.3 Métodos de Instancia

```python
layout.display()                              # Renderizar el layout
layout.on(event, callback)                    # Registrar callback por evento
layout.connect_selection(reactive_model)      # Conectar modelo reactivo
```

### 2.4 Métodos de Clase

```python
MatrixLayout.set_debug(enabled)               # Activar/desactivar debug
MatrixLayout.register_comm(force=False)       # Registrar comm manualmente
MatrixLayout.on_global(event, callback)       # Callback global
```

---

## 3. API de ReactiveMatrixLayout

### 3.1 Construcción

```python
layout = ReactiveMatrixLayout(ascii_layout, selection_model=None, 
                              figsize=None, **kwargs)
```

**Parámetros:**
- `ascii_layout` (str): Layout ASCII
- `selection_model` (SelectionModel, opcional): Modelo de selección compartido
- `figsize` (tuple, opcional): Tamaño global
- `**kwargs`: Parámetros adicionales de MatrixLayout

### 3.2 Métodos add_* (Gráficos Reactivos)

```python
layout.add_scatter(letter, x_col, y_col, category_col=None, interactive=True, **kwargs)
layout.add_barchart(letter, category_col, value_col=None, linked_to=None, **kwargs)
layout.add_histogram(letter, column, bins=20, linked_to=None, **kwargs)
layout.add_boxplot(letter, column=None, category_col=None, linked_to=None, **kwargs)
layout.add_heatmap(letter, x_col, y_col, value_col, linked_to=None, **kwargs)
layout.add_correlation_heatmap(letter, linked_to=None, **kwargs)
layout.add_line(letter, x_col, y_col, series_col=None, linked_to=None, **kwargs)
layout.add_pie(letter, category_col, value_col=None, linked_to=None, **kwargs)
layout.add_violin(letter, value_col, category_col=None, linked_to=None, **kwargs)
layout.add_grouped_barchart(letter, main_col, sub_col, value_col=None, linked_to=None, **kwargs)
```

**Gráficos Avanzados:**

```python
layout.add_kde(letter, column, bandwidth=None, linked_to=None, **kwargs)
layout.add_distplot(letter, column, bins=30, kde=True, rug=False, linked_to=None, **kwargs)
layout.add_rug(letter, column, axis='x', linked_to=None, **kwargs)
layout.add_qqplot(letter, column, dist='norm', linked_to=None, **kwargs)
layout.add_ecdf(letter, column, linked_to=None, **kwargs)
layout.add_ridgeline(letter, column, category_col, bandwidth=None, linked_to=None, **kwargs)
layout.add_ribbon(letter, x_col, y1_col, y2_col, linked_to=None, **kwargs)
layout.add_hist2d(letter, x_col, y_col, bins=20, linked_to=None, **kwargs)
layout.add_polar(letter, angle_col, radius_col, angle_unit='rad', linked_to=None, **kwargs)
layout.add_funnel(letter, stage_col, value_col, linked_to=None, **kwargs)
layout.add_radviz(letter, features, class_col, linked_to=None, **kwargs)
layout.add_star_coordinates(letter, features, class_col, linked_to=None, **kwargs)
layout.add_parallel_coordinates(letter, dimensions, category_col=None, linked_to=None, **kwargs)
```

### 3.3 Métodos de Gestión de Datos

```python
layout.set_data(data)                         # Establecer datos globales
layout.display()                              # Renderizar layout reactivo
```

### 3.4 Propiedades

```python
layout.selection_widget                       # Widget de selección (ipywidgets)
layout.items                                  # Items seleccionados actualmente
layout.selected_data                          # DataFrame de datos seleccionados
layout.count                                  # Número de items seleccionados
```

---

## 4. API de SelectionModel

```python
from BESTLIB import SelectionModel

selection = SelectionModel()
selection.set_items(items)                    # Establecer items seleccionados
selection.get_items()                         # Obtener items seleccionados
selection.get_count()                         # Número de items
selection.clear()                             # Limpiar selección
selection.observe(callback)                   # Observar cambios
```

---

## 5. API de ChartRegistry (Para Usuarios Avanzados)

```python
from BESTLIB import ChartRegistry, ChartBase

# Registrar un nuevo tipo de gráfico
ChartRegistry.register(MyCustomChart)

# Obtener un gráfico por tipo
chart = ChartRegistry.get('my_chart_type')

# Listar todos los tipos
types = ChartRegistry.list_types()

# Verificar si está registrado
exists = ChartRegistry.is_registered('scatter')
```

---

## 6. Compatibilidad con Funciones Legacy

Estas funciones están disponibles por compatibilidad pero internamente delegan a la implementación modular:

```python
from BESTLIB.compat import (
    map_scatter,
    map_barchart,
    map_histogram,
    map_boxplot,
    map_heatmap,
    map_line,
    map_pie,
    map_grouped_barchart
)
```

**Nota:** Estas funciones son wrappers sobre `MatrixLayout.map_*` y se mantienen solo para compatibilidad hacia atrás.

---

## 7. Ejemplos de Uso Público

### Ejemplo 1: Layout Estático Simple

```python
from BESTLIB import MatrixLayout
import pandas as pd

df = pd.read_csv('data.csv')

# Configurar gráficos
MatrixLayout.map_scatter('S', df, x_col='x', y_col='y', category_col='species')
MatrixLayout.map_barchart('B', df, category_col='species')

# Crear y mostrar layout
layout = MatrixLayout("S\nB")
layout.display()
```

### Ejemplo 2: Layout Reactivo con Vistas Enlazadas

```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel
import pandas as pd

df = pd.read_csv('data.csv')

# Crear modelo de selección compartido
selection = SelectionModel()

# Crear layout reactivo
layout = ReactiveMatrixLayout("SB", selection_model=selection)
layout.set_data(df)

# Agregar scatter interactivo
layout.add_scatter('S', x_col='x', y_col='y', category_col='species', interactive=True)

# Agregar bar chart enlazado (se actualiza cuando se selecciona en scatter)
layout.add_barchart('B', category_col='species', linked_to='S')

# Mostrar
layout.display()

# Acceder a datos seleccionados
print(f"Seleccionados: {layout.count} items")
print(layout.selected_data)
```

### Ejemplo 3: Usar ChartRegistry

```python
from BESTLIB import ChartRegistry, MatrixLayout

# Ver todos los tipos de gráficos disponibles
print("Gráficos disponibles:", ChartRegistry.list_types())

# Obtener un gráfico específico
scatter_chart = ChartRegistry.get('scatter')

# Usar el gráfico
spec = scatter_chart.get_spec(data, x_col='x', y_col='y')
```

---

## 8. Deprecations (Funcionalidades Marcadas para Eliminación)

### v0.2.0 (Futuro)

Las siguientes funcionalidades serán eliminadas en v0.2.0:

1. **`LinkedViews`** → Migrar a `ReactiveMatrixLayout`
2. **Imports directos de `BESTLIB.matrix`** → Usar `from BESTLIB import MatrixLayout`
3. **Imports directos de `BESTLIB.reactive`** → Usar `from BESTLIB import ReactiveMatrixLayout`

---

## 9. Versiones Internas (No Público)

Los siguientes módulos son de uso interno y **NO** forman parte de la API pública:

- `BESTLIB/matrix.py` (legacy, usar `layouts/matrix.py`)
- `BESTLIB/reactive.py` (legacy, usar `layouts/reactive.py`)
- `BESTLIB/data/*` (uso interno)
- `BESTLIB/render/*` (uso interno)
- `BESTLIB/utils/*` (uso interno, excepto exports explícitos)
- `BESTLIB/compat/*` (wrappers internos)

---

## 10. Garantías de Compatibilidad

BESTLIB sigue [Semantic Versioning](https://semver.org/):

- **Versiones 0.x.y**: API puede cambiar, pero mantenemos compatibilidad con imports principales
- **Versiones 1.x.y**: API pública estable, cambios solo en versiones mayores

### Cambios Permitidos en Versiones Menores (0.x.y → 0.x.(y+1))

- Agregar nuevos métodos/clases
- Agregar parámetros opcionales con valores por defecto
- Deprecar funcionalidades (con warnings)
- Corregir bugs

### Cambios NO Permitidos en Versiones Menores

- Eliminar clases/métodos públicos
- Cambiar firmas de métodos existentes
- Cambiar comportamiento de métodos sin avisar

---

**Última actualización:** Diciembre 2024  
**Mantenido por:** Equipo BESTLIB

