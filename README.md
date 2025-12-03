# BESTLIB — Interactive Visualization Framework 

BESTLIB es una librería de visualización interactiva que combina layouts ASCII, gráficos D3.js, un sistema reactivo y comunicación bidireccional entre Python y JavaScript para construir dashboards sin escribir HTML ni JavaScript.

## Características Principales

- Más de 20 tipos de gráficos
- Vistas enlazadas mediante ReactiveMatrixLayout
- Sistema reactivo para sincronización automática
- Comunicación bidireccional JS ↔ Python usando Jupyter Comm
- Layouts ASCII para definir dashboards
- Arquitectura modular y extensible

## Arquitectura del Proyecto

```
bestlib/
├── core/         
├── charts/       
├── data/         
├── layouts/      
├── reactive/     
├── render/       
├── utils/        
└── compat/       
```

### Capas

- Presentación (D3.js)
- Comunicación (CommManager)
- Layouts (MatrixLayout, ReactiveMatrixLayout)
- Gráficos (ChartRegistry, ChartBase)
- Datos (preparators, validators, transformers)
- Renderizado (HTMLGenerator, JSBuilder, AssetManager)

## Instalación

### Google Colab

```
!pip install pybestlib==0.1.0

```

### Verificación

```
import BESTLIB
print(BESTLIB.__version__)
```

## Inicio Rápido

```
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
import pandas as pd

# Crear datos de ejemplo
df = pd.DataFrame({
    'edad': [25, 30, 35, 40, 45, 50],
    'salario': [50000, 60000, 70000, 80000, 90000, 100000],
    'dept': ['IT', 'HR', 'IT', 'Finance', 'HR', 'IT']
})

# Crear modelo de selección
selection = SelectionModel()

# Crear layout
layout = ReactiveMatrixLayout("S", selection_model=selection)

# Agregar scatter plot
layout.add_scatter(
    'S',
    df,
    x_col='edad',
    y_col='salario',
    category_col='dept',
    interactive=True,
    colorMap={
        'IT': '#e74c3c',
        'HR': '#3498db',
        'Finance': '#2ecc71'
    },
    pointRadius=5,
    xLabel='Edad',
    yLabel='Salario'
)

layout.display()
```

## Dashboard con Vistas Enlazadas

```
from BESTLIB.layouts.reactive import ReactiveMatrixLayout
import pandas as pd
import numpy as np

# Creando datos de muestra
np.random.seed(42)
df_iris = pd.DataFrame({
    'petal_length': np.concatenate([
        np.random.normal(1.5, 0.2, 50),   # setosa
        np.random.normal(4.5, 0.5, 50),   # versicolor
        np.random.normal(5.5, 0.6, 50)    # virginica
    ]),
    'petal_width': np.concatenate([
        np.random.normal(0.3, 0.1, 50),
        np.random.normal(1.3, 0.2, 50),
        np.random.normal(2.0, 0.3, 50)
    ]),
    'sepal_length': np.concatenate([
        np.random.normal(5.0, 0.4, 50),
        np.random.normal(6.0, 0.5, 50),
        np.random.normal(6.5, 0.6, 50)
    ]),
    'sepal_width': np.concatenate([
        np.random.normal(3.4, 0.3, 50),
        np.random.normal(2.8, 0.3, 50),
        np.random.normal(3.0, 0.3, 50)
    ]),
    'species': ['setosa'] * 50 + ['versicolor'] * 50 + ['virginica'] * 50
})

# Layout reactivo ASCII
layout = ReactiveMatrixLayout("""
S
X
""")

# SCATTER principal
layout.map_scatter(
    "S",
    df_iris,
    x_col="petal_length",
    y_col="petal_width",
    color_col="species",
    title="Scatter interactivo"
)

# BOXPLOT enlazado al scatter
layout.map_boxplot(
    "X",
    df_iris,
    column="petal_length",
    category_col="species",
    linked_to="S",
    title="Boxplot reactivo"
)

# Renderizar
layout.display()

```

## Funcionamiento Interno

1. El usuario define el layout ASCII  
2. Se agregan gráficos mediante ChartRegistry  
3. Se validan datos, se preparan y se genera una especificación  
4. BESTLIB genera HTML y JS  
5. El navegador renderiza con D3  
6. Eventos se envían JS → Python mediante CommManager  
7. ReactiveEngine actualiza vistas enlazadas

## Catálogo de Gráficos

Incluye scatter, line, bar, histogram, boxplot, heatmap, KDE, violin, pie, polar, radviz, parallel coordinates, hexbin, hist2d, ECDF y más.

## Sistema Reactivo

ReactiveMatrixLayout habilita:

- Selecciones sincronizadas
- Actualización automática
- Propagación de estado en múltiples gráficos

## Comunicación JS ↔ Python

Ejemplo de evento:

```
{
  "type": "select",
  "div_id": "matrix-1234",
  "payload": {
    "items": [],
    "__view_letter__": "A",
    "__graph_type__": "scatter"
  }
}
```

## Desarrollo

### Construcción de assets JS

```
cd js
npm install
npm run build
```

## Contribuciones

Proyecto desarrollado por:  
Nahía Escalante, Alejandro Rojas, Max Antúnez

## Licencia

MIT License.
