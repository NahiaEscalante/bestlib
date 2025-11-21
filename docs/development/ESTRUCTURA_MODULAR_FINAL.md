# Estructura Modular Final de BESTLIB

**Fecha de creación**: 2025-01-XX
**Estado**: En progreso - Modularización incremental

## 📋 Resumen Ejecutivo

Este documento describe la estructura modular final de BESTLIB, resultado de la refactorización del código monolítico original en módulos organizados por responsabilidad.

## 🗂️ Estructura de Directorios

```
BESTLIB/
├── __init__.py                 # Punto de entrada principal
├── core/                       # ⚙️ Núcleo del sistema
│   ├── __init__.py
│   ├── exceptions.py          # Jerarquía de excepciones
│   ├── registry.py            # Registry global de componentes
│   ├── comm.py                # Sistema de comunicación JS ↔ Python
│   ├── events.py              # Sistema de eventos y callbacks
│   └── layout.py              # Layout Engine (parsing ASCII)
├── data/                       # 📊 Procesamiento de datos
│   ├── __init__.py
│   ├── preparators.py         # Preparadores para cada tipo de gráfico
│   ├── validators.py          # Validadores de datos
│   ├── transformers.py        # Transformadores DataFrame ↔ dicts
│   └── aggregators.py         # Agregadores (group_by, bin, stats)
├── charts/                     # 📈 Sistema de gráficos
│   ├── __init__.py            # Registro automático de gráficos
│   ├── base.py                # ChartBase (clase abstracta)
│   ├── registry.py            # ChartRegistry
│   ├── scatter.py             # ScatterChart
│   ├── bar.py                 # BarChart
│   ├── histogram.py           # HistogramChart
│   ├── boxplot.py             # BoxplotChart
│   ├── heatmap.py             # HeatmapChart
│   ├── line.py                # LineChart
│   ├── pie.py                 # PieChart
│   ├── violin.py              # ViolinChart (placeholder)
│   ├── radviz.py              # RadvizChart (placeholder)
│   ├── star_coordinates.py    # StarCoordinatesChart (placeholder)
│   ├── parallel_coordinates.py # ParallelCoordinatesChart (placeholder)
│   └── grouped_bar.py         # GroupedBarChart
├── layouts/                    # 🔲 Sistema de layouts (PENDIENTE)
│   ├── __init__.py
│   ├── matrix.py              # MatrixLayout (refactorizado)
│   └── reactive.py            # ReactiveMatrixLayout (refactorizado)
├── reactive/                   # ⚡ Sistema reactivo (PENDIENTE)
│   ├── __init__.py
│   ├── engine.py              # ReactiveEngine
│   ├── selection.py           # SelectionModel
│   ├── linking.py             # LinkManager
│   └── engines/               # Engines de comunicación
│       ├── jupyter.py         # JupyterCommEngine
│       ├── colab.py           # ColabEngine
│       └── js_only.py         # JSOnlyFallback
├── render/                     # 🎨 Sistema de renderizado (PENDIENTE)
│   ├── __init__.py
│   ├── html.py                # HTML generator
│   ├── builder.py             # JS builder
│   ├── templates/             # Plantillas JS
│   └── assets.py              # Gestión de assets (JS/CSS)
├── utils/                      # 🛠️ Utilidades
│   ├── __init__.py
│   ├── json.py                # Sanitización JSON
│   └── figsize.py             # Conversión figsize
├── themes/                     # 🎨 Temas (FUTURO)
│   └── __init__.py
├── matrix.py                   # ⚠️ LEGACY - A migrar
├── reactive.py                 # ⚠️ LEGACY - A migrar
├── linked.py                   # ⚠️ LEGACY - Deprecated
├── matrix.js                   # ⚠️ LEGACY - A modularizar
├── d3.min.js                   # D3.js library
└── style.css                   # Estilos CSS
```

## ✅ Módulos Completados

### Core Module (`core/`)
- ✅ **exceptions.py**: Jerarquía completa de excepciones
  - `BestlibError` (base)
  - `LayoutError`, `ChartError`, `DataError`, `RenderError`, `CommunicationError`
  
- ✅ **registry.py**: Registry global de componentes
  - `Registry.register()`, `Registry.get()`, `Registry.list_components()`
  - Soporte para múltiples tipos de componentes
  
- ✅ **comm.py**: Sistema de comunicación JS ↔ Python
  - `CommManager` para gestión de Comm targets de Jupyter
  - Registro automático de instancias (weak references)
  - Routing de mensajes JS → Python
  
- ✅ **events.py**: Sistema de eventos y callbacks
  - `EventManager` con soporte para múltiples handlers
  - Handlers globales e instancia-específicos
  - Métodos: `on()`, `emit()`, `get_handlers()`
  
- ✅ **layout.py**: Layout Engine
  - `LayoutEngine.parse_ascii_layout()` - Parsing de layouts ASCII
  - `Grid` class para representación estructurada
  - Validación de layouts

### Data Module (`data/`)
- ✅ **validators.py**: Validación de datos
  - `validate_data_structure()`, `validate_columns()`, `validate_data_types()`
  - Validadores específicos: `validate_scatter_data()`, `validate_bar_data()`
  
- ✅ **transformers.py**: Transformación de datos
  - `dataframe_to_dicts()`, `dicts_to_dataframe()`
  - `normalize_types()`, `sanitize_for_json()`
  
- ✅ **preparators.py**: Preparación de datos por tipo de gráfico
  - `prepare_scatter_data()` - Scatter plots
  - `prepare_bar_data()` - Bar charts
  - `prepare_histogram_data()` - Histogramas
  - `prepare_boxplot_data()` - Boxplots
  - `prepare_heatmap_data()` - Heatmaps
  - `prepare_line_data()` - Line charts
  - `prepare_pie_data()` - Pie charts
  - `prepare_grouped_bar_data()` - Grouped bar charts
  
- ✅ **aggregators.py**: Agregación de datos
  - `group_by_category()` - Agrupación por categoría
  - `bin_numeric_data()` - Binning numérico
  - `calculate_statistics()` - Estadísticas básicas

### Charts Module (`charts/`)
- ✅ **base.py**: Clase base abstracta `ChartBase`
  - Métodos abstractos: `validate_data()`, `prepare_data()`, `get_spec()`
  - Propiedad `chart_type`
  
- ✅ **registry.py**: Registry de gráficos
  - `ChartRegistry.register()`, `ChartRegistry.get()`
  - Auto-registro de gráficos
  
- ✅ **Gráficos implementados**:
  - ✅ `ScatterChart` - Scatter plots completos
  - ✅ `BarChart` - Bar charts
  - ✅ `HistogramChart` - Histogramas
  - ✅ `BoxplotChart` - Boxplots
  - ✅ `HeatmapChart` - Heatmaps
  - ✅ `LineChart` - Line charts
  - ✅ `PieChart` - Pie charts
  - ✅ `GroupedBarChart` - Grouped bar charts
  
- ⚠️ **Gráficos placeholder** (estructura lista, implementación pendiente):
  - `ViolinChart`
  - `RadvizChart`
  - `StarCoordinatesChart`
  - `ParallelCoordinatesChart`

### Utils Module (`utils/`)
- ✅ **json.py**: Sanitización JSON
  - `sanitize_for_json()` - Convierte numpy/pandas a tipos Python nativos
  
- ✅ **figsize.py**: Conversión de figsize
  - `figsize_to_pixels()` - Convierte pulgadas a píxeles
  - `process_figsize_in_kwargs()` - Procesa figsize en kwargs

## 🚧 Módulos Pendientes

### Layouts Module (`layouts/`)
- ⏳ **matrix.py**: Refactorizar `MatrixLayout` para usar nuevos módulos
  - Integrar `EventManager`, `CommManager`
  - Usar `ChartRegistry` y `ChartBase`
  - Usar preparadores de `data/`
  
- ⏳ **reactive.py**: Refactorizar `ReactiveMatrixLayout`
  - Integrar con nuevo sistema reactivo

### Reactive Module (`reactive/`)
- ⏳ **engine.py**: `ReactiveEngine` unificado
  - Estado centralizado
  - Flujo unidireccional de datos
  
- ⏳ **selection.py**: `SelectionModel` desacoplado
  
- ⏳ **linking.py**: `LinkManager` para vistas enlazadas
  
- ⏳ **engines/**: Engines de comunicación multiplataforma
  - `jupyter.py` - Jupyter Comm
  - `colab.py` - Google Colab API
  - `js_only.py` - Fallback JS-only

### Render Module (`render/`)
- ⏳ **html.py**: HTML generator
  - Generación de HTML con contenedores y estilos
  
- ⏳ **builder.py**: JS builder
  - Construcción de código JS a partir de specs
  - Integración con templates
  
- ⏳ **templates/**: Plantillas JS modulares
  - Separar JS inline en templates reutilizables
  
- ⏳ **assets.py**: Gestión de assets
  - Carga de JS/CSS
  - Caching

## ✅ Estado Actual de la Implementación

### Módulos Completados (Fase 1)

1. **Core Module** ✅
   - Sistema de excepciones completo
   - Registry global funcional
   - CommManager implementado
   - EventManager con múltiples handlers
   - LayoutEngine básico

2. **Data Module** ✅
   - Preparadores para 8 tipos de gráficos
   - Validadores completos
   - Transformadores DataFrame ↔ dicts
   - Agregadores (group_by, bin, stats)

3. **Charts Module** ✅
   - ChartBase (clase abstracta)
   - ChartRegistry funcional
   - 8 gráficos completamente implementados
   - 4 gráficos placeholder (estructura lista)

4. **Utils Module** ✅
   - Sanitización JSON
   - Conversión figsize

5. **Compat Module** ✅
   - Wrappers para métodos map_*
   - DeprecationWarnings implementados

6. **__init__.py Principal** ✅
   - Nueva API modular expuesta
   - Compatibilidad hacia atrás mantenida
   - Auto-registro de Comm

### Módulos Pendientes (Fase 2)

1. **Layouts Module** ⏳
   - Refactorizar MatrixLayout para usar nuevos módulos
   - Integrar EventManager, CommManager
   - Usar ChartRegistry

2. **Reactive Module** ⏳
   - ReactiveEngine unificado
   - SelectionModel desacoplado
   - LinkManager para vistas enlazadas
   - Engines de comunicación multiplataforma

3. **Render Module** ⏳
   - HTML generator
   - JS builder modular
   - Templates JS separados
   - Gestión de assets

## 📐 Principios de Diseño

### 1. Separación de Responsabilidades
- **Core**: Infraestructura base (comm, events, registry)
- **Data**: Procesamiento de datos (validación, transformación, preparación)
- **Charts**: Lógica de gráficos (specs, validación)
- **Layouts**: Gestión de layouts y disposición
- **Reactive**: Estado y reactividad
- **Render**: Generación de HTML/JS
- **Utils**: Utilidades reutilizables

### 2. Extensibilidad
- Nuevos gráficos: Heredar de `ChartBase` y registrar en `ChartRegistry`
- Nuevos layouts: Implementar interfaz de layout
- Nuevos preparadores: Agregar a `data/preparators.py`

### 3. Compatibilidad hacia atrás
- Wrappers para API antigua (`map_scatter`, `map_barchart`, etc.)
- Migración gradual sin romper código existente

### 4. BESTLIB Visualization Spec
- Contrato universal para definición de gráficos
- Estructura: `{type, data, encoding, options, interaction}`
- Todos los gráficos implementan este spec

## 🔄 Flujo de Datos

```
Usuario → Chart.get_spec()
    ↓
Data Validators (validar estructura)
    ↓
Data Preparators (preparar datos)
    ↓
Chart Spec (BESTLIB Visualization Spec)
    ↓
Render Builder (generar HTML/JS)
    ↓
Comm Manager (eventos JS ↔ Python)
    ↓
Event Manager (routing de eventos)
```

## 📝 Notas de Implementación

### Patrones Utilizados
- **Registry Pattern**: Para descubrimiento dinámico de componentes
- **Factory Pattern**: Para creación de gráficos
- **Observer Pattern**: Para sistema de eventos
- **Strategy Pattern**: Para engines de comunicación
- **Template Method**: En `ChartBase`

### Dependencias Mínimas
- `pandas`: Opcional (se detecta automáticamente)
- `ipywidgets`: Opcional (solo para Comm)
- D3.js: Incluido en el paquete

### Compatibilidad Multiplataforma
- Jupyter Notebook: ✅ Comm targets
- JupyterLab: ✅ Comm targets
- Google Colab: ⏳ Colab API (pendiente)
- Deepnote: ⏳ Detección automática (pendiente)
- JS-only: ⏳ Fallback (pendiente)

## 🎯 Próximos Pasos (Actualizado)

### Fase 1 - Completada ✅
- ✅ Estructura de directorios modular
- ✅ Core module completo
- ✅ Data module completo
- ✅ Charts module completo (8 gráficos)
- ✅ Utils module completo
- ✅ Wrappers de compatibilidad
- ✅ __init__.py principal actualizado

### Fase 2 - En Progreso ⏳
1. **Refactorizar MatrixLayout** para usar nuevos módulos
   - Integrar EventManager en lugar de _handlers
   - Usar CommManager en lugar de _ensure_comm_target
   - Usar ChartRegistry para obtener gráficos
   - Usar preparadores de data/ en lugar de _prepare_data

2. **Migrar sistema reactivo** al nuevo `reactive/`
   - Extraer ReactiveEngine de reactive.py
   - Desacoplar SelectionModel
   - Crear LinkManager

3. **Crear sistema de renderizado modular** en `render/`
   - Extraer generación de HTML
   - Separar JS en templates
   - Crear JS builder

4. **Implementar engines de comunicación** para Colab/Deepnote
   - JupyterCommEngine (✅ ya existe como CommManager)
   - ColabEngine con google.colab API
   - JSOnlyFallback para entornos sin Comm

5. **Modularizar matrix.js** en templates separados
   - Separar renderizadores por tipo de gráfico
   - Templates reutilizables

### Fase 3 - Pendiente 📋
6. **Tests unitarios** para cada módulo
7. **Documentación** de API pública
8. **Ejemplos** de uso de nueva API modular
9. **Migración gradual** de código legacy

## 📝 Uso de la Nueva API Modular

### Ejemplo 1: Usar Chart Registry Directamente

```python
from BESTLIB import ChartRegistry

# Obtener scatter chart
scatter = ChartRegistry.get('scatter')

# Generar spec
spec = scatter.get_spec(
    data=df,
    x_col='age',
    y_col='income',
    category_col='department',
    interactive=True
)

# Usar spec en layout
from BESTLIB import MatrixLayout
layout = MatrixLayout("S")
layout.map("S", spec)
layout.display()
```

### Ejemplo 2: Usar Preparadores de Datos

```python
from BESTLIB.data import prepare_scatter_data, validate_scatter_data

# Validar datos
validate_scatter_data(df, x_col='age', y_col='income')

# Preparar datos
processed, original = prepare_scatter_data(
    df,
    x_col='age',
    y_col='income',
    category_col='department'
)
```

### Ejemplo 3: Compatibilidad hacia atrás

```python
from BESTLIB import MatrixLayout

# API antigua sigue funcionando (con warnings)
MatrixLayout.map_scatter('S', df, x_col='age', y_col='income')
layout = MatrixLayout("S")
layout.display()
```

## 📚 Referencias

- `BESTLIB_modularization_proposal.md`: Propuesta original de modularización
- `BESTLIB_architecture_complete_v2.md`: Documento maestro de arquitectura (pendiente de generar)

---

**Última actualización**: Fase 2 Completada
**Versión**: 0.2.0-modular

## 🎉 Fase 2 Completada - Refactorización de Módulos Legacy

### ✅ Nuevos Módulos Creados

1. **Reactive Module** (`reactive/`) ✅
   - `selection.py`: ReactiveData y SelectionModel extraídos
   - `engine.py`: ReactiveEngine para estado centralizado
   - `linking.py`: LinkManager para vistas enlazadas
   - `engines/`: Engines de comunicación multiplataforma
     - `jupyter.py`: JupyterCommEngine
     - `colab.py`: ColabEngine
     - `js_only.py`: JSOnlyFallback
   
2. **Render Module** (`render/`) ✅
   - `html.py`: HTMLGenerator para generación de HTML
   - `builder.py`: JSBuilder para construcción de JavaScript
   - `assets.py`: AssetManager para gestión de assets (JS/CSS)

3. **Layouts Module** (`layouts/`) ✅
   - `matrix.py`: MatrixLayout refactorizado usando nuevos módulos
     - Usa EventManager en lugar de _handlers
     - Usa CommManager en lugar de _ensure_comm_target
     - Usa LayoutEngine para parsing
     - Usa Render module para HTML/JS
     - Usa AssetManager para assets

### 🔄 Integración con Módulos Existentes

- **MatrixLayout refactorizado** ahora usa:
  - `EventManager` para gestión de eventos
  - `CommManager` para comunicación
  - `LayoutEngine` para parsing de layouts
  - `AssetManager` para carga de assets
  - `HTMLGenerator` y `JSBuilder` para renderizado
  - `ChartRegistry` para gráficos

- **__init__.py actualizado** para exponer:
  - Nuevos módulos reactive (ReactiveData, ReactiveEngine, LinkManager)
  - Nuevos módulos render (HTMLGenerator, JSBuilder, AssetManager)
  - MatrizLayout refactorizado (con fallback a legacy)

### 📝 Estado Final

- ✅ **Fase 1**: Core, Data, Charts, Utils, Compat
- ✅ **Fase 2**: Reactive, Render, Layouts refactorizados
- ⏳ **Fase 3**: Tests, documentación, ejemplos (pendiente)

### 🎯 Próximos Pasos

1. Tests unitarios para módulos nuevos
2. Migración completa de ReactiveMatrixLayout
3. Documentación de API pública actualizada
4. Ejemplos usando nueva API modular
5. Optimización de performance

