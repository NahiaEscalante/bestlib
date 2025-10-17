# 🎯 Demo: Brush Selection (Barrido) - Usar Datos en Otra Celda

## 📝 Ejemplo Completo en Colab

### Celda 1: Instalación
```python
!pip install git+https://github.com/NahiaEscalante/bestlib.git@pruebas
```

### Celda 2: Importar
```python
from BESTLIB.matrix import MatrixLayout
```

### Celda 3: Variable Global para Guardar Selección
```python
# Variable global para almacenar datos seleccionados
datos_seleccionados = []

def guardar_seleccion(payload):
    global datos_seleccionados
    items = payload.get('items', [])
    datos_seleccionados = items
    print(f"✅ {len(items)} elementos seleccionados y guardados!")
    for item in items[:5]:  # Mostrar primeros 5
        if 'category' in item:
            print(f"   {item['category']}: {item['value']}")
        else:
            print(f"   ({item['x']:.1f}, {item['y']:.1f})")
```

### Celda 4: Gráfico de Barras con Brush
```python
# Datos
ventas = [
    {"category": "Ene", "value": 150},
    {"category": "Feb", "value": 230},
    {"category": "Mar", "value": 180},
    {"category": "Abr", "value": 290},
    {"category": "May", "value": 220},
    {"category": "Jun", "value": 310},
    {"category": "Jul", "value": 270},
]

# Configurar gráfico
MatrixLayout.map({
    'B': {
        "type": "bar",
        "data": ventas,
        "color": "#4a90e2",
        "interactive": True,  # ← IMPORTANTE: Activa brush
        "axes": True
    }
})

# Crear y mostrar
layout_bar = MatrixLayout("B")
layout_bar.on('select', guardar_seleccion)  # ← Conecta con la función
layout_bar.display()

print("\n💡 Instrucciones:")
print("1. Arrastra el mouse sobre las barras para seleccionar")
print("2. Los datos se guardarán en 'datos_seleccionados'")
```

### Celda 5: Usar los Datos Seleccionados
```python
# Usar datos seleccionados en otra celda
if datos_seleccionados:
    print(f"\n📊 Analizando {len(datos_seleccionados)} elementos seleccionados:\n")
    
    # Calcular estadísticas
    valores = [item['value'] for item in datos_seleccionados]
    categorias = [item['category'] for item in datos_seleccionados]
    
    print(f"Categorías: {', '.join(categorias)}")
    print(f"Suma total: {sum(valores)}")
    print(f"Promedio: {sum(valores)/len(valores):.2f}")
    print(f"Máximo: {max(valores)} ({categorias[valores.index(max(valores))]})")
    print(f"Mínimo: {min(valores)} ({categorias[valores.index(min(valores))]})")
    
    # Crear nuevo gráfico solo con seleccionados
    MatrixLayout.map({
        'F': {
            "type": "bar",
            "data": datos_seleccionados,
            "color": "#e74c3c",  # Color diferente
            "axes": True
        }
    })
    
    print("\n📈 Nuevo gráfico con solo los datos seleccionados:")
    MatrixLayout("F").display()
else:
    print("⚠️ No hay datos seleccionados aún. Ejecuta la celda 4 y arrastra sobre las barras.")
```

### Celda 6: Scatter Plot con Brush
```python
import random
random.seed(42)

# Generar datos
scatter_data = [
    {
        "x": random.uniform(10, 100),
        "y": random.uniform(10, 100),
        "category": random.choice(["A", "B", "C"])
    }
    for _ in range(40)
]

# Variable para guardar puntos seleccionados
puntos_seleccionados = []

def guardar_puntos(payload):
    global puntos_seleccionados
    items = payload.get('items', [])
    puntos_seleccionados = items
    count = payload.get('count', len(items))
    print(f"✅ {count} puntos seleccionados!")

# Configurar scatter
MatrixLayout.map({
    'S': {
        "type": "scatter",
        "data": scatter_data,
        "colorMap": {
            "A": "#e74c3c",
            "B": "#3498db",
            "C": "#2ecc71"
        },
        "interactive": True,  # ← Activa brush
        "axes": True
    }
})

layout_scatter = MatrixLayout("S")
layout_scatter.on('select', guardar_puntos)
layout_scatter.display()

print("\n💡 Arrastra para seleccionar múltiples puntos")
```

### Celda 7: Analizar Puntos Seleccionados
```python
if puntos_seleccionados:
    print(f"\n📊 {len(puntos_seleccionados)} puntos seleccionados:\n")
    
    # Agrupar por categoría
    from collections import Counter
    categorias_count = Counter([p['category'] for p in puntos_seleccionados])
    
    print("Distribución por categoría:")
    for cat, count in categorias_count.items():
        print(f"  {cat}: {count} puntos")
    
    # Promedios
    avg_x = sum(p['x'] for p in puntos_seleccionados) / len(puntos_seleccionados)
    avg_y = sum(p['y'] for p in puntos_seleccionados) / len(puntos_seleccionados)
    
    print(f"\nCentro de la selección:")
    print(f"  X promedio: {avg_x:.2f}")
    print(f"  Y promedio: {avg_y:.2f}")
else:
    print("⚠️ No hay puntos seleccionados")
```

---

## 🎓 Cómo Funciona

1. **Brush (Barrido)**: Arrastras el mouse sobre el gráfico para crear un área de selección
2. **Evento `select`**: Cuando sueltas, se envía un evento a Python con los datos
3. **Variable Global**: Guardas los datos en una variable (`datos_seleccionados`)
4. **Reutilización**: Usas esa variable en celdas posteriores

## 🔑 Puntos Clave

- `"interactive": True` → Activa el brush
- `.on('select', función)` → Conecta el evento con tu función
- Variable global → Permite compartir datos entre celdas
- `payload['items']` → Lista de elementos seleccionados

---

**¡Ahora puedes seleccionar datos y usarlos en análisis posteriores!** 🎉
