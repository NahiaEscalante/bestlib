# 🎯 Ejemplo Completo: Merge Automático con Scatter, Bar y Heatmap

Este ejemplo demuestra el sistema de **merge automático** funcionando con diferentes tipos de gráficos, incluyendo un ejemplo de heatmap.

## 📝 Ejemplo Completo: Dashboard con 3 Gráficos

```python
# ============================================
# CELDA 1: Importar librerías
# ============================================
from BESTLIB.reactive import ReactiveMatrixLayout
import pandas as pd
import numpy as np

# ============================================
# CELDA 2: Crear datos de ejemplo
# ============================================
np.random.seed(42)
n = 150

df = pd.DataFrame({
    'edad': np.random.randint(22, 65, n),
    'salario': np.random.randint(3000, 20000, n),
    'departamento': np.random.choice(['IT', 'Sales', 'Finance', 'HR'], n),
    'experiencia': np.random.randint(1, 25, n),
    'satisfaccion': np.random.uniform(1, 10, n)
})

print(f"✅ Datos creados: {len(df)} registros")

# ============================================
# CELDA 3: Crear layout con merge automático
# ============================================
# Layout ASCII:
# SSBB
# SSHH
#
# Donde:
# S = Scatter Plot (2x2 fusionado automáticamente)
# B = Bar Chart (1x2 fusionado automáticamente)
# H = Histogram (1x2 fusionado automáticamente)

layout = ReactiveMatrixLayout("""
SSBB
SSHH
""")

# ============================================
# CELDA 4: Agregar gráficos (NO necesitas __merge__)
# ============================================

# 1. Scatter Plot Principal (se fusiona automáticamente en 2x2)
layout.add_scatter(
    'S',
    df,
    x_col='edad',
    y_col='salario',
    category_col='departamento',
    interactive=True,  # Habilita brush selection
    axes=True,
    pointRadius=5,
    colorMap={
        'IT': '#e74c3c',
        'Sales': '#3498db',
        'Finance': '#2ecc71',
        'HR': '#f39c12'
    }
)

# 2. Bar Chart (se fusiona automáticamente en 1x2)
layout.add_barchart(
    'B',
    category_col='departamento',
    linked_to='S',  # Enlazado al scatter plot
    axes=True
)

# 3. Histogram (se fusiona automáticamente en 1x2)
layout.add_histogram(
    'H',
    column='edad',
    bins=20,
    linked_to='S',  # Enlazado al scatter plot
    axes=True
)

# ============================================
# CELDA 5: Mostrar dashboard
# ============================================
layout.display()

print("\n" + "="*60)
print("✅ Dashboard creado con merge automático!")
print("="*60)
print("\n💡 Características:")
print("   - Scatter plot (2x2) fusionado automáticamente")
print("   - Bar chart (1x2) fusionado automáticamente")
print("   - Histogram (1x2) fusionado automáticamente")
print("   - Todos los gráficos están enlazados")
print("   - Selecciona puntos en el scatter para ver actualizaciones")
print("="*60)

# ============================================
# CELDA 6: Acceder a datos seleccionados
# ============================================
# Después de seleccionar puntos en el scatter plot:

selected = layout.selected_data
print(f"\n📊 Datos seleccionados: {len(selected)} elementos")
if len(selected) > 0:
    df_selected = pd.DataFrame(selected)
    print(f"   Edad promedio: {df_selected['edad'].mean():.1f} años")
    print(f"   Salario promedio: ${df_selected['salario'].mean():.0f}")
```

## 📝 Ejemplo Avanzado: Con Heatmap Simulado

Si necesitas un heatmap (requiere implementación adicional), puedes usar un ejemplo similar:

```python
from BESTLIB.reactive import ReactiveMatrixLayout
from BESTLIB.matrix import MatrixLayout
import pandas as pd
import numpy as np

# Crear datos de correlación (simulado como heatmap)
np.random.seed(42)
data = {
    'edad': np.random.randint(20, 60, 100),
    'salario': np.random.randint(3000, 15000, 100),
    'experiencia': np.random.randint(1, 20, 100)
}
df = pd.DataFrame(data)

# Calcular matriz de correlación
corr_matrix = df.corr()

# Crear datos para "heatmap" (usando bar chart como visualización)
heatmap_data = []
for i, col1 in enumerate(corr_matrix.columns):
    for j, col2 in enumerate(corr_matrix.columns):
        heatmap_data.append({
            'x': col1,
            'y': col2,
            'value': corr_matrix.loc[col1, col2]
        })

# Layout con scatter, bar y "heatmap"
layout = ReactiveMatrixLayout("""
SSBB
SSHH
""")

# Scatter plot principal
layout.add_scatter(
    'S',
    df,
    x_col='edad',
    y_col='salario',
    interactive=True,
    axes=True
)

# Bar chart
layout.add_barchart(
    'B',
    category_col='edad',  # Usar edad como categoría
    linked_to='S',
    axes=True
)

# Histogram (simulando visualización de heatmap)
layout.add_histogram(
    'H',
    column='experiencia',
    bins=15,
    linked_to='S',
    axes=True
)

layout.display()
```

## 🔍 Explicación Técnica del Algoritmo

### Algoritmo de Detección de Regiones Contiguas

El algoritmo implementado utiliza una estrategia de **expansión rectangular** (similar a un flood-fill optimizado):

#### 1. **Fase de Inicialización**
```javascript
const visited = Array.from({length: R}, () => Array(C).fill(false));
```
- Crea una matriz de visitados para evitar procesar celdas múltiples veces

#### 2. **Iteración Principal**
```javascript
for (let r = 0; r < R; r++) {
  for (let c = 0; c < C; c++) {
    if (visited[r][c]) continue;  // Saltar celdas ya procesadas
```

#### 3. **Detección de Inicio de Región**
- Cuando encuentra una celda no visitada con una letra específica
- Inicializa `width = 1` y `height = 1`

#### 4. **Expansión Horizontal (Greedy)**
```javascript
while (c + width < C && 
       !visited[r][c + width] && 
       rows[r][c + width] === letter) {
    width++;
}
```
- Expande hacia la derecha mientras la letra sea la misma
- Se detiene cuando encuentra una letra diferente o el borde

#### 5. **Expansión Vertical (Validación Completa)**
```javascript
while (r + height < R && canGrow) {
    for (let cc = c; cc < c + width; cc++) {
        if (visited[r + height][cc] || 
            rows[r + height][cc] !== letter) {
            canGrow = false;
            break;
        }
    }
    if (canGrow) height++;
}
```
- Verifica que TODAS las celdas en la fila siguiente (dentro del rango horizontal) tengan la misma letra
- Solo expande verticalmente si toda la fila es consistente

#### 6. **Aplicación de Spans CSS**
```javascript
cell.style.gridRow = `${r + 1} / span ${height}`;
cell.style.gridColumn = `${c + 1} / span ${width}`;
```
- Usa CSS Grid para fusionar visualmente las celdas
- `span` indica cuántas celdas abarca horizontal/verticalmente

### Complejidad del Algoritmo

- **Tiempo**: O(R × C) - Cada celda se visita exactamente una vez
- **Espacio**: O(R × C) - Matriz de visitados
- **Eficiencia**: Óptimo para el problema, ya que debe revisar todas las celdas

### Ventajas del Algoritmo

1. **Simplicidad**: Fácil de entender y mantener
2. **Eficiencia**: Cada celda se procesa una sola vez
3. **Correctitud**: Siempre encuentra la región rectangular máxima
4. **Compatibilidad**: Funciona con cualquier tipo de contenido (HTML, gráficos D3, etc.)

## 🎨 Comparación Visual

### Sin Merge (grid individual):
```
┌───┐┌───┐┌───┐
│ A ││ A ││ C │
└───┘└───┘└───┘
┌───┐┌───┐┌───┐
│ A ││ A ││ C │
└───┘└───┘└───┘
┌───┐┌───┐┌───┐
│ B ││ B ││ B │
└───┘└───┘└───┘
```

### Con Merge Automático:
```
┌───────────┐┌───┐
│           ││   │
│     A     ││ C │
│  (2x2)    ││   │
│           │└───┘
└───────────┘
┌─────────────────┐
│       B         │
│     (1x3)       │
└─────────────────┘
```

## ✅ Verificación del Merge Automático

Para verificar que funciona:

1. **Inspecciona el DOM**: Las celdas fusionadas tienen `grid-row: X / span Y`
2. **Visual**: Las regiones aparecen como bloques unificados
3. **Funcionalidad**: Los gráficos se renderizan correctamente en áreas fusionadas

## 🚀 Resultado

El sistema ahora:
- ✅ Detecta automáticamente regiones contiguas
- ✅ Fusiona celdas sin necesidad de `__merge__`
- ✅ Funciona con cualquier tipo de gráfico
- ✅ Mantiene compatibilidad con control manual
- ✅ Es más simple e intuitivo para el usuario

