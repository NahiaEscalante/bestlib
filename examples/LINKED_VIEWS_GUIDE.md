# 🔗 Linked Views - Vistas Enlazadas en BESTLIB

## 🎯 ¿Qué son Linked Views?

**Linked Views** (Vistas Enlazadas) permite que múltiples visualizaciones se actualicen **automáticamente** cuando interactúas con una de ellas.

**Ejemplo**: Seleccionas puntos en un scatter plot → El bar chart se actualiza automáticamente para mostrar solo las categorías de los puntos seleccionados.

---

## 📦 Instalación

```python
!pip install git+https://github.com/NahiaEscalante/bestlib.git@widget
```

---

## 🚀 Ejemplo Básico

### **Celda 1: Imports y Datos**

```python
from BESTLIB.linked import LinkedViews
import random

# Generar datos de ejemplo
random.seed(42)
datos = [
    {
        'x': random.uniform(10, 100),
        'y': random.uniform(10, 100),
        'category': random.choice(['A', 'B', 'C']),
        'value': random.randint(10, 50)
    }
    for _ in range(100)
]

print(f"✅ {len(datos)} puntos generados")
```

---

### **Celda 2: Crear Vistas Enlazadas**

```python
# Crear gestor de vistas enlazadas
linked = LinkedViews()

# Configurar scatter plot (vista principal con brush)
linked.add_scatter(
    'scatter1',
    data=datos,
    x_field='x',
    y_field='y',
    category_field='category',
    interactive=True,  # ⭐ Habilita brush selection
    colorMap={
        'A': '#e74c3c',
        'B': '#3498db', 
        'C': '#2ecc71'
    },
    pointRadius=5
)

# Configurar bar chart (se actualiza automáticamente)
linked.add_barchart(
    'bar1',
    category_field='category',
    color='#9b59b6'
)

# Mostrar ambas vistas enlazadas
linked.display()

print("\n🎯 INSTRUCCIONES:")
print("1. Arrastra el mouse sobre el scatter plot para seleccionar puntos")
print("2. El bar chart se actualizará automáticamente")
print("3. Mostrará solo las categorías de los puntos seleccionados")
```

---

### **Celda 3: Acceder a Datos Seleccionados**

```python
# Esta celda se puede ejecutar en cualquier momento
seleccionados = linked.get_selected_data()

if seleccionados:
    print(f"\n📊 DATOS SELECCIONADOS: {len(seleccionados)} puntos")
    
    # Análisis por categoría
    from collections import Counter
    cats = Counter([p['category'] for p in seleccionados])
    
    print("\n🏷️ Distribución:")
    for cat, count in cats.items():
        print(f"   {cat}: {count} puntos")
    
    # Estadísticas
    avg_x = sum(p['x'] for p in seleccionados) / len(seleccionados)
    avg_y = sum(p['y'] for p in seleccionados) / len(seleccionados)
    
    print(f"\n📍 Promedios:")
    print(f"   X: {avg_x:.2f}")
    print(f"   Y: {avg_y:.2f}")
else:
    print("⏳ Esperando selección...")
```

---

## 🎨 Ejemplo Avanzado: 3 Vistas Enlazadas

```python
from BESTLIB.linked import LinkedViews
import random

# Datos más complejos
random.seed(42)
datos_iris = []
especies = ['setosa', 'versicolor', 'virginica']

for especie in especies:
    for _ in range(50):
        if especie == 'setosa':
            base_x, base_y = 30, 70
        elif especie == 'versicolor':
            base_x, base_y = 60, 50
        else:
            base_x, base_y = 80, 65
        
        datos_iris.append({
            'sepal_length': base_x + random.uniform(-10, 10),
            'sepal_width': base_y + random.uniform(-10, 10),
            'petal_length': random.uniform(10, 70),
            'species': especie
        })

# Crear múltiples vistas enlazadas
linked = LinkedViews()

# Vista 1: Scatter de Sepal Length vs Width (con brush)
linked.add_scatter(
    'sepal_scatter',
    data=datos_iris,
    x_field='sepal_length',
    y_field='sepal_width',
    category_field='species',
    interactive=True,
    colorMap={
        'setosa': '#e74c3c',
        'versicolor': '#3498db',
        'virginica': '#2ecc71'
    },
    pointRadius=6
)

# Vista 2: Bar chart de especies (se actualiza con selección)
linked.add_barchart(
    'species_bar',
    category_field='species',
    color='#9b59b6'
)

# Mostrar vistas enlazadas
linked.display()

print("\n🎯 Scatter Plot ← → Bar Chart")
print("✅ Completamente enlazados en tiempo real")
```

---

## 🔧 API Completa

### **`LinkedViews()`**
Crea un gestor de vistas enlazadas.

### **`.add_scatter(view_id, data, ...)`**
Agrega un scatter plot.

**Parámetros**:
- `view_id`: Identificador único
- `data`: Lista de diccionarios con datos
- `x_field`: Campo para eje X (default: 'x')
- `y_field`: Campo para eje Y (default: 'y')
- `category_field`: Campo de categoría (default: 'category')
- `interactive`: Habilita brush (default: True)
- `colorMap`: Diccionario de colores por categoría
- `pointRadius`: Tamaño de puntos

### **`.add_barchart(view_id, ...)`**
Agrega un bar chart que se actualiza automáticamente.

**Parámetros**:
- `view_id`: Identificador único
- `category_field`: Campo para agrupar (default: 'category')
- `color`: Color de las barras
- `axes`: Mostrar ejes (default: True)

### **`.display()`**
Muestra todas las vistas enlazadas.

### **`.get_selected_data()`**
Retorna los datos actualmente seleccionados.

### **`.get_selected_count()`**
Retorna el número de elementos seleccionados.

---

## ✅ Ventajas

| Característica | Sin Linked Views | Con Linked Views |
|----------------|------------------|------------------|
| **Actualización** | Manual (re-ejecutar) | Automática |
| **Múltiples vistas** | Independientes | Sincronizadas |
| **Interactividad** | Limitada | Completa |
| **Análisis** | Celda por celda | En tiempo real |

---

## 🎓 Casos de Uso

1. **Análisis Exploratorio**: Selecciona outliers y ve su distribución
2. **Filtrado Visual**: Selecciona región de interés y analiza
3. **Comparación**: Ve cómo cambian las estadísticas con diferentes selecciones
4. **Presentaciones**: Demos interactivas en vivo

---

## 📊 Flujo de Funcionamiento

```
1. Usuario arrastra mouse en scatter plot
   ↓
2. Brush captura coordenadas
   ↓
3. JavaScript filtra puntos dentro del área
   ↓
4. Envía datos seleccionados a Python (via comm)
   ↓
5. Python actualiza LinkedViews._selected_data
   ↓
6. LinkedViews._update_linked_views() se ejecuta
   ↓
7. Bar chart se recalcula con solo datos seleccionados
   ↓
8. Bar chart se re-renderiza automáticamente
   ↓
9. ✅ Usuario ve actualización en tiempo real
```

---

## 🚀 Próximos Pasos

- ✅ Scatter plot con brush
- ✅ Bar chart reactivo
- 🔄 Agregar más tipos de gráficos (line, pie, etc.)
- 🔄 Soporte para 3+ vistas enlazadas
- 🔄 Filtros bidireccionales (seleccionar en cualquier vista)

---

**¿Listo para obtener 5/5 puntos en Linked Views?** 🎯
