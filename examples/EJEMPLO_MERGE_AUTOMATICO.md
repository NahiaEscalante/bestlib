# 🎯 Ejemplo: Merge Automático en MatrixLayout

Este ejemplo demuestra el nuevo sistema de **merge automático** que detecta y fusiona regiones contiguas de celdas con la misma letra, sin necesidad de especificar `__merge__` manualmente.

## 🔍 Algoritmo de Detección de Regiones Contiguas

El sistema utiliza un algoritmo de **expansión rectangular** (similar a flood-fill pero optimizado):

1. **Iteración por filas y columnas**: Recorre la matriz de izquierda a derecha, arriba a abajo
2. **Detección de inicio de región**: Cuando encuentra una celda no visitada con una letra
3. **Expansión horizontal**: Expande hacia la derecha mientras la letra sea la misma
4. **Expansión vertical**: Expande hacia abajo verificando que todas las filas en el rango tengan la misma letra
5. **Marcado de celdas**: Marca todas las celdas de la región como visitadas
6. **Aplicación de spans**: Usa CSS Grid `grid-row` y `grid-column` con `span` para fusionar visualmente

### Pseudocódigo del Algoritmo:

```
Para cada celda (r, c) en la matriz:
    Si ya está visitada → continuar
    Si es '.' → marcar como visitada y continuar
    
    letra = matriz[r][c]
    width = 1, height = 1
    
    // Expandir horizontalmente
    mientras (c + width < columnas && 
              !visitada[r][c+width] && 
              matriz[r][c+width] == letra):
        width++
    
    // Expandir verticalmente
    mientras (puede crecer verticalmente):
        para cada columna en el rango [c, c+width):
            si (matriz[r+height][cc] != letra):
                puede crecer = false
                break
        si puede crecer:
            height++
    
    // Crear celda fusionada con span
    celda.gridRow = r+1 / span height
    celda.gridColumn = c+1 / span width
```

## 📝 Ejemplo 1: Merge Automático Básico (Sin `__merge__`)

```python
from BESTLIB.matrix import MatrixLayout

# NO necesitas especificar __merge__ - el sistema detecta automáticamente
MatrixLayout.map({
    "A": "<b style='color:blue'>Título Principal</b>",
    "B": "<b style='color:red'>ROJO</b>",
    "C": "<i>Control</i>"
})

layout = MatrixLayout("""
AAC
AAC
BBB
""")

layout.display()
```

**Resultado automático:**
- Las celdas `A` se fusionan automáticamente en un bloque 2x2
- Las celdas `B` se fusionan automáticamente en un bloque 1x3
- La celda `C` permanece individual

## 📝 Ejemplo 2: Merge Automático con Gráficos

```python
from BESTLIB.reactive import ReactiveMatrixLayout
import pandas as pd
import numpy as np

# Crear datos
np.random.seed(42)
df = pd.DataFrame({
    'edad': np.random.randint(20, 60, 100),
    'salario': np.random.randint(3000, 15000, 100),
    'departamento': np.random.choice(['IT', 'Sales', 'Finance'], 100),
    'experiencia': np.random.randint(1, 20, 100)
})

# Layout con merge automático
# SS = Scatter plot grande (2x2)
# BB = Bar chart ancho (1x2)
# HH = Histogram ancho (1x2)
layout = ReactiveMatrixLayout("""
SSBB
SSHH
""")

# NO necesitas especificar __merge__ - funciona automáticamente!

# Scatter plot (se fusionará automáticamente en 2x2)
layout.add_scatter(
    'S',
    df,
    x_col='edad',
    y_col='salario',
    category_col='departamento',
    interactive=True,
    axes=True
)

# Bar chart (se fusionará automáticamente en 1x2)
layout.add_barchart(
    'B',
    category_col='departamento',
    linked_to='S',
    axes=True
)

# Histogram (se fusionará automáticamente en 1x2)
layout.add_histogram(
    'H',
    column='edad',
    bins=20,
    linked_to='S',
    axes=True
)

layout.display()
```

## 📝 Ejemplo 3: Control Manual del Merge (Opcional)

Si necesitas **desactivar** el merge automático o controlarlo manualmente:

```python
from BESTLIB.matrix import MatrixLayout

# Opción 1: Desactivar merge completamente
MatrixLayout.map({
    "__merge__": False,  # Desactiva merge automático
    "A": "Contenido A",
    "B": "Contenido B"
})

# Opción 2: Solo merge para letras específicas
MatrixLayout.map({
    "__merge__": ["A"],  # Solo fusionar A, no B
    "A": "Fusionado",
    "B": "Individual"
})

# Opción 3: Merge explícito para todas (igual que automático)
MatrixLayout.map({
    "__merge__": True,  # Fusiona todas explícitamente
    "A": "Contenido A",
    "B": "Contenido B"
})
```

## 📝 Ejemplo 4: Dashboard Completo con Merge Automático

```python
from BESTLIB.reactive import ReactiveMatrixLayout
import pandas as pd
import numpy as np

# Datos de ejemplo
np.random.seed(42)
n = 200
df = pd.DataFrame({
    'edad': np.random.randint(22, 65, n),
    'salario': np.random.randint(3000, 20000, n),
    'departamento': np.random.choice(['IT', 'Sales', 'Finance', 'HR'], n),
    'experiencia': np.random.randint(1, 25, n),
    'satisfaccion': np.random.uniform(1, 10, n)
})

# Layout complejo con múltiples regiones fusionadas
# S = Scatter plot grande (3x2)
# B = Bar chart (1x2)
# H = Histogram (1x2)
# P = Boxplot (1x2)
# T = Título (1x2)
layout = ReactiveMatrixLayout("""
SSBB
SSHH
SSPP
TTPP
""")

# Scatter plot principal (3x2 fusionado automáticamente)
layout.add_scatter(
    'S',
    df,
    x_col='edad',
    y_col='salario',
    category_col='departamento',
    interactive=True,
    axes=True,
    pointRadius=4
)

# Bar chart (1x2 fusionado automáticamente)
layout.add_barchart(
    'B',
    category_col='departamento',
    linked_to='S',
    axes=True
)

# Histogram (1x2 fusionado automáticamente)
layout.add_histogram(
    'H',
    column='edad',
    bins=25,
    linked_to='S',
    axes=True
)

# Boxplot (2x2 fusionado automáticamente)
layout.add_boxplot(
    'P',
    column='salario',
    category_col='departamento',
    linked_to='S',
    axes=True
)

# Título (usando map manual)
from BESTLIB.matrix import MatrixLayout
MatrixLayout.map({
    "T": "<div style='background: #f0f0f0; padding: 15px; text-align: center; border-radius: 6px;'>" +
         "<h2 style='margin: 0; color: #333;'>📊 Dashboard Interactivo</h2>" +
         "<p style='margin: 5px 0 0 0; color: #666;'>Selecciona puntos en el scatter plot</p>" +
         "</div>"
})

layout.display()

print("\n✅ Dashboard creado con merge automático!")
print("💡 Las celdas con la misma letra se fusionaron automáticamente")
```

## 📊 Estructura Visual del Layout

```
┌──────────────────┬──────────────┐
│                  │              │
│   Scatter Plot   │  Bar Chart   │
│   (Main)         │              │
│   (3x2)          ├──────────────┤
│                  │              │
│                  │  Histogram   │
│                  ├──────────────┤
│                  │              │
│                  │  Boxplot     │
├──────────────────┴──────────────┤
│     Título          Boxplot      │
│     (1x2)           (continúa)   │
└──────────────────────────────────┘
```

## 🎨 Ventajas del Merge Automático

1. **Simplicidad**: No necesitas especificar `__merge__` para casos comunes
2. **Intuitivo**: El layout ASCII es más claro y directo
3. **Flexible**: Puedes controlar manualmente cuando sea necesario
4. **Compatible**: Funciona con cualquier tipo de gráfico (scatter, bar, histogram, boxplot, etc.)
5. **Consistente**: El mismo algoritmo funciona para todos los tipos de contenido

## 🔧 Comparación: Antes vs Ahora

### ❌ Antes (requería especificar merge manualmente):
```python
MatrixLayout.map({
    "__merge__": ["S", "B", "H"],  # Tenías que especificar
    "S": None,
    "B": None,
    "H": None
})
```

### ✅ Ahora (merge automático):
```python
# No necesitas especificar __merge__ - funciona automáticamente!
MatrixLayout.map({
    "S": None,  # Se fusiona automáticamente
    "B": None,  # Se fusiona automáticamente
    "H": None   # Se fusiona automáticamente
})
```

## 📈 Ejemplo Avanzado: Múltiples Regiones

```python
from BESTLIB.reactive import ReactiveMatrixLayout
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'x': np.random.randn(100),
    'y': np.random.randn(100),
    'cat': np.random.choice(['A', 'B', 'C'], 100)
})

# Layout con múltiples regiones fusionadas automáticamente
layout = ReactiveMatrixLayout("""
SSBB
SSBB
HHHH
""")

# S = Scatter (2x2 fusionado automáticamente)
layout.add_scatter('S', df, x_col='x', y_col='y', interactive=True)

# B = Bar (2x2 fusionado automáticamente)
layout.add_barchart('B', category_col='cat', linked_to='S')

# H = Histogram (1x4 fusionado automáticamente)
layout.add_histogram('H', column='x', bins=15, linked_to='S')

layout.display()
```

## ✅ Verificación

Para verificar que el merge automático funciona:

1. **Inspecciona el HTML**: Las celdas fusionadas tendrán `grid-row` y `grid-column` con `span`
2. **Visual**: Las regiones contiguas con la misma letra aparecen como un solo bloque
3. **Funcionalidad**: Los gráficos se renderizan correctamente en las celdas fusionadas

## 🚀 Ejecución

Este código funciona en:
- ✅ Jupyter Notebook
- ✅ Google Colab
- ✅ VS Code con Jupyter
- ✅ Cualquier entorno que soporte IPython

**No necesitas instalar nada adicional** - el merge automático está activado por defecto.

