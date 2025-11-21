# 🏗️ Propuesta de Modularización para BESTLIB

## 📋 Tabla de Contenidos

1. [Análisis de Arquitectura Actual](#análisis-de-arquitectura-actual)
2. [Problemas Identificados](#problemas-identificados)
3. [Arquitectura Modular Propuesta](#arquitectura-modular-propuesta)
4. [Sistema Extensible de Gráficos](#sistema-extensible-de-gráficos)
5. [Desacoplamiento del Sistema Reactivo](#desacoplamiento-del-sistema-reactivo)
6. [Estrategia de Renderizado HTML/JS](#estrategia-de-renderizado-htmljs)
7. [Patrones de Diseño Recomendados](#patrones-de-diseño-recomendados)
8. [Roadmap Técnico](#roadmap-técnico)
9. [Advertencias y Riesgos](#advertencias-y-riesgos)

---

## 🔍 Análisis de Arquitectura Actual

### Estructura Actual

```
BESTLIB/
├── __init__.py          (36 líneas - importaciones dinámicas)
├── matrix.py            (1940 líneas - MatrixLayout + métodos estáticos)
├── reactive.py          (3146 líneas - ReactiveMatrixLayout + widgets)
├── linked.py            (352 líneas - LinkedViews deprecated)
├── matrix.js            (6062 líneas - TODO el JavaScript en un archivo)
├── style.css            (estilos)
└── d3.min.js           (D3.js minificado)
```

### Componentes Principales

#### 1. **MatrixLayout** (`matrix.py`)
- **Responsabilidades mezcladas:**
  - Gestión de layout ASCII (parsing, grid)
  - Preparación de datos (13 métodos `map_*` para diferentes gráficos)
  - Validación de datos
  - Comunicación bidireccional (comm targets, handlers)
  - Renderizado HTML/JS (generación de código inline)
  - Sistema de eventos (callbacks, handlers globales)
  - Cache de archivos JS/CSS

- **Métodos estáticos por tipo de gráfico:**
  - `map_scatter()`, `map_barchart()`, `map_histogram()`, `map_boxplot()`
  - `map_heatmap()`, `map_correlation_heatmap()`, `map_line()`, `map_pie()`
  - `map_violin()`, `map_radviz()`, `map_star_coordinates()`, `map_parallel_coordinates()`
  - `map_grouped_barchart()`

- **Problemas:**
  - Cada nuevo gráfico requiere modificar `MatrixLayout`
  - Lógica de preparación de datos mezclada con lógica de layout
  - No hay abstracción para tipos de gráficos

#### 2. **ReactiveMatrixLayout** (`reactive.py`)
- **Responsabilidades mezcladas:**
  - Wrapper sobre `MatrixLayout`
  - Sistema reactivo (SelectionModel, ReactiveData)
  - Vistas enlazadas (linking entre gráficos)
  - Generación de JavaScript inline para actualizaciones dinámicas
  - Gestión de callbacks complejos
  - Conversión de datos (DataFrame ↔ listas)

- **Problemas críticos:**
  - **3146 líneas** en un solo archivo
  - JavaScript inline generado en Python (hard to maintain, no syntax highlighting)
  - Lógica de actualización de gráficos mezclada con lógica de estado
  - Callbacks anidados y complejos
  - Flags de actualización para prevenir bucles infinitos (síntoma de diseño problemático)

#### 3. **matrix.js** (6062 líneas)
- **Problemas:**
  - Todo el JavaScript en un solo archivo
  - Lógica de renderizado de todos los gráficos mezclada
  - Difícil de mantener y testear
  - No hay modularización

#### 4. **LinkedViews** (`linked.py`)
- **Estado:** Deprecated (siendo reemplazado por ReactiveMatrixLayout)
- **Problema:** Duplicación de funcionalidad

### Acoplamientos Identificados

1. **MatrixLayout ↔ ReactiveMatrixLayout:**
   - `ReactiveMatrixLayout` hereda funcionalidad de `MatrixLayout` mediante composición
   - Acceso directo a `MatrixLayout._map` (variable de clase)
   - Comparten sistema de eventos

2. **Python ↔ JavaScript:**
   - JavaScript inline generado en Python
   - Estructura de datos compartida (mapping) sin validación de contrato
   - Comm targets acoplados a nombres específicos

3. **Gráficos ↔ Layout:**
   - Cada gráfico conoce detalles del layout
   - Preparación de datos mezclada con especificación de gráfico
   - No hay abstracción de "tipo de gráfico"

4. **Estado ↔ Renderizado:**
   - Lógica de actualización de gráficos mezclada con gestión de estado
   - Callbacks que generan JavaScript inline

---

## ⚠️ Problemas Identificados

### 1. **Violación del Principio de Responsabilidad Única (SRP)**
- `MatrixLayout` hace demasiadas cosas: layout, datos, renderizado, eventos
- `ReactiveMatrixLayout` mezcla estado, linking, y generación de JS

### 2. **Falta de Extensibilidad**
- Agregar un nuevo gráfico requiere:
  - Modificar `MatrixLayout` (agregar método `map_*`)
  - Modificar `matrix.js` (agregar función de renderizado)
  - Modificar `ReactiveMatrixLayout` (si necesita linking)
  - Generar JavaScript inline en Python

### 3. **Código Duplicado**
- Lógica de preparación de datos repetida entre gráficos
- Validación de datos duplicada
- Conversión DataFrame ↔ listas repetida

### 4. **Mantenibilidad**
- Archivos muy grandes (3146, 1940, 6062 líneas)
- JavaScript inline sin syntax highlighting
- Difícil de testear (lógica mezclada)

### 5. **Testing**
- Difícil testear componentes aislados
- Dependencias fuertes entre módulos
- JavaScript inline no se puede testear fácilmente

### 6. **Escalabilidad**
- Agregar nuevas funcionalidades requiere tocar múltiples archivos
- Riesgo de romper funcionalidad existente
- No hay sistema de plugins o extensiones

---

## 🏛️ Arquitectura Modular Propuesta

### Estructura de Carpetas Recomendada

```
bestlib/
├── __init__.py                 # API pública simplificada
│
├── core/                        # Núcleo del sistema
│   ├── __init__.py
│   ├── layout.py               # MatrixLayout (solo layout, sin gráficos)
│   ├── comm.py                 # Sistema de comunicación JS ↔ Python
│   ├── events.py               # Sistema de eventos y callbacks
│   └── registry.py             # Registry global de componentes
│
├── layouts/                     # Tipos de layouts
│   ├── __init__.py
│   ├── matrix.py               # Layout de matriz ASCII (refactorizado)
│   └── grid.py                 # Layout de grid (futuro)
│
├── charts/                      # Sistema de gráficos extensible
│   ├── __init__.py
│   ├── base.py                 # Clase base abstracta para gráficos
│   ├── registry.py             # Registry de tipos de gráficos
│   ├── scatter.py              # Scatter plot
│   ├── bar.py                  # Bar chart
│   ├── histogram.py            # Histogram
│   ├── boxplot.py              # Box plot
│   ├── heatmap.py              # Heatmap
│   ├── line.py                 # Line chart
│   ├── pie.py                  # Pie chart
│   ├── violin.py               # Violin plot
│   ├── radviz.py               # RadViz
│   ├── star_coordinates.py     # Star Coordinates
│   └── parallel_coordinates.py # Parallel Coordinates
│
├── data/                        # Procesamiento de datos
│   ├── __init__.py
│   ├── preparators.py          # Preparadores de datos por tipo
│   ├── validators.py           # Validadores de datos
│   ├── transformers.py         # Transformadores (DataFrame ↔ dicts)
│   └── aggregators.py          # Agregaciones (groupby, sum, etc.)
│
├── reactive/                    # Sistema reactivo desacoplado
│   ├── __init__.py
│   ├── state.py                # ReactiveData, SelectionModel
│   ├── engine.py               # ReactiveEngine (gestión de estado)
│   ├── linking.py              # Sistema de linking entre gráficos
│   └── views.py                # ReactiveMatrixLayout (refactorizado)
│
├── render/                      # Renderizado HTML/JS
│   ├── __init__.py
│   ├── html.py                 # Generación de HTML
│   ├── templates.py            # Plantillas JS (no inline)
│   ├── js_builder.py           # Builder para código JS
│   └── assets.py               # Gestión de assets (JS/CSS)
│
├── utils/                       # Utilidades
│   ├── __init__.py
│   ├── json.py                 # Sanitización JSON
│   ├── figsize.py              # Conversión de figsize
│   └── colors.py                # Utilidades de colores
│
└── themes/                       # Temas y estilos (futuro)
    ├── __init__.py
    ├── default.py
    └── dark.py
```

### Descripción de Módulos

#### **core/** - Núcleo del Sistema

**Responsabilidades:**
- Gestión de layout básico (parsing ASCII, grid)
- Sistema de comunicación bidireccional
- Sistema de eventos
- Registry global

**Por qué separarlo:**
- Es la base de todo el sistema
- No debe depender de gráficos específicos
- Debe ser estable y bien testado

#### **layouts/** - Tipos de Layouts

**Responsabilidades:**
- Implementaciones específicas de layouts
- MatrixLayout refactorizado (solo layout, sin gráficos)

**Por qué separarlo:**
- Permite agregar nuevos tipos de layouts (grid, flex, etc.)
- Separación clara entre layout y contenido

#### **charts/** - Sistema de Gráficos

**Responsabilidades:**
- Definición de tipos de gráficos
- Preparación de datos específica de cada gráfico
- Especificación de renderizado (no implementación JS)

**Por qué separarlo:**
- Extensibilidad: agregar gráficos sin tocar código existente
- Mantenibilidad: cada gráfico en su propio archivo
- Testabilidad: testear gráficos aisladamente

#### **data/** - Procesamiento de Datos

**Responsabilidades:**
- Preparación de datos (normalización, validación)
- Transformaciones (DataFrame ↔ dicts)
- Agregaciones (groupby, sum, count)

**Por qué separarlo:**
- Reutilizable entre gráficos
- Testeable independientemente
- Evita duplicación de código

#### **reactive/** - Sistema Reactivo

**Responsabilidades:**
- Gestión de estado (ReactiveData, SelectionModel)
- Motor reactivo (ReactiveEngine)
- Sistema de linking entre gráficos
- ReactiveMatrixLayout (wrapper que usa componentes modulares)

**Por qué separarlo:**
- Desacopla estado de renderizado
- Permite usar sistema reactivo sin layouts
- Facilita testing del estado

#### **render/** - Renderizado

**Responsabilidades:**
- Generación de HTML
- Plantillas JS (no inline)
- Builder para código JS
- Gestión de assets

**Por qué separarlo:**
- Separación de concerns: datos vs presentación
- Facilita cambiar estrategia de renderizado
- Permite usar bundlers en el futuro

#### **utils/** - Utilidades

**Responsabilidades:**
- Funciones auxiliares reutilizables
- Sin dependencias de otros módulos

#### **themes/** - Temas (Futuro)

**Responsabilidades:**
- Estilos y temas
- Configuración visual

---

## 🎨 Sistema Extensible de Gráficos

### Interfaz Base para Gráficos

```python
# charts/base.py (conceptual, no código real)

class ChartBase(ABC):
    """
    Clase base abstracta para todos los gráficos.
    Define el contrato que deben cumplir todos los gráficos.
    """
    
    @property
    @abstractmethod
    def chart_type(self) -> str:
        """Tipo de gráfico (ej: 'scatter', 'bar')"""
        pass
    
    @abstractmethod
    def prepare_data(self, data, **kwargs) -> dict:
        """
        Prepara datos para el gráfico.
        
        Args:
            data: DataFrame o lista de diccionarios
            **kwargs: Parámetros específicos del gráfico
        
        Returns:
            dict: Datos preparados en formato estándar
        """
        pass
    
    @abstractmethod
    def validate_data(self, data, **kwargs) -> bool:
        """
        Valida que los datos sean adecuados para este gráfico.
        
        Returns:
            bool: True si los datos son válidos
        """
        pass
    
    @abstractmethod
    def get_spec(self, data, **kwargs) -> dict:
        """
        Genera la especificación del gráfico.
        
        Returns:
            dict: Spec con 'type', 'data', y opciones
        """
        pass
    
    def get_js_renderer(self) -> str:
        """
        Retorna el nombre de la función JS que renderiza este gráfico.
        Por defecto: 'render{ChartType}' (ej: 'renderScatter')
        
        Returns:
            str: Nombre de función JS
        """
        return f"render{self.chart_type.capitalize()}"
```

### Registry de Gráficos

```python
# charts/registry.py (conceptual)

class ChartRegistry:
    """
    Registry global de tipos de gráficos.
    Permite registrar nuevos gráficos sin modificar código existente.
    """
    
    _charts = {}  # {chart_type: ChartClass}
    
    @classmethod
    def register(cls, chart_class: Type[ChartBase]):
        """Registra un nuevo tipo de gráfico"""
        chart_type = chart_class().chart_type
        cls._charts[chart_type] = chart_class
    
    @classmethod
    def get(cls, chart_type: str) -> ChartBase:
        """Obtiene una instancia de gráfico por tipo"""
        if chart_type not in cls._charts:
            raise ValueError(f"Chart type '{chart_type}' not registered")
        return cls._charts[chart_type]()
    
    @classmethod
    def list_types(cls) -> List[str]:
        """Lista todos los tipos de gráficos registrados"""
        return list(cls._charts.keys())
```

### Ejemplo de Implementación de Gráfico

```python
# charts/scatter.py (conceptual)

from .base import ChartBase
from ..data import preparators, validators

class ScatterChart(ChartBase):
    
    @property
    def chart_type(self) -> str:
        return 'scatter'
    
    def validate_data(self, data, x_col=None, y_col=None, **kwargs) -> bool:
        """Valida que existan columnas x e y"""
        return validators.has_columns(data, [x_col, y_col])
    
    def prepare_data(self, data, x_col=None, y_col=None, 
                     category_col=None, **kwargs):
        """Prepara datos para scatter plot"""
        return preparators.prepare_scatter_data(
            data, x_col=x_col, y_col=y_col, category_col=category_col
        )
    
    def get_spec(self, data, **kwargs) -> dict:
        """Genera spec para scatter plot"""
        prepared_data = self.prepare_data(data, **kwargs)
        return {
            'type': self.chart_type,
            'data': prepared_data,
            **kwargs
        }
```

### Cómo Agregar un Nuevo Gráfico

**Paso 1:** Crear clase de gráfico
```python
# charts/new_chart.py
from .base import ChartBase

class NewChart(ChartBase):
    @property
    def chart_type(self) -> str:
        return 'new_chart'
    
    # Implementar métodos abstractos...
```

**Paso 2:** Registrar el gráfico
```python
# charts/__init__.py
from .registry import ChartRegistry
from .new_chart import NewChart

ChartRegistry.register(NewChart)
```

**Paso 3:** Agregar función JS de renderizado
```javascript
// render/templates/charts/new_chart.js
function renderNewChart(container, spec, d3, divId) {
    // Lógica de renderizado...
}
```

**Paso 4:** Registrar función JS
```python
# render/templates.py
CHARTS_JS = {
    'new_chart': 'renderNewChart',
    # ...
}
```

**¡Listo!** El gráfico está disponible sin modificar código existente.

### Manejo de Inputs de Datos

**Estrategia:**
- Cada gráfico define sus requisitos de datos
- Preparadores genéricos en `data/preparators.py`
- Validadores en `data/validators.py`
- Transformadores en `data/transformers.py`

**Ejemplo:**
```python
# data/preparators.py
def prepare_scatter_data(data, x_col, y_col, category_col=None):
    """Prepara datos para scatter plot"""
    # Lógica reutilizable
    pass

def prepare_bar_data(data, category_col, value_col=None):
    """Prepara datos para bar chart"""
    # Lógica reutilizable
    pass
```

### Sistema de Linking

**Estrategia:**
- Linking manejado por `reactive/linking.py`
- Gráficos no conocen el sistema de linking
- Linking se configura externamente

**Ejemplo:**
```python
# reactive/linking.py
class LinkManager:
    def link_charts(self, source_chart, target_chart, link_type='selection'):
        """Enlaza dos gráficos"""
        # Configurar callbacks
        pass
```

### Evitar Código Duplicado

**Estrategias:**
1. **Preparadores genéricos** en `data/preparators.py`
2. **Validadores reutilizables** en `data/validators.py`
3. **Utilidades compartidas** en `utils/`
4. **Clase base** con funcionalidad común

---

## 🔄 Desacoplamiento del Sistema Reactivo

### Arquitectura Propuesta

```
┌─────────────────┐
│  ReactiveEngine │  ← Motor de estado centralizado
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ State │ │ Views │  ← Estado y vistas separados
└───────┘ └───────┘
    │         │
    └────┬────┘
         │
┌────────▼────────┐
│  LinkManager     │  ← Sistema de linking independiente
└─────────────────┘
```

### ReactiveCore / StateEngine

**Propósito:**
- Motor de estado centralizado
- Desacoplado de layouts y gráficos
- Gestiona cambios de estado y notifica observadores

**Estructura propuesta:**
```python
# reactive/engine.py (conceptual)

class ReactiveEngine:
    """
    Motor reactivo centralizado.
    Gestiona estado y notifica cambios a observadores.
    """
    
    def __init__(self):
        self._state = {}  # Estado global
        self._observers = {}  # {state_key: [callbacks]}
    
    def set_state(self, key: str, value: Any):
        """Actualiza estado y notifica observadores"""
        old_value = self._state.get(key)
        self._state[key] = value
        self._notify(key, old_value, value)
    
    def get_state(self, key: str) -> Any:
        """Obtiene estado actual"""
        return self._state.get(key)
    
    def observe(self, key: str, callback: Callable):
        """Registra observador para cambios de estado"""
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(callback)
    
    def _notify(self, key: str, old_value: Any, new_value: Any):
        """Notifica a observadores de cambios"""
        for callback in self._observers.get(key, []):
            callback(old_value, new_value)
```

### Separación Estado y Vistas

**Estrategia:**
- **Estado:** Gestionado por `ReactiveEngine` o `SelectionModel`
- **Vistas:** Solo leen estado y se actualizan cuando cambia
- **Renderizado:** Separado en módulo `render/`

**Ejemplo:**
```python
# reactive/state.py
class SelectionModel:
    """Modelo de selección (solo estado)"""
    def __init__(self, engine: ReactiveEngine):
        self.engine = engine
        self.engine.observe('selection', self._on_selection_change)
    
    def update(self, items):
        """Actualiza selección (solo estado)"""
        self.engine.set_state('selection', items)
    
    def _on_selection_change(self, old_value, new_value):
        """Callback interno (no renderiza)"""
        pass

# reactive/views.py
class ReactiveMatrixLayout:
    """Vista reactiva (lee estado, renderiza)"""
    def __init__(self, selection_model: SelectionModel):
        self.selection_model = selection_model
        # Observar cambios de estado
        selection_model.engine.observe('selection', self._update_views)
    
    def _update_views(self, old_value, new_value):
        """Actualiza vistas cuando cambia estado (renderiza)"""
        # Llamar a render/ para actualizar gráficos
        pass
```

### Estados Compartidos

**Estrategia:**
- Estados compartidos en `ReactiveEngine` global
- Cada componente puede observar diferentes keys
- Sin acoplamiento directo entre componentes

**Ejemplo:**
```python
# Estado compartido
engine = ReactiveEngine()
engine.set_state('selected_data', [])
engine.set_state('filter_active', False)

# Componente 1 observa 'selected_data'
engine.observe('selected_data', callback1)

# Componente 2 observa 'selected_data' y 'filter_active'
engine.observe('selected_data', callback2)
engine.observe('filter_active', callback2)
```

### Evitar Mezclar Lógica de UI con Lógica de Datos

**Reglas:**
1. **Estado:** Solo datos, sin lógica de UI
2. **Vistas:** Solo renderizado, sin lógica de negocio
3. **Linking:** Lógica de coordinación, no renderizado
4. **Renderizado:** Solo presentación, sin estado

**Ejemplo de separación:**
```python
# ❌ MAL: Mezclado
class BadReactiveLayout:
    def update_chart(self, items):
        # Lógica de datos
        data = process_items(items)
        # Lógica de UI (generar JS inline)
        js = f"updateChart({data})"
        # Renderizar
        display(Javascript(js))

# ✅ BIEN: Separado
class GoodReactiveLayout:
    def __init__(self, data_processor, renderer):
        self.data_processor = data_processor
        self.renderer = renderer
    
    def update_chart(self, items):
        # Solo coordinar
        data = self.data_processor.process(items)  # Lógica de datos
        self.renderer.update('chart_id', data)     # Renderizado
```

---

## 🎨 Estrategia de Renderizado HTML/JS

### Problema Actual

- JavaScript inline generado en Python
- Sin syntax highlighting
- Difícil de mantener
- No se puede usar bundlers
- Código JS mezclado con lógica Python

### Solución Propuesta

#### 1. **Plantillas JS Separadas**

```
render/
├── templates/
│   ├── base.js              # Funciones base (comm, eventos)
│   ├── charts/
│   │   ├── scatter.js       # Renderizado de scatter
│   │   ├── bar.js           # Renderizado de bar
│   │   ├── histogram.js    # Renderizado de histogram
│   │   └── ...              # Un archivo por gráfico
│   └── layout.js            # Renderizado de layout
└── builder.py                # Builder que combina plantillas
```

#### 2. **Builder de Código JS**

```python
# render/builder.py (conceptual)

class JSBuilder:
    """
    Construye código JS combinando plantillas.
    """
    
    def __init__(self):
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Carga plantillas JS desde archivos"""
        # Cargar base.js
        # Cargar charts/*.js según gráficos usados
        pass
    
    def build(self, chart_types: List[str]) -> str:
        """
        Construye código JS para los gráficos especificados.
        
        Args:
            chart_types: Lista de tipos de gráficos a incluir
        
        Returns:
            str: Código JS completo
        """
        # Combinar plantillas
        js_code = self.templates['base']
        for chart_type in chart_types:
            if chart_type in self.templates:
                js_code += self.templates[chart_type]
        return js_code
```

#### 3. **Evitar HTML Inline Inmantenible**

**Estrategia:**
- Usar plantillas HTML (Jinja2 o similar)
- Separar estructura de datos
- Generar HTML de forma declarativa

**Ejemplo:**
```python
# render/html.py (conceptual)

HTML_TEMPLATE = """
<style>{css}</style>
<div id="{div_id}" class="matrix-layout">{content}</div>
<script>
{js_code}
</script>
"""

def generate_html(div_id: str, css: str, js_code: str) -> str:
    """Genera HTML usando plantilla"""
    return HTML_TEMPLATE.format(
        div_id=div_id,
        css=css,
        js_code=js_code
    )
```

#### 4. **Bundling Modular (Futuro)**

**Estrategia:**
- Usar bundler (webpack, rollup, etc.) para combinar JS
- Generar bundles por tipo de gráfico
- Cargar solo lo necesario

**Estructura:**
```
render/
├── src/                    # Código fuente JS
│   ├── charts/
│   └── base/
├── dist/                   # Bundles generados
│   ├── bestlib-core.js
│   ├── bestlib-scatter.js
│   └── bestlib-all.js
└── webpack.config.js       # Configuración de bundling
```

#### 5. **Compatibilidad con Jupyter, Colab y Deepnote**

**Estrategia:**
- Detectar entorno automáticamente
- Adaptar carga de JS según entorno
- Fallbacks para entornos sin soporte completo

**Ejemplo:**
```python
# render/assets.py (conceptual)

class AssetLoader:
    """Carga assets según entorno"""
    
    def detect_environment(self) -> str:
        """Detecta entorno (jupyter, colab, deepnote)"""
        # Lógica de detección
        pass
    
    def load_js(self, chart_types: List[str]) -> str:
        """Carga JS según entorno"""
        env = self.detect_environment()
        if env == 'colab':
            # Estrategia para Colab
            return self._load_for_colab(chart_types)
        elif env == 'jupyter':
            # Estrategia para Jupyter
            return self._load_for_jupyter(chart_types)
        # ...
```

---

## 🎯 Patrones de Diseño Recomendados

### 1. **Observer Pattern** → Linking y Selección

**Dónde usar:**
- Sistema de eventos (`core/events.py`)
- Sistema reactivo (`reactive/engine.py`)
- Linking entre gráficos (`reactive/linking.py`)

**Por qué:**
- Desacopla emisores de receptores
- Permite múltiples observadores
- Facilita extensibilidad

**Ejemplo:**
```python
# reactive/engine.py
class ReactiveEngine:
    def observe(self, key: str, callback: Callable):
        """Observer: registra callback para cambios"""
        pass
    
    def _notify(self, key: str, old_value, new_value):
        """Notifica a todos los observadores"""
        for callback in self._observers.get(key, []):
            callback(old_value, new_value)
```

### 2. **Strategy Pattern** → Distintos Layouts

**Dónde usar:**
- Tipos de layouts (`layouts/`)
- Estrategias de renderizado (`render/`)

**Por qué:**
- Permite intercambiar algoritmos
- Facilita agregar nuevos layouts
- Separación de concerns

**Ejemplo:**
```python
# layouts/base.py
class LayoutStrategy(ABC):
    @abstractmethod
    def parse(self, layout_spec: str) -> Grid:
        pass
    
    @abstractmethod
    def render(self, grid: Grid) -> str:
        pass

# layouts/matrix.py
class MatrixLayoutStrategy(LayoutStrategy):
    def parse(self, layout_spec: str) -> Grid:
        # Parsear ASCII
        pass
```

### 3. **Factory Pattern** → Creación de Gráficos

**Dónde usar:**
- Registry de gráficos (`charts/registry.py`)
- Creación de instancias de gráficos

**Por qué:**
- Centraliza creación de objetos
- Facilita extensibilidad
- Oculta detalles de implementación

**Ejemplo:**
```python
# charts/registry.py
class ChartRegistry:
    @classmethod
    def create(cls, chart_type: str, **kwargs) -> ChartBase:
        """Factory: crea instancia de gráfico"""
        chart_class = cls._charts.get(chart_type)
        if not chart_class:
            raise ValueError(f"Unknown chart type: {chart_type}")
        return chart_class(**kwargs)
```

### 4. **Composite Pattern** → Matrices y Sublayouts

**Dónde usar:**
- Layouts anidados
- Gráficos compuestos

**Por qué:**
- Trata objetos individuales y compuestos uniformemente
- Facilita estructuras recursivas

**Ejemplo:**
```python
# layouts/composite.py
class CompositeLayout:
    def __init__(self):
        self.children = []  # Layouts hijos
    
    def add_child(self, layout: Layout):
        self.children.append(layout)
    
    def render(self) -> str:
        # Renderizar hijos recursivamente
        return ''.join(child.render() for child in self.children)
```

### 5. **Adapter Pattern** → Integración con JS

**Dónde usar:**
- Adaptar datos Python a formato JS
- Adaptar eventos JS a eventos Python

**Por qué:**
- Permite que interfaces incompatibles trabajen juntas
- Facilita integración con D3.js

**Ejemplo:**
```python
# render/adapters.py
class JSDataAdapter:
    """Adapta datos Python a formato JS"""
    def adapt(self, data: Any) -> str:
        """Convierte datos a JSON string para JS"""
        return json.dumps(self._sanitize(data))
    
    def _sanitize(self, data: Any) -> Any:
        """Sanitiza datos para JSON"""
        # Lógica de sanitización
        pass
```

### 6. **Template Method Pattern** → Preparación de Datos

**Dónde usar:**
- Preparación de datos en gráficos (`charts/base.py`)

**Por qué:**
- Define esqueleto de algoritmo
- Permite que subclases redefinan pasos específicos

**Ejemplo:**
```python
# charts/base.py
class ChartBase(ABC):
    def prepare_data(self, data, **kwargs):
        """Template method"""
        self.validate_data(data, **kwargs)  # Paso 1
        processed = self._process(data, **kwargs)  # Paso 2
        return self._format(processed)  # Paso 3
    
    @abstractmethod
    def _process(self, data, **kwargs):
        """Paso específico de cada gráfico"""
        pass
```

### 7. **Registry Pattern** → Sistema de Registro

**Dónde usar:**
- Registry de gráficos (`charts/registry.py`)
- Registry de layouts (`layouts/registry.py`)

**Por qué:**
- Centraliza registro de componentes
- Facilita descubrimiento de componentes
- Permite extensibilidad sin modificar código existente

---

## 🗺️ Roadmap Técnico

### **Fase 1: Fundación (Crítico - Hacer Primero)**

**Objetivo:** Crear estructura modular sin romper código existente

**Tareas:**
1. ✅ Crear estructura de carpetas
2. ✅ Mover utilidades a `utils/`
3. ✅ Extraer sistema de comunicación a `core/comm.py`
4. ✅ Extraer sistema de eventos a `core/events.py`
5. ✅ Crear `charts/base.py` con interfaz abstracta
6. ✅ Crear `charts/registry.py`
7. ✅ Migrar un gráfico de prueba (ej: scatter) a nuevo sistema
8. ✅ Mantener compatibilidad hacia atrás (wrappers en `matrix.py`)

**Duración estimada:** 2-3 semanas

**Riesgo:** Medio (requiere cuidado para no romper funcionalidad)

---

### **Fase 2: Migración de Gráficos (Importante)**

**Objetivo:** Migrar todos los gráficos al nuevo sistema

**Tareas:**
1. Migrar gráficos uno por uno:
   - scatter → `charts/scatter.py`
   - bar → `charts/bar.py`
   - histogram → `charts/histogram.py`
   - boxplot → `charts/boxplot.py`
   - heatmap → `charts/heatmap.py`
   - line → `charts/line.py`
   - pie → `charts/pie.py`
   - violin → `charts/violin.py`
   - radviz → `charts/radviz.py`
   - star_coordinates → `charts/star_coordinates.py`
   - parallel_coordinates → `charts/parallel_coordinates.py`
   - grouped_barchart → `charts/grouped_bar.py`

2. Extraer lógica de preparación de datos a `data/preparators.py`
3. Extraer validadores a `data/validators.py`
4. Actualizar `MatrixLayout` para usar registry

**Duración estimada:** 3-4 semanas

**Riesgo:** Bajo (migración incremental)

---

### **Fase 3: Desacoplamiento Reactivo (Crítico)**

**Objetivo:** Separar sistema reactivo del layout

**Tareas:**
1. Crear `reactive/engine.py` (ReactiveEngine)
2. Refactorizar `SelectionModel` para usar engine
3. Crear `reactive/linking.py` (sistema de linking independiente)
4. Refactorizar `ReactiveMatrixLayout` para usar componentes modulares
5. Eliminar JavaScript inline de Python
6. Mover lógica de actualización a `render/`

**Duración estimada:** 3-4 semanas

**Riesgo:** Alto (toca código crítico)

---

### **Fase 4: Renderizado Modular (Importante)**

**Objetivo:** Separar JavaScript en plantillas

**Tareas:**
1. Extraer funciones JS a `render/templates/`
2. Crear `render/builder.py` para combinar plantillas
3. Crear `render/html.py` para generación de HTML
4. Actualizar `MatrixLayout` para usar builder
5. Eliminar JavaScript inline

**Duración estimada:** 2-3 semanas

**Riesgo:** Medio (requiere testing cuidadoso)

---

### **Fase 5: Optimizaciones (Opcional)**

**Objetivo:** Mejorar rendimiento y mantenibilidad

**Tareas:**
1. Implementar bundling modular (webpack/rollup)
2. Lazy loading de gráficos
3. Cache de plantillas JS
4. Optimización de comunicación JS ↔ Python
5. Agregar temas (`themes/`)

**Duración estimada:** 2-3 semanas

**Riesgo:** Bajo (mejoras opcionales)

---

### **Fase 6: Limpieza (Opcional)**

**Objetivo:** Eliminar código legacy

**Tareas:**
1. Eliminar `linked.py` (deprecated)
2. Limpiar código duplicado
3. Actualizar documentación
4. Agregar tests unitarios
5. Agregar tests de integración

**Duración estimada:** 1-2 semanas

**Riesgo:** Bajo (solo limpieza)

---

## ⚠️ Advertencias y Riesgos

### **Riesgos de Modularizar Mal**

1. **Sobre-modularización:**
   - Crear demasiados módulos pequeños
   - Dificulta navegación
   - Aumenta complejidad innecesariamente

2. **Bajo-modularización:**
   - Mantener archivos grandes
   - No separar responsabilidades
   - Dificulta mantenimiento

3. **Dependencias circulares:**
   - Módulos que se importan mutuamente
   - Dificulta testing
   - Causa problemas de importación

4. **Acoplamiento oculto:**
   - Módulos que parecen independientes pero están acoplados
   - Dificulta cambios
   - Causa bugs inesperados

### **Decisiones Difíciles de Revertir**

1. **Estructura de carpetas:**
   - Una vez establecida, cambiar es costoso
   - Afecta imports y documentación
   - **Recomendación:** Planificar bien desde el inicio

2. **API pública:**
   - Cambios en API pública rompen código de usuarios
   - **Recomendación:** Mantener compatibilidad hacia atrás con wrappers

3. **Sistema de registro:**
   - Cambiar registry afecta extensibilidad
   - **Recomendación:** Diseñar bien desde el inicio

4. **Formato de datos:**
   - Cambios en formato de datos afectan todos los gráficos
   - **Recomendación:** Definir contrato claro desde el inicio

### **Malas Prácticas a Evitar**

1. **❌ NO:** Generar JavaScript inline en Python
   - **✅ SÍ:** Usar plantillas JS separadas

2. **❌ NO:** Mezclar lógica de estado con renderizado
   - **✅ SÍ:** Separar estado y vistas

3. **❌ NO:** Modificar código existente para agregar gráficos
   - **✅ SÍ:** Usar sistema de registro

4. **❌ NO:** Duplicar código entre gráficos
   - **✅ SÍ:** Extraer lógica común a módulos compartidos

5. **❌ NO:** Crear dependencias circulares
   - **✅ SÍ:** Diseñar jerarquía de dependencias clara

6. **❌ NO:** Romper compatibilidad hacia atrás sin necesidad
   - **✅ SÍ:** Mantener wrappers para API antigua

7. **❌ NO:** Hacer cambios grandes de una vez
   - **✅ SÍ:** Migración incremental

### **Recomendaciones Finales**

1. **Empezar pequeño:**
   - Migrar un gráfico primero
   - Validar arquitectura
   - Iterar

2. **Mantener compatibilidad:**
   - Wrappers para API antigua
   - Deprecation warnings
   - Documentación de migración

3. **Testing continuo:**
   - Tests unitarios para cada módulo
   - Tests de integración
   - Tests de regresión

4. **Documentación:**
   - Documentar arquitectura
   - Guías de migración
   - Ejemplos de extensión

5. **Revisión de código:**
   - Code reviews antes de merge
   - Validar arquitectura
   - Asegurar calidad

---

## 📊 Diagrama Conceptual de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        API Pública                           │
│                  (bestlib/__init__.py)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│   Layouts    │ │   Charts    │ │  Reactive   │
│  (layouts/)  │ │  (charts/)  │ │ (reactive/) │
└──────┬───────┘ └──────┬───────┘ └──────┬──────┘
       │               │                │
       └───────────────┼────────────────┘
                       │
            ┌──────────▼──────────┐
            │      Core           │
            │  (core/)            │
            │  - Layout Engine    │
            │  - Comm System      │
            │  - Events           │
            │  - Registry         │
            └──────────┬──────────┘
                       │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│    Data      │ │   Render    │ │   Utils     │
│  (data/)     │ │  (render/)  │ │  (utils/)   │
└──────────────┘ └─────────────┘ └────────────┘
```

### Flujo de Datos

```
Usuario
  │
  ├─> Layout (layouts/matrix.py)
  │     │
  │     ├─> Chart Registry (charts/registry.py)
  │     │     │
  │     │     └─> Chart (charts/scatter.py)
  │     │           │
  │     │           ├─> Data Preparator (data/preparators.py)
  │     │           └─> Data Validator (data/validators.py)
  │     │
  │     └─> Renderer (render/builder.py)
  │           │
  │           ├─> HTML Generator (render/html.py)
  │           └─> JS Templates (render/templates/)
  │
  └─> Reactive System (reactive/)
        │
        ├─> Reactive Engine (reactive/engine.py)
        │     │
        │     └─> State (reactive/state.py)
        │
        └─> Link Manager (reactive/linking.py)
              │
              └─> Updates Charts via Engine
```

---

## ✅ Checklist de Implementación

### Fase 1: Fundación
- [ ] Crear estructura de carpetas
- [ ] Mover utilidades
- [ ] Extraer comm system
- [ ] Extraer events system
- [ ] Crear ChartBase
- [ ] Crear ChartRegistry
- [ ] Migrar scatter como prueba
- [ ] Wrappers de compatibilidad

### Fase 2: Migración
- [ ] Migrar todos los gráficos
- [ ] Extraer preparators
- [ ] Extraer validators
- [ ] Actualizar MatrixLayout

### Fase 3: Reactivo
- [ ] Crear ReactiveEngine
- [ ] Refactorizar SelectionModel
- [ ] Crear LinkManager
- [ ] Refactorizar ReactiveMatrixLayout
- [ ] Eliminar JS inline

### Fase 4: Renderizado
- [ ] Extraer plantillas JS
- [ ] Crear JSBuilder
- [ ] Crear HTML generator
- [ ] Actualizar MatrixLayout

### Fase 5: Optimizaciones
- [ ] Bundling modular
- [ ] Lazy loading
- [ ] Cache de plantillas
- [ ] Temas

### Fase 6: Limpieza
- [ ] Eliminar código legacy
- [ ] Tests unitarios
- [ ] Tests de integración
- [ ] Documentación

---

## 📝 Notas Finales

Esta propuesta es un **plan arquitectónico**, no código de implementación. El objetivo es guiar la modularización de BESTLIB de forma estructurada y escalable.

**Principios clave:**
1. **Separación de responsabilidades:** Cada módulo tiene una responsabilidad clara
2. **Extensibilidad:** Agregar gráficos sin modificar código existente
3. **Mantenibilidad:** Código organizado y fácil de entender
4. **Testabilidad:** Componentes aislados y testeables
5. **Compatibilidad:** Mantener API existente durante migración

**Próximos pasos:**
1. Revisar y validar esta propuesta
2. Priorizar fases según necesidades
3. Comenzar con Fase 1 (Fundación)
4. Iterar y ajustar según feedback

---

**Documento generado:** 2025-01-XX  
**Versión:** 1.0  
**Autor:** Análisis arquitectónico de BESTLIB

