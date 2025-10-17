# 🚀 Inicio Rápido - BESTLIB

## ⚡ Prueba en 2 Minutos

### 1. Abre el notebook demo

```bash
# Desde la carpeta bestlib
jupyter notebook examples/demo_completo.ipynb
```

### 2. O crea un nuevo notebook y copia esto:

```python
# Celda 1: Importar
import sys
sys.path.insert(0, '../BESTLIB')  # Ajusta la ruta según necesites
from matrix import MatrixLayout

print("✅ Importado correctamente")
```

```python
# Celda 2: Gráfico de Barras Interactivo
data = [
    {"category": "Lunes", "value": 120},
    {"category": "Martes", "value": 180},
    {"category": "Miércoles", "value": 150},
    {"category": "Jueves", "value": 200},
    {"category": "Viernes", "value": 170}
]

MatrixLayout.map({
    'B': {
        "type": "bar",
        "data": data,
        "color": "#4a90e2",
        "interactive": True  # ← ¡Esto habilita la selección!
    }
})

layout = MatrixLayout("BBB")

# Variable para guardar selección
selected = []

# Callback que se ejecuta cuando seleccionas barras
def on_select(payload):
    global selected
    selected = payload.get('items', [])
    print(f"\n🎯 Seleccionaste {len(selected)} barras:")
    for item in selected:
        print(f"  • {item['category']}: {item['value']}")

layout.on('select', on_select)
layout
```

```python
# Celda 3: Usar los datos seleccionados
import pandas as pd

if selected:
    df = pd.DataFrame(selected)
    print("📊 Datos seleccionados:\n")
    print(df)
    print(f"\n💰 Total: {df['value'].sum()}")
    print(f"📈 Promedio: {df['value'].mean():.2f}")
else:
    print("⚠️ Selecciona algunas barras arrastrando el mouse en el gráfico arriba")
```

### 3. Interactúa

1. **Mira el gráfico de barras** que apareció
2. **Arrastra el mouse** sobre las barras para seleccionar un rango
3. **Observa** cómo se imprime la información en tiempo real
4. **Ejecuta la Celda 3** para ver los datos en un DataFrame

## 🎨 Ejemplos Rápidos

### Círculo Simple

```python
MatrixLayout.map({
    'C': {
        'shape': 'circle',
        'color': '#e74c3c',
        'size': 50,
        'title': '¡Círculo!'
    }
})

MatrixLayout("C")
```

### Scatter Plot con Clicks

```python
import random

data = [
    {
        "x": random.randint(0, 100),
        "y": random.randint(0, 100),
        "label": f"Punto {i+1}"
    }
    for i in range(15)
]

MatrixLayout.map({
    'S': {
        "type": "scatter",
        "data": data,
        "interactive": True,
        "zoom": True  # ← Prueba la rueda del mouse!
    }
})

layout = MatrixLayout("SSS")

layout.on('point_click', lambda p: print(f"Clickeaste: {p['point']['label']}"))

layout
```

### Dashboard Completo

```python
MatrixLayout.map({
    'T': '<h2 style="text-align:center; background: #667eea; color: white; padding: 10px; border-radius: 8px;">📊 Mi Dashboard</h2>',
    'B': {
        "type": "bar",
        "data": [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
            {"category": "C", "value": 15}
        ],
        "color": "#667eea",
        "interactive": True
    },
    'C': {
        'shape': 'circle',
        'color': '#2ecc71',
        'size': 40,
        'title': 'Estado: OK'
    },
    '__merge__': True
})

dashboard = MatrixLayout("""
TTTTTT
BBBBB.
BBBBB.
C.....
""")

dashboard.on('select', lambda p: print(f"✅ {len(p['items'])} elementos seleccionados"))

dashboard
```

## 🐛 Si algo no funciona

### Activar Debug

```python
MatrixLayout.set_debug(True)

# Ahora verás mensajes como:
# 🐛 [MatrixLayout] Modo debug activado
# 📩 [MatrixLayout] Evento recibido: select
# ✓ Usando handler de instancia
```

### Ver Estado

```python
status = MatrixLayout.get_status()
print(status)

# Deberías ver:
# {
#   'comm_registered': True,  ← Debe ser True
#   'active_instances': 1,
#   'instance_ids': ['matrix-...'],
#   'global_handlers': []
# }
```

### Problema: "Comm no registrado"

```python
# Forzar registro
MatrixLayout.register_comm(force=True)
```

### Problema: "Los datos no se capturan"

```python
# Asegúrate de usar una variable GLOBAL
selected = []  # ← Fuera de la función

def on_select(payload):
    global selected  # ← ¡Importante!
    selected = payload['items']

layout.on('select', on_select)
```

## 📖 Siguientes Pasos

1. **Abre** `examples/demo_completo.ipynb` para ver TODOS los ejemplos
2. **Lee** `docs/QUICK_REFERENCE.md` para referencia rápida
3. **Consulta** `docs/README.md` para documentación completa
4. **Experimenta** creando tus propios dashboards!

## 💡 Tips

### Tip 1: Encadenar Callbacks
```python
layout.on('select', callback1)\
      .on('point_click', callback2)
```

### Tip 2: Múltiples Layouts
```python
layout1 = MatrixLayout("AAA")
layout2 = MatrixLayout("BBB")

# Cada uno puede tener sus propios callbacks
layout1.on('select', handler1)
layout2.on('select', handler2)
```

### Tip 3: Callback Global
```python
# Para TODOS los layouts sin callback específico
MatrixLayout.on_global('select', lambda p: print("Global:", p))
```

## 🎯 Conceptos Clave

1. **`MatrixLayout.map()`** = Configurar qué va en cada celda
2. **`MatrixLayout("AAA")`** = Crear el layout con ASCII art
3. **`.on('evento', callback)`** = Capturar interacciones
4. **`interactive: True`** = Habilitar selección en gráficos
5. **Variables globales** = Guardar datos entre celdas

## ✅ Checklist

- [ ] Importé BESTLIB correctamente
- [ ] Vi un gráfico renderizado
- [ ] Interactué con un gráfico (click o arrastrar)
- [ ] Vi mensajes en la consola al interactuar
- [ ] Accedí a los datos seleccionados en otra celda

**Si marcaste todos ✅ ¡Estás listo! 🎉**

---

## 🆘 Ayuda Rápida

| Quiero... | Código |
|-----------|--------|
| Ver círculo | `{'shape': 'circle', 'color': '#e74c3c'}` |
| Ver barras | `{"type": "bar", "data": [...]}` |
| Ver scatter | `{"type": "scatter", "data": [...]}` |
| Seleccionar datos | `"interactive": True` |
| Capturar selección | `layout.on('select', callback)` |
| Ver mensajes debug | `MatrixLayout.set_debug(True)` |
| Hacer zoom | `"zoom": True` (scatter only) |

---

**¡Diviértete creando visualizaciones interactivas! 🚀**
