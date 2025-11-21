# 📊 Análisis Completo del Proyecto BESTLIB

## 🎯 Resumen Ejecutivo

**BESTLIB** es una librería de visualización interactiva para Jupyter Notebooks que permite crear dashboards con layouts ASCII y gráficos D3.js. El proyecto está diseñado con una arquitectura modular que soporta múltiples tipos de gráficos, vistas enlazadas, sistema reactivo y comunicación bidireccional entre Python y JavaScript.

---

## 🏗️ Arquitectura General

### Estructura de Directorios

```
BESTLIB/
├── __init__.py              # Punto de entrada principal con importaciones dinámicas
├── matrix.py                 # Implementación legacy de MatrixLayout (2480 líneas)
├── matrix.js                 # Código JavaScript para renderizado D3.js
├── style.css                 # Estilos CSS para layouts
├── linked.py                 # Sistema de vistas enlazadas (LinkedViews)
├── reactive.py               # Sistema reactivo legacy
│
├── charts/                   # Sistema modular de gráficos
│   ├── base.py               # Clase base abstracta ChartBase
│   ├── registry.py           # ChartRegistry para registro dinámico
│   ├── scatter.py            # Scatter plot
│   ├── bar.py                # Bar chart
│   ├── histogram.py          # Histogram
│   ├── boxplot.py            # Box plot
│   ├── heatmap.py            # Heatmap
│   ├── line.py               # Line chart
│   ├── pie.py                # Pie chart
│   ├── violin.py             # Violin plot
│   ├── radviz.py             # Radviz
│   ├── star_coordinates.py   # Star coordinates
│   ├── parallel_coordinates.py # Parallel coordinates
│   ├── grouped_bar.py        # Grouped bar chart
│   ├── line_plot.py          # Line plot (nuevo)
│   ├── horizontal_bar.py    # Horizontal bar (nuevo)
│   ├── hexbin.py             # Hexbin (nuevo)
│   ├── errorbars.py          # Error bars (nuevo)
│   ├── fill_between.py       # Fill between (nuevo)
│   ├── step_plot.py          # Step plot (nuevo)
│   ├── kde.py                # KDE (avanzado)
│   ├── distplot.py           # Distribution plot (avanzado)
│   ├── rug.py                # Rug plot (avanzado)
│   ├── qqplot.py             # Q-Q plot (avanzado)
│   ├── ecdf.py               # ECDF (avanzado)
│   ├── ridgeline.py          # Ridgeline (avanzado)
│   ├── ribbon.py             # Ribbon (avanzado)
│   ├── hist2d.py             # 2D Histogram (avanzado)
│   ├── polar.py              # Polar chart (avanzado)
│   └── funnel.py             # Funnel chart (avanzado)
│
├── core/                     # Módulos core del sistema
│   ├── comm.py               # CommManager - Comunicación bidireccional JS ↔ Python
│   ├── events.py             # EventManager - Sistema de eventos y callbacks
│   ├── layout.py             # LayoutEngine - Parsing de layouts ASCII
│   ├── registry.py           # Registry global
│   └── exceptions.py         # Jerarquía de excepciones
│
├── data/                     # Procesamiento de datos
│   ├── preparators.py        # Preparación de datos para cada tipo de gráfico
│   ├── validators.py         # Validación de datos
│   ├── transformers.py       # Transformaciones de datos
│   └── aggregators.py        # Agregaciones de datos
│
├── layouts/                   # Layouts modulares
│   ├── matrix.py             # MatrixLayout refactorizado (versión modular)
│   └── reactive.py           # ReactiveMatrixLayout
│
├── reactive/                  # Sistema reactivo modular
│   ├── selection.py          # SelectionModel y ReactiveData
│   ├── engine.py             # ReactiveEngine - Motor reactivo
│   ├── linking.py            # LinkManager - Gestión de enlaces
│   └── engines/              # Engines específicos por entorno
│       ├── base.py           # Base engine
│       ├── jupyter.py        # Engine para Jupyter
│       ├── colab.py          # Engine para Google Colab
│       └── js_only.py        # Engine solo JS
│
├── render/                    # Sistema de renderizado
│   ├── html.py               # HTMLGenerator - Generación de HTML
│   ├── builder.py            # JSBuilder - Construcción de código JS
│   └── assets.py            # AssetManager - Gestión de assets (D3.js, CSS)
│
└── utils/                     # Utilidades
    ├── json.py               # sanitize_for_json - Conversión a JSON
    └── figsize.py            # figsize_to_pixels - Conversión de tamaños
```

---

## 🔄 Flujo de Funcionamiento

### 1. **Inicialización**

```python
from BESTLIB import MatrixLayout
layout = MatrixLayout("AB\nCD")  # Layout ASCII 2x2
```

**Proceso:**
1. `MatrixLayout.__init__()` crea una instancia con `div_id` único
2. Parsea el layout ASCII usando `LayoutEngine.parse_ascii_layout()`
3. Registra la instancia en `CommManager` para comunicación bidireccional
4. Inicializa `EventManager` para manejo de eventos
5. Registra el comm target de Jupyter (`bestlib_matrix`)

### 2. **Mapeo de Gráficos**

```python
MatrixLayout.map_scatter('A', df, x_col='x', y_col='y', category_col='cat')
MatrixLayout.map_barchart('B', df, category_col='cat', value_col='val')
```

**Proceso:**
1. Los métodos `map_*` son `@classmethod` que guardan specs en `MatrixLayout._map`
2. Cada método usa `ChartRegistry.get(chart_type)` para obtener el gráfico
3. El gráfico valida y prepara los datos usando `validate_data()` y `prepare_data()`
4. Genera la spec usando `get_spec()` que retorna un dict con:
   - `type`: Tipo de gráfico
   - `data`: Datos procesados
   - `options`: Opciones de visualización
   - `interaction`: Configuración de interactividad
   - `encoding`: Mapeo de campos a canales visuales

### 3. **Renderizado**

```python
layout.display()  # O simplemente: layout
```

**Proceso:**
1. `_repr_html_()` o `_repr_mimebundle_()` se ejecuta automáticamente
2. `_prepare_repr_data()` prepara:
   - Carga JS y CSS (cacheados)
   - Escapa el layout ASCII
   - Combina `MatrixLayout._map` con metadata
   - Serializa a JSON
3. Genera HTML con:
   - `<style>` con CSS inline
   - `<div id="matrix-{uuid}">` contenedor
   - `<script>` con código JavaScript
4. El JavaScript ejecuta `render(divId, asciiLayout, mapping)`
5. `render()` en `matrix.js`:
   - Parsea el layout ASCII
   - Crea grid de celdas
   - Para cada celda, busca el spec en `mapping`
   - Llama a la función renderizadora correspondiente (ej: `renderScatterD3()`)
   - Cada renderizador usa D3.js para crear el SVG

### 4. **Interactividad**

**Brush Selection (Selección con cepillo):**
1. Usuario dibuja rectángulo en scatter plot
2. JavaScript detecta selección y filtra datos
3. Envía evento `select` vía comm a Python
4. `CommManager._handle_message()` recibe el evento
5. `EventManager.emit()` ejecuta handlers registrados
6. Handlers pueden:
   - Actualizar `SelectionModel` (sistema reactivo)
   - Actualizar otros gráficos (vistas enlazadas)
   - Ejecutar callbacks personalizados

---

## 🎨 Sistema de Gráficos

### Arquitectura de Gráficos

Todos los gráficos heredan de `ChartBase` que define:

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

### Tipos de Gráficos Disponibles

**Básicos (11 tipos):**
1. `scatter` - Scatter plot
2. `bar` - Bar chart
3. `histogram` - Histogram
4. `boxplot` - Box plot
5. `heatmap` - Heatmap
6. `line` - Line chart
7. `pie` - Pie chart
8. `violin` - Violin plot
9. `radviz` - Radviz
10. `star_coordinates` - Star coordinates
11. `parallel_coordinates` - Parallel coordinates

**Nuevos (6 tipos):**
12. `line_plot` - Line plot
13. `horizontal_bar` - Horizontal bar
14. `hexbin` - Hexbin
15. `errorbars` - Error bars
16. `fill_between` - Fill between
17. `step_plot` - Step plot

**Avanzados (10 tipos):**
18. `kde` - Kernel Density Estimation
19. `distplot` - Distribution plot
20. `rug` - Rug plot
21. `qqplot` - Q-Q plot
22. `ecdf` - Empirical CDF
23. `ridgeline` - Ridgeline plot
24. `ribbon` - Ribbon chart
25. `hist2d` - 2D Histogram
26. `polar` - Polar chart
27. `funnel` - Funnel chart

**Total: 27 tipos de gráficos**

### Registro de Gráficos

Los gráficos se registran automáticamente al importar `charts/__init__.py`:

```python
ChartRegistry.register(ScatterChart)
ChartRegistry.register(BarChart)
# ... etc
```

El `ChartRegistry` mantiene un diccionario `_charts: Dict[str, Type[ChartBase]]` que mapea `chart_type` a la clase.

---

## 🔗 Sistema de Comunicación

### CommManager

Gestiona la comunicación bidireccional JavaScript ↔ Python usando Jupyter Comm API.

**Flujo:**
1. `CommManager.register_comm()` registra el comm target `bestlib_matrix`
2. JavaScript crea un comm cuando se renderiza un gráfico interactivo
3. Eventos (select, click, brush) se envían desde JS a Python
4. `CommManager._handle_message()` recibe y enruta eventos
5. `EventManager.emit()` ejecuta handlers registrados

**Eventos soportados:**
- `select` - Selección de datos (brush)
- `click` - Click en elemento
- `brush` - Evento de brush
- `hover` - Hover sobre elemento

### EventManager

Sistema de eventos con soporte para:
- **Handlers de instancia**: Específicos para cada `MatrixLayout`
- **Handlers globales**: Se ejecutan para todos los layouts

```python
# Handler de instancia
layout.on('select', lambda payload: print(f"Seleccionados: {payload['count']}"))

# Handler global
MatrixLayout.on_global('select', lambda payload: log_to_file(payload))
```

---

## ⚡ Sistema Reactivo

### Componentes

1. **SelectionModel**: Modelo reactivo especializado para selecciones
   - Hereda de `ReactiveData`
   - Mantiene historial de selecciones
   - Sincroniza con widgets de ipywidgets

2. **ReactiveData**: Widget reactivo base
   - Traits: `items` (List[Dict]), `count` (Int)
   - Callbacks con `on_change()`
   - Conversión a DataFrame con `to_dataframe()`

3. **ReactiveEngine**: Motor reactivo centralizado
   - Estado centralizado (`_state`)
   - Sistema de suscripciones
   - Prevención de loops infinitos

4. **LinkManager**: Gestión de enlaces entre gráficos
   - Define relaciones entre gráficos
   - Propaga actualizaciones

### Uso

```python
from BESTLIB.reactive import SelectionModel

selection = SelectionModel()
selection.on_change(lambda items, count: print(f"{count} seleccionados"))

layout = MatrixLayout("S")
layout.connect_selection(selection, scatter_letter='S')
layout.display()
```

---

## 🔄 Vistas Enlazadas (LinkedViews)

Sistema que permite que múltiples gráficos se actualicen automáticamente cuando se seleccionan datos.

**Flujo:**
1. `LinkedViews` mantiene múltiples `MatrixLayout` instances
2. Un gráfico es "principal" (con brush selection)
3. Otros gráficos son "secundarios" (se actualizan automáticamente)
4. Cuando hay selección en el principal:
   - Se filtran los datos
   - Se actualizan los secundarios vía JavaScript
   - Se mantiene sincronización

**Ejemplo:**
```python
from BESTLIB.linked import LinkedViews

linked = LinkedViews()
linked.add_scatter('scatter1', data, interactive=True)
linked.add_barchart('bar1', category_col='category')
linked.display()
```

---

## 📐 Layouts ASCII

### Formato

Los layouts se definen con texto ASCII donde cada letra representa una celda:

```
AB
CD
```

Esto crea un grid 2x2 con celdas A, B, C, D.

### Parsing

`LayoutEngine.parse_ascii_layout()`:
1. Divide por líneas (`\n`)
2. Valida que todas las filas tengan igual longitud
3. Crea estructura `Grid` con:
   - `rows`: Número de filas
   - `cols`: Número de columnas
   - `cells`: Diccionario de celdas con posición y letra

### Configuración Avanzada

```python
layout = MatrixLayout(
    "AB\nCD",
    figsize=(400, 300),        # Tamaño global de gráficos
    row_heights=[200, 300],    # Alturas por fila (px o fr)
    col_widths=[1, 2],         # Anchos por columna (ratios o px)
    gap=12,                    # Espaciado entre celdas (px)
    cell_padding=15,           # Padding de celdas (px)
    max_width=1200             # Ancho máximo del layout (px)
)
```

---

## 🎨 Renderizado JavaScript

### Archivo `matrix.js`

Contiene:
1. **Función `render()`**: Función principal que renderiza el layout
2. **Funciones renderizadoras**: Una por cada tipo de gráfico
   - `renderScatterD3()`
   - `renderBarD3()`
   - `renderHistogramD3()`
   - etc.
3. **Utilidades**: Funciones helper para escalas, colores, etc.
4. **Comunicación**: Código para crear comms y enviar eventos

### Flujo de Renderizado

1. `render(divId, asciiLayout, mapping)` se ejecuta
2. Parsea `asciiLayout` en grid
3. Crea contenedor con CSS Grid
4. Para cada celda:
   - Busca spec en `mapping[letter]`
   - Verifica si es spec de BESTLIB o D3.js nativo
   - Llama a función renderizadora correspondiente
   - La función renderizadora:
     - Crea SVG con D3.js
     - Calcula escalas
     - Dibuja elementos (círculos, barras, líneas, etc.)
     - Agrega ejes, tooltips, interactividad

### Soporte para Google Colab

El proyecto incluye detección automática de Colab y carga de assets:
- `AssetManager.ensure_colab_assets_loaded()` carga D3.js desde CDN
- `wait_for_d3=True` hace que el código espere a D3 antes de renderizar
- Evita race conditions donde JS se ejecuta antes de que D3 esté disponible

---

## 📊 Procesamiento de Datos

### Preparadores (`data/preparators.py`)

Cada tipo de gráfico tiene su preparador:
- `prepare_scatter_data()`: Convierte DataFrame/list a formato scatter
- `prepare_bar_data()`: Agrupa y agrega datos para bar chart
- `prepare_histogram_data()`: Binea datos y almacena filas originales por bin
- etc.

**Características:**
- Soporte para DataFrames de pandas y listas de diccionarios
- Preserva datos originales en `_original_row` y `_original_rows`
- Operaciones vectorizadas para mejor rendimiento
- Sampling automático si hay muchos puntos (`maxPoints`)

### Validadores (`data/validators.py`)

Validan que los datos sean adecuados:
- `validate_scatter_data()`: Verifica columnas x, y existen
- `validate_bar_data()`: Verifica columnas de categoría
- `validate_data_structure()`: Verifica estructura general

### Transformadores (`data/transformers.py`)

Transformaciones de datos:
- Normalización
- Agregación
- Filtrado

### Agregadores (`data/aggregators.py`)

Funciones de agregación:
- `count`, `sum`, `mean`, `median`, etc.

---

## 🔧 Utilidades

### `utils/json.py`

`sanitize_for_json()`: Convierte tipos numpy a tipos Python nativos para JSON serialization.

### `utils/figsize.py`

`figsize_to_pixels()`: Convierte figsize de pulgadas a píxeles (asumiendo 96 DPI).

---

## 🚨 Manejo de Errores

### Jerarquía de Excepciones

```python
BestlibError (base)
├── LayoutError      # Errores en layouts
├── ChartError       # Errores en gráficos
├── DataError        # Errores en datos
├── RenderError      # Errores en renderizado
└── CommunicationError  # Errores en comunicación JS ↔ Python
```

### Validaciones

- Layouts ASCII deben tener filas de igual longitud
- Columnas requeridas deben existir en DataFrames
- Datos no pueden estar vacíos
- Tipos de datos deben ser correctos

---

## 🔄 Compatibilidad y Fallbacks

El proyecto tiene múltiples niveles de fallback:

1. **Importaciones opcionales**: Maneja dependencias faltantes con try/except
2. **Múltiples rutas de importación**: Intenta importar desde módulos modulares, luego legacy
3. **Stubs**: Si un módulo no está disponible, crea funciones stub básicas
4. **Detección de entorno**: Detecta Jupyter, Colab, o script standalone

### Flags de Disponibilidad

- `HAS_WIDGETS`: ipywidgets disponible
- `HAS_PANDAS`: pandas disponible
- `HAS_CORE`: módulos core disponibles
- `HAS_CHARTS`: módulos de gráficos disponibles
- `HAS_DATA`: módulos de datos disponibles
- `HAS_UTILS`: módulos de utilidades disponibles
- `HAS_REACTIVE`: módulos reactivos disponibles
- `HAS_LINKED`: módulos de vistas enlazadas disponibles

---

## 📦 Dependencias

### Requeridas (pero opcionales en código)

- `ipython` >= 7.0 (para Jupyter)
- `ipywidgets` >= 7.0 (para widgets interactivos)
- `pandas` >= 1.3.0 (para DataFrames)
- `numpy` >= 1.20.0 (para operaciones numéricas)

### Opcionales

- `scikit-learn` >= 1.0.0 (solo para `add_confusion_matrix`)

**Nota**: El código maneja todas las dependencias como opcionales con try/except, permitiendo que funcione incluso sin algunas dependencias (con funcionalidades limitadas).

---

## 🎯 Características Principales

### 1. **Layouts ASCII**
- Define disposición de gráficos con texto simple
- Soporte para grids complejos
- Configuración de dimensiones, espaciado, padding

### 2. **27+ Tipos de Gráficos**
- Desde básicos (scatter, bar) hasta avanzados (ridgeline, polar)
- Sistema extensible con registro dinámico
- Cada gráfico es una clase independiente

### 3. **Interactividad**
- Brush selection en scatter plots
- Click events
- Tooltips
- Zoom (en algunos gráficos)

### 4. **Vistas Enlazadas**
- Múltiples gráficos sincronizados
- Actualización automática cuando se seleccionan datos
- Visualización de conexiones con líneas SVG

### 5. **Sistema Reactivo**
- `SelectionModel` para selecciones
- `ReactiveData` para datos reactivos
- Callbacks y observadores
- Integración con ipywidgets

### 6. **Comunicación Bidireccional**
- JavaScript → Python: Eventos de selección, click, etc.
- Python → JavaScript: Actualización de datos (futuro)
- Usa Jupyter Comm API

### 7. **Soporte Multi-entorno**
- Jupyter Notebook
- Jupyter Lab
- Google Colab (con detección automática)
- Scripts standalone (modo limitado)

### 8. **Optimizaciones**
- Caché de JS y CSS (carga una sola vez)
- Operaciones vectorizadas con pandas
- Sampling automático para datasets grandes
- Lazy loading de módulos

---

## 🔍 Puntos Clave de la Arquitectura

### 1. **Dualidad Legacy/Modular**

El proyecto tiene dos implementaciones:
- **Legacy**: `matrix.py` (2480 líneas, todo en un archivo)
- **Modular**: `layouts/matrix.py` + módulos separados

El `__init__.py` intenta importar modular primero, luego hace fallback a legacy.

### 2. **Sistema de Especificaciones (Specs)**

Cada gráfico genera una "spec" (especificación) que es un dict con:
- `type`: Tipo de gráfico
- `data`: Datos procesados
- `options`: Opciones de visualización
- `interaction`: Configuración de interactividad
- `encoding`: Mapeo de campos a canales visuales

Las specs se serializan a JSON y se pasan a JavaScript.

### 3. **Registro Dinámico**

Los gráficos se registran automáticamente al importar, permitiendo:
- Extensibilidad sin modificar código existente
- Hot-reload en desarrollo
- Verificación de tipos disponibles

### 4. **Preservación de Datos Originales**

Cada dato procesado incluye:
- `_original_row`: Fila original completa (para scatter, bar, etc.)
- `_original_rows`: Lista de filas originales (para histogram bins, etc.)
- `_original_index`: Índice original

Esto permite que las vistas enlazadas accedan a los datos completos.

### 5. **Gestión de Estado**

- `MatrixLayout._map`: Mapping global de letras a specs (compartido entre instancias)
- `CommManager._instances`: Registro de instancias activas (weakref)
- `EventManager._handlers`: Handlers por instancia y globales
- `ReactiveEngine._state`: Estado reactivo centralizado

---

## 🐛 Problemas Conocidos y Soluciones

### 1. **Race Condition en Colab**

**Problema**: JS se ejecuta antes de que D3.js esté disponible.

**Solución**: `wait_for_d3=True` hace que el código espere a D3.

### 2. **Expansión Infinita de Matriz**

**Problema**: Layouts grandes se expanden infinitamente.

**Solución**: `max_width` automático basado en número de celdas.

### 3. **Datos Vacíos en Vistas Enlazadas**

**Problema**: Histogramas no preservaban filas originales por bin.

**Solución**: `prepare_histogram_data()` ahora almacena `_original_rows` por bin.

### 4. **Import Errors en Jupyter**

**Problema**: Caché de módulos causa errores de importación.

**Solución**: Múltiples rutas de importación con fallbacks y `_ensure_reactive_imported()`.

---

## 📈 Flujo de Datos Completo

```
1. Usuario crea DataFrame/list
   ↓
2. Llama a MatrixLayout.map_scatter('A', data, ...)
   ↓
3. ChartRegistry.get('scatter') obtiene ScatterChart
   ↓
4. ScatterChart.validate_data() valida
   ↓
5. ScatterChart.prepare_data() prepara datos
   ↓
6. ScatterChart.get_spec() genera spec
   ↓
7. Spec se guarda en MatrixLayout._map['A']
   ↓
8. Usuario llama a layout.display()
   ↓
9. _repr_html_() genera HTML con JS
   ↓
10. JavaScript ejecuta render(divId, layout, mapping)
    ↓
11. render() parsea layout y crea grid
    ↓
12. Para cada celda, busca spec en mapping
    ↓
13. Llama a renderScatterD3(cell, spec)
    ↓
14. renderScatterD3() crea SVG con D3.js
    ↓
15. Usuario interactúa (brush selection)
    ↓
16. JavaScript detecta selección y filtra datos
    ↓
17. Envía evento 'select' vía comm a Python
    ↓
18. CommManager recibe y enruta a EventManager
    ↓
19. EventManager ejecuta handlers registrados
    ↓
20. Handlers pueden actualizar SelectionModel o otros gráficos
```

---

## 🎓 Conceptos Clave

### 1. **Spec-based Architecture**

Todo se basa en "specs" (especificaciones) que son dicts serializables a JSON. Esto permite:
- Separación entre lógica Python y renderizado JS
- Fácil debugging (puedes inspeccionar la spec)
- Extensibilidad (nuevos gráficos solo necesitan generar specs)

### 2. **Event-driven Communication**

La comunicación JS ↔ Python es event-driven:
- JavaScript emite eventos
- Python registra handlers
- No hay polling ni estado compartido directo

### 3. **Reactive Programming**

El sistema reactivo permite:
- Actualización automática cuando cambian datos
- Propagación de cambios entre componentes
- Prevención de loops infinitos

### 4. **Modular Design**

Cada componente es independiente:
- Gráficos: Clases separadas, registro dinámico
- Data: Preparadores, validadores, transformadores separados
- Core: Comm, Events, Layout, Registry separados
- Render: HTML, JS Builder, Assets separados

---

## 🔮 Extensiones Futuras

### Posibles Mejoras

1. **Más tipos de gráficos**: Sankey, treemap, network, etc.
2. **Animaciones**: Transiciones suaves entre estados
3. **Exportación**: PNG, SVG, PDF
4. **Temas**: Múltiples temas visuales
5. **Dashboard builder**: UI para crear layouts visualmente
6. **Streaming data**: Actualización en tiempo real
7. **3D plots**: Gráficos 3D con WebGL
8. **Machine learning**: Integración con scikit-learn para visualizaciones ML

---

## 📝 Notas Finales

Este proyecto es un ejemplo excelente de:
- **Arquitectura modular** bien diseñada
- **Compatibilidad hacia atrás** mantenida durante refactorización
- **Manejo robusto de errores** con múltiples fallbacks
- **Documentación extensa** en código y archivos MD
- **Soporte multi-entorno** (Jupyter, Colab, standalone)

El código muestra madurez en:
- Separación de responsabilidades
- Extensibilidad
- Manejo de edge cases
- Optimizaciones de rendimiento

---

**Fecha de Análisis**: 2024
**Versión Analizada**: 0.1.0-modular
**Estado**: En desarrollo activo, modularización en progreso
