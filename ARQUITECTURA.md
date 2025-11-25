# 🏗️ Arquitectura de BESTLIB

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Componentes Principales](#componentes-principales)
4. [Flujo de Datos](#flujo-de-datos)
5. [Patrones de Diseño](#patrones-de-diseño)
6. [Sistema de Comunicación](#sistema-de-comunicación)
7. [Sistema de Renderizado](#sistema-de-renderizado)
8. [Sistema Reactivo](#sistema-reactivo)
9. [Extensibilidad](#extensibilidad)
10. [Diagramas de Flujo](#diagramas-de-flujo)

---

## 🎯 Visión General

**BESTLIB** es una librería de visualización interactiva para Jupyter Notebooks que combina:

- **Python** (backend): Preparación de datos, lógica de negocio, gestión de estado
- **D3.js** (frontend): Renderizado de gráficos interactivos en el navegador
- **Jupyter Comm Protocol**: Comunicación bidireccional Python ↔ JavaScript

### Principios de Diseño

1. **Modularidad**: Cada componente tiene una responsabilidad única
2. **Extensibilidad**: Fácil agregar nuevos tipos de gráficos
3. **Compatibilidad**: Soporte para Jupyter Notebook, JupyterLab, Google Colab
4. **Reactividad**: Actualización automática sin re-ejecutar celdas
5. **Separación de Concerns**: Backend (Python) y Frontend (JavaScript) claramente separados

---

## 📁 Estructura del Proyecto

```
BESTLIB/
├── __init__.py                 # Punto de entrada principal, imports con fallbacks
├── matrix.py                   # MatrixLayout legacy (compatibilidad)
├── reactive.py                 # ReactiveMatrixLayout legacy (compatibilidad)
├── linked.py                   # LinkedViews (compatibilidad)
├── matrix.js                   # Frontend JavaScript (D3.js rendering)
├── d3.min.js                   # D3.js library (minified)
├── style.css                   # Estilos CSS unificados
│
├── charts/                     # Sistema de gráficos modular
│   ├── __init__.py             # Registro automático de charts
│   ├── base.py                 # ChartBase (clase abstracta)
│   ├── registry.py             # ChartRegistry (patrón Registry)
│   ├── scatter.py              # ScatterChart
│   ├── bar.py                  # BarChart
│   ├── histogram.py            # HistogramChart
│   ├── boxplot.py              # BoxplotChart
│   ├── heatmap.py              # HeatmapChart
│   ├── line.py                 # LineChart
│   ├── pie.py                  # PieChart
│   ├── violin.py               # ViolinChart
│   ├── radviz.py               # RadvizChart
│   ├── star_coordinates.py     # StarCoordinatesChart
│   ├── parallel_coordinates.py  # ParallelCoordinatesChart
│   ├── grouped_bar.py          # GroupedBarChart
│   ├── line_plot.py            # LinePlotChart
│   ├── horizontal_bar.py       # HorizontalBarChart
│   ├── hexbin.py               # HexbinChart
│   ├── errorbars.py             # ErrorbarsChart
│   ├── fill_between.py         # FillBetweenChart
│   ├── step_plot.py            # StepPlotChart
│   ├── kde.py                  # KdeChart
│   ├── distplot.py             # DistplotChart
│   ├── rug.py                  # RugChart
│   ├── qqplot.py               # QqplotChart
│   ├── ecdf.py                 # EcdfChart
│   ├── ridgeline.py            # RidgelineChart
│   ├── ribbon.py               # RibbonChart
│   ├── hist2d.py               # Hist2dChart
│   ├── polar.py                # PolarChart
│   └── funnel.py               # FunnelChart
│
├── core/                       # Componentes centrales
│   ├── __init__.py
│   ├── comm.py                 # CommManager (comunicación JS ↔ Python)
│   ├── events.py               # EventManager (gestión de eventos)
│   ├── exceptions.py           # Excepciones personalizadas
│   ├── layout.py               # LayoutEngine (parsing ASCII layouts)
│   └── registry.py             # Registry genérico (no usado actualmente)
│
├── data/                       # Procesamiento de datos
│   ├── __init__.py
│   ├── validators.py           # Validación de datos
│   ├── preparators.py          # Preparación de datos para gráficos
│   ├── transformers.py         # Transformaciones de datos
│   └── aggregators.py          # Agregaciones de datos
│
├── layouts/                    # Layouts (versión modular)
│   ├── __init__.py
│   ├── matrix.py               # MatrixLayout (versión modular)
│   └── reactive.py             # ReactiveMatrixLayout (versión modular)
│
├── reactive/                    # Sistema reactivo modular
│   ├── __init__.py
│   ├── selection.py            # SelectionModel, ReactiveData
│   ├── engine.py               # ReactiveEngine
│   ├── linking.py              # LinkManager
│   └── engines/                 # Engines específicos por entorno
│       ├── base.py             # BaseEngine
│       ├── jupyter.py          # JupyterEngine
│       ├── colab.py            # ColabEngine
│       └── js_only.py          # JSOnlyEngine
│
├── render/                      # Sistema de renderizado
│   ├── __init__.py
│   ├── assets.py               # AssetManager (carga de JS/CSS)
│   ├── builder.py              # JSBuilder (construcción de JS)
│   └── html.py                 # HTMLGenerator (generación de HTML)
│
├── utils/                       # Utilidades
│   ├── __init__.py
│   ├── figsize.py              # Conversión de figsize
│   └── json.py                 # Sanitización JSON
│
├── compat/                      # Compatibilidad hacia atrás
│   ├── __init__.py
│   ├── chart_wrappers.py       # Wrappers para charts legacy
│   └── matrix_wrapper.py       # Wrapper para MatrixLayout legacy
│
└── themes/                      # Temas visuales (futuro)
```

---

## 🧩 Componentes Principales

### 1. Layouts

#### `MatrixLayout` (`layouts/matrix.py`)
**Responsabilidad**: Layout estático con gráficos independientes.

**Características**:
- Parsing de layouts ASCII
- Gestión de specs de gráficos (`_map`)
- Generación de HTML/JS para renderizado
- Sistema de eventos básico

**API Principal**:
```python
MatrixLayout.map_scatter(letter, data, x_col, y_col, **kwargs)
MatrixLayout.map_barchart(letter, data, category_col, value_col, **kwargs)
MatrixLayout.map_histogram(letter, data, value_col, bins, **kwargs)
# ... otros map_* methods
```

#### `ReactiveMatrixLayout` (`layouts/reactive.py`)
**Responsabilidad**: Layout reactivo con vistas enlazadas y actualización automática.

**Características**:
- Hereda de `MatrixLayout` (composición)
- Sistema de selección reactiva (`SelectionModel`)
- Vistas enlazadas (`linked_to`)
- Actualización automática de gráficos dependientes

**API Principal**:
```python
layout = ReactiveMatrixLayout("AS\nHX", selection_model=SelectionModel())
layout.set_data(df)
layout.add_scatter('A', x_col='x', y_col='y', interactive=True)
layout.add_histogram('H', column='x', linked_to='A')
layout.add_boxplot('X', column='y', linked_to='A')
layout.display()
```

### 2. Sistema de Gráficos

#### `ChartBase` (`charts/base.py`)
**Responsabilidad**: Clase base abstracta para todos los gráficos.

**Contrato**:
```python
class ChartBase(ABC):
    @property
    @abstractmethod
    def chart_type(self) -> str
    
    @abstractmethod
    def validate_data(self, data, **kwargs)
    
    @abstractmethod
    def prepare_data(self, data, **kwargs)
    
    @abstractmethod
    def get_spec(self, data, **kwargs) -> dict
```

**Flujo**:
1. `validate_data()`: Valida que los datos sean adecuados
2. `prepare_data()`: Transforma datos a formato estándar
3. `get_spec()`: Genera spec JSON para JavaScript

#### `ChartRegistry` (`charts/registry.py`)
**Responsabilidad**: Registro centralizado de tipos de gráficos (patrón Registry).

**Uso**:
```python
ChartRegistry.register(ScatterChart)
chart = ChartRegistry.get('scatter')
spec = chart.get_spec(data, x_col='x', y_col='y')
```

**Ventajas**:
- Extensibilidad: Agregar nuevos gráficos sin modificar código existente
- Desacoplamiento: Los layouts no conocen implementaciones específicas
- Centralización: Un solo punto de registro

### 3. Procesamiento de Datos

#### `validators.py`
**Responsabilidad**: Validación de estructura y tipos de datos.

**Funciones principales**:
- `validate_scatter_data()`: Valida datos para scatter plots
- `validate_bar_data()`: Valida datos para bar charts
- `validate_data_structure()`: Validación genérica

#### `preparators.py`
**Responsabilidad**: Transformación de datos a formato estándar para gráficos.

**Funciones principales**:
- `prepare_scatter_data()`: Prepara datos para scatter plots
- `prepare_bar_data()`: Prepara datos para bar charts
- `prepare_histogram_data()`: Prepara datos para histogramas
- `prepare_boxplot_data()`: Prepara datos para boxplots

**Formato estándar**:
- Lista de diccionarios con campos estándar (`x`, `y`, `category`, `value`)
- Incluye `_original_row` y `_original_index` para trazabilidad

#### `transformers.py` y `aggregators.py`
**Responsabilidad**: Transformaciones y agregaciones avanzadas de datos.

### 4. Sistema de Comunicación

#### `CommManager` (`core/comm.py`)
**Responsabilidad**: Gestión de comunicación bidireccional JavaScript ↔ Python.

**Características**:
- Registro de Comm targets de Jupyter
- Routing de mensajes a instancias correctas
- Gestión de weak references para evitar memory leaks
- Soporte para Jupyter Notebook, JupyterLab, Google Colab

**Flujo**:
1. JavaScript envía evento: `sendEvent(divId, 'select', payload)`
2. `CommManager` recibe mensaje vía Comm protocol
3. `CommManager` busca instancia por `div_id`
4. `EventManager` de la instancia procesa el evento
5. Handlers registrados se ejecutan

#### `EventManager` (`core/events.py`)
**Responsabilidad**: Gestión de eventos y handlers.

**Características**:
- Registro de handlers por tipo de evento
- Handlers globales y por instancia
- Sistema de prioridades

### 5. Sistema de Renderizado

#### `HTMLGenerator` (`render/html.py`)
**Responsabilidad**: Generación de HTML completo con assets embebidos.

**Características**:
- Carga automática de D3.js desde CDN
- Inyección de CSS (`style.css`)
- Wrapper seguro para prevenir XSS

#### `JSBuilder` (`render/builder.py`)
**Responsabilidad**: Construcción de código JavaScript.

**Características**:
- Generación de llamadas a `render()`
- Sanitización de datos para JSON
- Soporte para esperar D3.js (Colab)

#### `AssetManager` (`render/assets.py`)
**Responsabilidad**: Gestión de assets (JS/CSS) en diferentes entornos.

**Características**:
- Detección automática de entorno (Colab, Jupyter, etc.)
- Carga condicional de assets
- Prevención de carga duplicada

### 6. Sistema Reactivo

#### `SelectionModel` (`reactive/selection.py`)
**Responsabilidad**: Modelo de selección reactiva.

**Características**:
- Almacena items seleccionados
- Sistema de callbacks (`on_change()`)
- Sincronización con variables Python

#### `ReactiveData` (`reactive/selection.py`)
**Responsabilidad**: Widget reactivo para sincronización de datos.

**Características**:
- Traits sincronizados con JavaScript
- Observadores automáticos
- Compatible con `ipywidgets`

#### `ReactiveEngine` (`reactive/engine.py`)
**Responsabilidad**: Motor reactivo que coordina actualizaciones.

**Características**:
- Engines específicos por entorno
- Gestión de ciclo de vida
- Optimización de actualizaciones

#### `LinkManager` (`reactive/linking.py`)
**Responsabilidad**: Gestión de enlaces entre vistas.

**Características**:
- Registro de dependencias
- Propagación de actualizaciones
- Prevención de bucles infinitos

---

## 🔄 Flujo de Datos

### Flujo de Renderizado Inicial

```
Usuario crea layout
    ↓
MatrixLayout.__init__()
    ↓
Usuario llama map_*() o add_*()
    ↓
ChartRegistry.get(chart_type)
    ↓
chart.validate_data()
    ↓
chart.prepare_data()
    ↓
chart.get_spec()
    ↓
Spec guardado en MatrixLayout._map[letter]
    ↓
Usuario llama display() o _repr_html_()
    ↓
_prepare_repr_data()
    ↓
HTMLGenerator.generate_full_html()
    ↓
JSBuilder.build_full_js()
    ↓
HTML + JS inyectado en Jupyter
    ↓
JavaScript ejecuta render()
    ↓
matrix.js renderiza gráficos con D3.js
```

### Flujo de Interacción (Reactivo)

```
Usuario hace brush/click en gráfico
    ↓
JavaScript detecta evento
    ↓
sendEvent(divId, 'select', payload)
    ↓
CommManager recibe mensaje
    ↓
EventManager procesa evento
    ↓
Handler registrado ejecuta
    ↓
SelectionModel.update(items)
    ↓
Callbacks registrados se ejecutan
    ↓
update_histogram(), update_boxplot(), etc.
    ↓
JavaScript actualiza gráficos dependientes
```

### Flujo de Vistas Enlazadas

```
ReactiveMatrixLayout.add_scatter('A', ...)
    ↓
SelectionModel creado para 'A'
    ↓
ReactiveMatrixLayout.add_histogram('H', linked_to='A')
    ↓
Link registrado: 'H' → 'A'
    ↓
Callback update_histogram() registrado en SelectionModel de 'A'
    ↓
Usuario hace brush en 'A'
    ↓
SelectionModel de 'A' actualizado
    ↓
update_histogram() ejecutado
    ↓
Datos filtrados calculados
    ↓
JavaScript actualiza gráfico 'H'
```

---

## 🎨 Patrones de Diseño

### 1. Registry Pattern
**Implementación**: `ChartRegistry`

**Propósito**: Permitir registro dinámico de tipos de gráficos sin modificar código existente.

**Ventajas**:
- Extensibilidad
- Desacoplamiento
- Centralización

### 2. Template Method Pattern
**Implementación**: `ChartBase` → Charts específicos

**Propósito**: Definir esqueleto del algoritmo (validate → prepare → get_spec) y dejar que subclases implementen pasos específicos.

### 3. Strategy Pattern
**Implementación**: `ReactiveEngine` con engines específicos (`JupyterEngine`, `ColabEngine`, etc.)

**Propósito**: Intercambiar algoritmos de renderizado según el entorno.

### 4. Observer Pattern
**Implementación**: `SelectionModel.on_change()`, `EventManager`

**Propósito**: Notificar cambios de selección a gráficos dependientes.

### 5. Factory Pattern
**Implementación**: `ChartRegistry.get()` crea instancias de charts

**Propósito**: Crear objetos sin especificar la clase exacta.

### 6. Facade Pattern
**Implementación**: `MatrixLayout` y `ReactiveMatrixLayout` como fachadas

**Propósito**: Simplificar la API compleja del sistema interno.

### 7. Composition Pattern
**Implementación**: `ReactiveMatrixLayout` contiene `MatrixLayout`

**Propósito**: Reutilizar funcionalidad de `MatrixLayout` y agregar reactividad.

---

## 📡 Sistema de Comunicación

### Arquitectura de Comunicación

```
┌─────────────┐                    ┌─────────────┐
│   Python    │                    │ JavaScript  │
│  Backend    │                    │  Frontend   │
└─────────────┘                    └─────────────┘
       │                                   │
       │                                   │
       ▼                                   ▼
┌─────────────┐                    ┌─────────────┐
│ CommManager │◄─── Jupyter Comm ──►│  sendEvent │
│             │      Protocol        │             │
└─────────────┘                    └─────────────┘
       │                                   │
       ▼                                   │
┌─────────────┐                           │
│EventManager │                           │
└─────────────┘                           │
       │                                   │
       ▼                                   │
┌─────────────┐                           │
│  Handlers   │                           │
└─────────────┘                           │
       │                                   │
       └───────────◄──────────────────────┘
              (actualización de gráficos)
```

### Tipos de Eventos

1. **`select`**: Selección de items (click, brush)
2. **`brush`**: Selección por área (brush rectangle)
3. **`point_click`**: Click en punto específico
4. **`hover`**: Hover sobre elemento (futuro)

### Payload de Eventos

```python
{
    'type': 'select',
    'items': [...],              # Items seleccionados
    '__view_letter__': 'A',      # Letra de la vista
    '__is_primary_view__': True,  # Si es vista principal
    'indices': [...],            # Índices seleccionados
    '_original_rows': [...]      # Filas originales del DataFrame
}
```

---

## 🎨 Sistema de Renderizado

### Pipeline de Renderizado

```
1. Preparación de Specs
   └─> Chart.get_spec() genera dict con:
       - type: 'scatter', 'bar', etc.
       - data: [...]
       - options: {color, axes, xLabel, yLabel, ...}

2. Serialización
   └─> JSON sanitization (numpy types → Python types)

3. Generación de HTML
   └─> HTMLGenerator.generate_full_html()
       - Wrapper seguro
       - Carga de D3.js desde CDN
       - Inyección de CSS

4. Generación de JavaScript
   └─> JSBuilder.build_full_js()
       - Llamada a render(divId, layout, mapping)
       - Espera de D3.js (si es necesario)

5. Inyección en Jupyter
   └─> IPython.display.HTML() + Javascript()

6. Renderizado en Navegador
   └─> matrix.js ejecuta render()
       - Parsing de layout ASCII
       - Creación de grid CSS
       - Renderizado de cada celda con D3.js
```

### Renderers JavaScript

Cada tipo de gráfico tiene su función renderer en `matrix.js`:

- `renderScatterPlotD3()`: Scatter plots con brush
- `renderBarChartD3()`: Bar charts interactivos
- `renderHistogramD3()`: Histogramas con bins
- `renderBoxplotD3()`: Boxplots con cuantiles
- `renderHeatmapD3()`: Heatmaps con colores
- `renderLineD3()`: Line charts multi-serie
- `renderPieD3()`: Pie charts interactivos
- ... y 21 más

**Estructura común**:
```javascript
function renderChartD3(container, spec, d3, divId) {
    // 1. Validar datos
    const data = spec.data || [];
    if (data.length === 0) return;
    
    // 2. Calcular dimensiones
    const dims = getChartDimensions(container, spec, 400, 350);
    
    // 3. Crear SVG
    const svg = d3.select(container).append('svg')...;
    
    // 4. Crear escalas
    const x = d3.scaleLinear()...;
    const y = d3.scaleLinear()...;
    
    // 5. Renderizar elementos
    svg.selectAll('.element').data(data).enter()...;
    
    // 6. Renderizar ejes
    renderXAxis(...);
    renderYAxis(...);
    
    // 7. Agregar interactividad
    if (spec.interactive) {
        // Event listeners
    }
}
```

---

## ⚡ Sistema Reactivo

### Componentes del Sistema Reactivo

```
ReactiveMatrixLayout
    ├── SelectionModel (principal)
    ├── _scatter_selection_models {letter: SelectionModel}
    ├── _primary_view_models {letter: SelectionModel}
    ├── _view_links {master: [dependents]}
    └── _barchart_callbacks {letter: callback}
```

### Flujo de Actualización Reactiva

```
1. Usuario hace selección en vista principal 'A'
   ↓
2. JavaScript envía evento 'select' con items
   ↓
3. Handler de 'A' actualiza SelectionModel de 'A'
   ↓
4. SelectionModel dispara callbacks registrados
   ↓
5. update_histogram('H') ejecutado
   ↓
6. Datos filtrados calculados desde items
   ↓
7. JavaScript actualiza gráfico 'H' con nuevos datos
   ↓
8. Gráfico 'H' se re-renderiza automáticamente
```

### Prevención de Bucles Infinitos

- **Flags de actualización**: `_bestlib_updating_{letter}`
- **Verificación de cambios**: Hash de datos antes de actualizar
- **Delays**: `setTimeout()` para evitar actualizaciones inmediatas
- **Locks**: Flags de ejecución en callbacks

---

## 🔧 Extensibilidad

### Agregar un Nuevo Tipo de Gráfico

#### 1. Crear clase de Chart

```python
# BESTLIB/charts/mi_grafico.py
from .base import ChartBase
from ..core.exceptions import ChartError

class MiGraficoChart(ChartBase):
    @property
    def chart_type(self):
        return 'mi_grafico'
    
    def validate_data(self, data, **kwargs):
        # Validar datos
        pass
    
    def prepare_data(self, data, **kwargs):
        # Preparar datos
        return prepared_data
    
    def get_spec(self, data, **kwargs):
        self.validate_data(data, **kwargs)
        prepared = self.prepare_data(data, **kwargs)
        return {
            'type': self.chart_type,
            'data': prepared,
            **kwargs
        }
```

#### 2. Registrar en `__init__.py`

```python
# BESTLIB/charts/__init__.py
try:
    from .mi_grafico import MiGraficoChart
except (ImportError, AttributeError, Exception):
    pass

if MiGraficoChart is not None:
    ChartRegistry.register(MiGraficoChart)
```

#### 3. Agregar método `map_*` en `MatrixLayout`

```python
# BESTLIB/layouts/matrix.py
@classmethod
def map_mi_grafico(cls, letter, data, **kwargs):
    from ..charts import ChartRegistry
    chart = ChartRegistry.get('mi_grafico')
    spec = chart.get_spec(data, **kwargs)
    if not hasattr(cls, '_map') or cls._map is None:
        cls._map = {}
    cls._map[letter] = spec
    return spec
```

#### 4. Agregar renderer JavaScript

```javascript
// BESTLIB/matrix.js
function renderMiGraficoD3(container, spec, d3, divId) {
    const data = spec.data || [];
    // ... lógica de renderizado con D3.js
}

// En la función render(), agregar:
case 'mi_grafico':
    renderMiGraficoD3(container, spec, d3, divId);
    break;
```

#### 5. Agregar método `add_*` en `ReactiveMatrixLayout` (opcional)

```python
# BESTLIB/layouts/reactive.py
def add_mi_grafico(self, letter, linked_to=None, **kwargs):
    # Lógica similar a add_histogram o add_boxplot
    pass
```

---

## 📊 Diagramas de Flujo

### Diagrama de Clases (Simplificado)

```
┌─────────────────────┐
│    ChartBase        │ (Abstract)
│  (ABC)              │
├─────────────────────┤
│ + chart_type        │
│ + validate_data()   │
│ + prepare_data()    │
│ + get_spec()        │
└─────────────────────┘
         ▲
         │
    ┌────┴─────┬──────────┬──────────┐
    │          │          │          │
┌─────────┐ ┌──────┐ ┌─────────┐ ┌──────┐
│Scatter  │ │Bar   │ │Histogram│ │...   │
│Chart    │ │Chart │ │Chart    │ │      │
└─────────┘ └──────┘ └─────────┘ └──────┘
    │          │          │          │
    └──────────┴──────────┴──────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  ChartRegistry   │
         ├─────────────────┤
         │ + register()    │
         │ + get()         │
         └─────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  MatrixLayout   │
         ├─────────────────┤
         │ + map_*()       │
         │ + display()     │
         └─────────────────┘
                  ▲
                  │
         ┌─────────────────┐
         │ReactiveMatrix   │
         │Layout           │
         ├─────────────────┤
         │ + add_*()       │
         │ + set_data()    │
         └─────────────────┘
```

### Diagrama de Secuencia (Renderizado)

```
Usuario    MatrixLayout    ChartRegistry    Chart        JavaScript
   │            │                │            │              │
   │──map_scatter()──────────────>│            │              │
   │            │                │            │              │
   │            │──get('scatter')─>│            │              │
   │            │                │            │              │
   │            │                │──get_spec()─>│              │
   │            │                │            │              │
   │            │                │<──spec──────│              │
   │            │                │            │              │
   │            │<──spec─────────│            │              │
   │            │                │            │              │
   │            │──display()─────>│            │              │
   │            │                │            │              │
   │            │──_prepare_repr_data()       │              │
   │            │                │            │              │
   │            │──generate_html()            │              │
   │            │                │            │              │
   │            │──build_js()                 │              │
   │            │                │            │              │
   │<──HTML+JS──│                │            │              │
   │            │                │            │              │
   │            │                │            │──render()────>│
   │            │                │            │              │
   │            │                │            │──renderScatterD3()
   │            │                │            │              │
   │<──Gráfico renderizado─────────────────────────────────────│
```

### Diagrama de Secuencia (Interacción Reactiva)

```
Usuario    JavaScript    CommManager    EventManager    SelectionModel    Callback
   │            │              │              │                │              │
   │──brush─────>│              │              │                │              │
   │            │              │              │                │              │
   │            │──sendEvent()─>│              │                │              │
   │            │              │              │                │              │
   │            │              │──handle_message()            │              │
   │            │              │              │                │              │
   │            │              │──process_event()              │              │
   │            │              │              │                │              │
   │            │              │              │──update(items)─>│              │
   │            │              │              │                │              │
   │            │              │              │                │──on_change()─>│
   │            │              │              │                │              │
   │            │              │              │                │              │──update_histogram()
   │            │              │              │                │              │
   │            │              │              │                │              │──JavaScript update
   │            │              │              │                │              │
   │            │<──update─────│              │                │              │
   │            │              │              │                │              │
   │<──Gráfico actualizado─────────────────────────────────────────────────────│
```

---

## 🔐 Seguridad y Robustez

### Sanitización de Datos

- **JSON Sanitization**: Conversión de tipos NumPy a tipos Python nativos
- **HTML Escaping**: Prevención de XSS en contenido HTML
- **Safe HTML Mode**: Modo seguro por defecto

### Manejo de Errores

- **Excepciones personalizadas**: `ChartError`, `DataError`, `CommunicationError`
- **Fallbacks**: Múltiples estrategias de importación
- **Validación defensiva**: Verificación de datos antes de procesamiento

### Compatibilidad

- **Múltiples entornos**: Jupyter Notebook, JupyterLab, Google Colab
- **Fallbacks**: Versión legacy disponible si módulos modulares fallan
- **Detección automática**: Detección de entorno y ajuste automático

---

## 📈 Rendimiento

### Optimizaciones

1. **Caché de Assets**: JS y CSS cargados una sola vez
2. **Weak References**: Prevención de memory leaks
3. **Lazy Loading**: Importación bajo demanda
4. **Operaciones Vectorizadas**: Uso de pandas/numpy en lugar de loops
5. **Update Patterns**: Actualización incremental en lugar de re-renderizado completo

### Limitaciones Conocidas

- **Grandes Datasets**: Puede ser lento con >10,000 puntos
- **Múltiples Layouts**: Cada layout crea su propio contexto
- **Actualizaciones Simultáneas**: Puede causar race conditions (mitigado con flags)

---

## 🚀 Futuras Mejoras

1. **Web Workers**: Procesamiento de datos en background
2. **Virtual Scrolling**: Renderizado eficiente de grandes datasets
3. **Temas Personalizables**: Sistema de temas más robusto
4. **Exportación**: Exportar gráficos como PNG/SVG
5. **Animaciones**: Transiciones más fluidas
6. **Testing**: Suite de tests automatizados

---

## 📚 Referencias

- **D3.js**: https://d3js.org/
- **Jupyter Comm Protocol**: https://jupyter-client.readthedocs.io/
- **IPython Widgets**: https://ipywidgets.readthedocs.io/
- **Pandas**: https://pandas.pydata.org/

---

**Última actualización**: 2025-01-XX
**Versión**: 2.0 (Modular)

