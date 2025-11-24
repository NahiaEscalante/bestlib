# 🚀 BESTLIB - Quick Start para Google Colab

## ⚡ Prueba Rápida (5 minutos)

Copia y pega este código en Google Colab para probar TODAS las funcionalidades:

### 📋 Celda 1: Instalación
```python
# Instalar BESTLIB
!pip uninstall -y BESTLIB 2>/dev/null || true
!pip install git+https://github.com/NahiaEscalante/bestlib.git@restore

import BESTLIB
print(f"✅ BESTLIB v{BESTLIB.__version__}")
```

### 📊 Celda 2: Datos de Prueba
```python
import pandas as pd
import numpy as np

np.random.seed(42)

# Dataset sintético (150 muestras)
data = pd.DataFrame({
    'x': np.concatenate([np.random.normal(5, 0.5, 50), 
                         np.random.normal(6, 0.5, 50),
                         np.random.normal(7, 0.5, 50)]),
    'y': np.concatenate([np.random.normal(3, 0.4, 50),
                         np.random.normal(4, 0.3, 50),
                         np.random.normal(5, 0.3, 50)]),
    'category': ['A']*50 + ['B']*50 + ['C']*50
})

print(f"✅ {len(data)} muestras creadas")
data.head()
```

### 🎯 Celda 3: Scatter Interactivo (Test 1)
```python
from BESTLIB import MatrixLayout

# Activar debug
MatrixLayout.set_debug(True)

# Configurar scatter
MatrixLayout.map_scatter(
    'S', data,
    x_col='x', y_col='y', category_col='category',
    interactive=True,  # 🔥 Habilita brush
    axes=True,
    colorMap={'A': '#e74c3c', 'B': '#3498db', 'C': '#2ecc71'}
)

layout = MatrixLayout("SSS")

# Callback para capturar selección
selected = []
def on_select(payload):
    global selected
    selected = payload.get('items', [])
    print(f"📊 {len(selected)} puntos seleccionados")

layout.on('select', on_select)

print("🎯 ARRASTRA el mouse sobre el gráfico para seleccionar")
layout
```

### ✅ Celda 4: Verificar Selección
```python
if selected:
    df = pd.DataFrame(selected)
    print(f"✅ {len(df)} elementos")
    print(df['category'].value_counts())
else:
    print("⚠️ No hay selección. Arrastra en el gráfico.")
```

### 🔗 Celda 5: Linked Views (Test 2)
```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel

# Crear modelo reactivo
sel = SelectionModel()

# Layout con 3 vistas
layout = ReactiveMatrixLayout("""
SSS
BBH
""", selection_model=sel)

layout.set_data(data)

# Scatter (principal)
layout.add_scatter('S', x_col='x', y_col='y', 
                   category_col='category', interactive=True,
                   colorMap={'A': '#e74c3c', 'B': '#3498db', 'C': '#2ecc71'})

# Bar chart (enlazado)
layout.add_barchart('B', category_col='category', linked_to='S',
                    colorMap={'A': '#e74c3c', 'B': '#3498db', 'C': '#2ecc71'})

# Histogram (enlazado)
layout.add_histogram('H', column='x', bins=12, linked_to='S', color='#9b59b6')

print("🔗 Selecciona en SCATTER → Bar e Histogram se actualizan")
layout.display()
```

### 📋 Celda 6: Ver Datos Seleccionados
```python
count = sel.get_count()
items = sel.get_items()

print(f"📊 Seleccionados: {count}")

if items:
    df = pd.DataFrame(items)
    print("\n📈 Distribución:")
    print(df['category'].value_counts())
    print("\n🔢 Estadísticas:")
    print(df[['x', 'y']].describe())
else:
    print("⚠️ No hay selección")
```

### 🎨 Celda 7: Dashboard Completo (Test 3)
```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel

dash_sel = SelectionModel()

dashboard = ReactiveMatrixLayout("""
SSSBBB
SSSHHH
PPPCCC
""", selection_model=dash_sel, gap=12)

dashboard.set_data(data)

# 1. Scatter (principal)
dashboard.add_scatter('S', x_col='x', y_col='y', category_col='category',
                      interactive=True,
                      colorMap={'A': '#e74c3c', 'B': '#3498db', 'C': '#2ecc71'})

# 2. Bar chart (enlazado)
dashboard.add_barchart('B', category_col='category', linked_to='S',
                       colorMap={'A': '#e74c3c', 'B': '#3498db', 'C': '#2ecc71'})

# 3. Histogram (enlazado)
dashboard.add_histogram('H', column='y', bins=10, linked_to='S', color='#f39c12')

# 4. Pie chart (enlazado)
dashboard.add_pie('P', category_col='category', linked_to='S', donut=True,
                  colorMap={'A': '#e74c3c', 'B': '#3498db', 'C': '#2ecc71'})

# 5. Correlation heatmap (solo lectura)
dashboard.add_correlation_heatmap('C', showValues=False)

print("🎨 Dashboard: 5 vistas, 4 sincronizadas")
dashboard.display()
```

### 📊 Celda 8: Bar Chart Interactivo (Test 4)
```python
from BESTLIB import ReactiveMatrixLayout, SelectionModel

bar_sel = SelectionModel()
bar_data = []

layout_bar = ReactiveMatrixLayout("BBB", selection_model=bar_sel)
layout_bar.set_data(data)

# Bar chart como VISTA PRINCIPAL (genera selecciones)
layout_bar.add_barchart('B', category_col='category',
                        interactive=True,  # 🔥 Vista principal
                        selection_var='bar_data',  # 🔥 Guarda en variable
                        colorMap={'A': '#e74c3c', 'B': '#3498db', 'C': '#2ecc71'})

print("📊 Click en una BARRA para seleccionar")
layout_bar.display()
```

### ✅ Celda 9: Verificar Bar Selection
```python
if isinstance(bar_data, pd.DataFrame) and not bar_data.empty:
    print(f"✅ {len(bar_data)} filas seleccionadas")
    print(bar_data['category'].value_counts())
elif bar_data:
    print(f"✅ {len(bar_data)} elementos")
else:
    print("⚠️ Click en una barra del bar chart")
```

### 🔍 Celda 10: Verificar Sistema
```python
status = MatrixLayout.get_status()

print("🔍 Estado del Sistema")
print("="*60)
print(f"✅ Comm: {status['comm_registered']}")
print(f"📊 Instancias: {status['active_instances']}")
print(f"🎯 IDs: {status['instance_ids']}")
print("="*60)

if status['comm_registered']:
    print("\n✅ Sistema funcionando correctamente")
else:
    print("\n⚠️ Registrando comm...")
    MatrixLayout.register_comm(force=True)
```

---

## ✅ Checklist Rápido

Después de ejecutar todas las celdas, verifica:

- [ ] **Celda 1**: BESTLIB instalado ✅
- [ ] **Celda 2**: 150 muestras creadas ✅
- [ ] **Celda 3**: Scatter con brush funciona ✅
- [ ] **Celda 4**: Datos capturados en `selected` ✅
- [ ] **Celda 5**: 3 vistas sincronizadas ✅
- [ ] **Celda 6**: SelectionModel tiene datos ✅
- [ ] **Celda 7**: Dashboard con 5 vistas ✅
- [ ] **Celda 8**: Bar chart interactivo ✅
- [ ] **Celda 9**: Datos en `bar_data` ✅
- [ ] **Celda 10**: Comm registrado ✅

---

## 🎯 Qué Esperar

### Test 1: Scatter Interactivo
1. Aparece scatter plot con puntos de colores
2. Al arrastrar mouse → rectángulo de selección
3. Al soltar → mensaje en consola con cantidad
4. Variable `selected` tiene los datos

### Test 2: Linked Views
1. Aparece layout con 3 gráficos
2. Al seleccionar en scatter (superior):
   - Bar chart (inferior izq) se actualiza
   - Histogram (inferior der) se actualiza
3. **Sin re-ejecutar celdas**

### Test 3: Dashboard
1. Aparece dashboard con 5 visualizaciones
2. Al seleccionar en scatter:
   - 4 vistas se actualizan simultáneamente
   - Heatmap no cambia (solo lectura)

### Test 4: Bar Chart Principal
1. Aparece bar chart con 3 barras
2. Al hacer click en barra:
   - Datos de esa categoría en `bar_data`
   - Como DataFrame si pandas disponible

---

## 🐛 Si Algo Falla

### Los gráficos no se muestran
```python
MatrixLayout.register_comm(force=True)
```

### Las selecciones no funcionan
```python
MatrixLayout.set_debug(True)  # Ver eventos
```

### Error al importar
```python
!pip install --force-reinstall git+https://github.com/NahiaEscalante/bestlib.git@restore
# Luego: Runtime → Restart runtime
```

---

## 💡 Comandos Útiles

```python
# Ver estado
MatrixLayout.get_status()

# Activar debug
MatrixLayout.set_debug(True)

# Ver selección
sel.get_count()
sel.get_items()
sel.get_history()

# Limpiar
sel.clear()
```

---

## 📚 Más Información

- **Tests completos:** `TEST_COLAB.ipynb`
- **Guía detallada:** `INSTRUCCIONES_TEST_COLAB.md`
- **Análisis técnico:** `ANALISIS_BRANCH_RESTORE.md`
- **Resumen:** `RESUMEN_EJECUTIVO.md`

---

## 🎉 ¡Eso es Todo!

Si todas las celdas ejecutan sin errores y puedes seleccionar puntos/barras, **¡tu librería funciona perfectamente!** ✅

**Próximo paso:** Usa los tests completos en `TEST_COLAB.ipynb` para explorar más funcionalidades.
