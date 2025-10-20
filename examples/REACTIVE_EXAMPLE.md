# 🔄 Ejemplo: Variables Reactivas con BESTLIB

Este ejemplo muestra cómo usar variables reactivas que se actualizan automáticamente sin necesidad de re-ejecutar celdas.

## Celda 1: Instalación
```python
!pip install git+https://github.com/NahiaEscalante/bestlib.git@pruebas
!pip install ipywidgets
```

## Celda 2: Configuración Reactiva
```python
from BESTLIB.matrix import MatrixLayout
from BESTLIB.reactive import SelectionModel
import random

# Generar datos
random.seed(42)
scatter_data = [
    {"x": random.uniform(10, 100), "y": random.uniform(10, 100), 
     "category": random.choice(["A", "B", "C"])}
    for _ in range(100)
]

# ⭐ CREAR MODELO REACTIVO
selection = SelectionModel()

# ⭐ REGISTRAR CALLBACKS QUE SE EJECUTAN AUTOMÁTICAMENTE
def on_selection_change(items, count):
    print(f"\n🔄 ACTUALIZACIÓN AUTOMÁTICA!")
    print(f"✅ {count} puntos seleccionados")
    
    if count > 0:
        # Calcular estadísticas automáticamente
        from collections import Counter
        categorias = Counter([p['category'] for p in items])
        
        print("\n📊 Distribución:")
        for cat, c in categorias.items():
            porc = (c / count) * 100
            print(f"   {cat}: {c} ({porc:.1f}%)")
        
        avg_x = sum(p['x'] for p in items) / count
        avg_y = sum(p['y'] for p in items) / count
        print(f"\n📍 Centro: X={avg_x:.1f}, Y={avg_y:.1f}")

# Conectar callback
selection.on_change(on_selection_change)

print("✅ Modelo reactivo configurado")
print("💡 Los callbacks se ejecutarán automáticamente cuando hagas selecciones")
```

## Celda 3: Scatter con Modelo Reactivo
```python
# Crear layout
layout = MatrixLayout("S")

# Configurar scatter
layout.map({
    'S': {
        "type": "scatter",
        "data": scatter_data,
        "colorMap": {"A": "#e74c3c", "B": "#3498db", "C": "#2ecc71"},
        "interactive": True,
        "axes": True,
        "pointRadius": 5
    }
})

# ⭐ CONECTAR MODELO REACTIVO
layout.connect_selection(selection)

# Mostrar
layout.display()

print("\n🖱️ Arrastra el mouse para seleccionar")
print("💡 Los análisis aparecerán automáticamente AQUÍ ARRIBA ☝️")
```

## Celda 4: Acceder a Datos Reactivos (Sin Re-ejecutar)
```python
# ⭐ ESTA CELDA ACCEDE A LOS DATOS REACTIVOS
# No necesitas re-ejecutarla después de cada selección

if selection.get_count() > 0:
    items = selection.get_items()
    
    print(f"📊 Datos actuales: {len(items)} puntos")
    print("\nPrimeros 5:")
    for i, item in enumerate(items[:5], 1):
        print(f"  {i}. x={item['x']:.1f}, y={item['y']:.1f}, cat={item['category']}")
else:
    print("⚠️ No hay selección aún")
```

## Celda 5: Historial de Selecciones
```python
# Ver todas las selecciones que has hecho
history = selection.get_history()

print(f"📜 Historial: {len(history)} selecciones\n")

for i, sel in enumerate(history, 1):
    print(f"{i}. {sel['timestamp']}")
    print(f"   Puntos: {sel['count']}")
    print()
```

## Celda 6: Visualización Automática de Última Selección
```python
# ⭐ ESTA CELDA SE PUEDE EJECUTAR EN CUALQUIER MOMENTO
# Siempre mostrará la última selección

if selection.get_count() > 0:
    items = selection.get_items()
    
    # Crear gráfico de barras automáticamente
    from collections import Counter
    categorias = Counter([p['category'] for p in items])
    
    bar_data = [
        {"category": cat, "value": count}
        for cat, count in categorias.items()
    ]
    
    layout_auto = MatrixLayout("BA")
    layout_auto.map({
        'BA': {
            "type": "bar",
            "data": bar_data,
            "color": "#9b59b6",
            "axes": True,
            "interactive": False
        }
    })
    layout_auto.display()
    
    print(f"✅ Gráfico de {len(items)} puntos seleccionados")
else:
    print("⚠️ Haz una selección primero (Celda 3)")
```

---

## 🎯 Ventajas del Modelo Reactivo

### ✅ **Antes (Método Normal)**
```python
# ❌ Necesitas RE-EJECUTAR esta celda después de cada selección
if datos_seleccionados:
    print(f"Hay {len(datos_seleccionados)} datos")
```

### ✅ **Ahora (Modelo Reactivo)**
```python
# ✅ Se ejecuta AUTOMÁTICAMENTE cuando haces una selección
selection.on_change(lambda items, count: print(f"Auto: {count} puntos"))

# ✅ Puedes acceder a los datos en CUALQUIER momento
items = selection.get_items()  # Siempre actualizado
```

---

## 🔑 Características

1. **Actualización Automática**: Los callbacks se ejecutan sin re-ejecutar celdas
2. **Historial**: Guarda todas las selecciones que hiciste
3. **Acceso Global**: `selection.get_items()` funciona desde cualquier celda
4. **Múltiples Callbacks**: Puedes registrar varios callbacks
5. **Sincronización**: Usa ipywidgets para sincronizar JS ↔ Python

---

## 🧪 Comparación

| Característica | Método Normal | Modelo Reactivo |
|----------------|---------------|-----------------|
| Re-ejecutar celda | ✅ Necesario | ❌ No necesario |
| Callbacks automáticos | ❌ No | ✅ Sí |
| Historial | ❌ No | ✅ Sí |
| Sincronización | Manual | Automática |
| Código | Más simple | Más poderoso |

---

## 💡 Cuándo usar cada uno

**Modelo Normal** (variables globales):
- Para prototipos rápidos
- Cuando no necesitas historial
- Si ipywidgets no está disponible

**Modelo Reactivo**:
- Para análisis interactivos complejos
- Cuando quieres callbacks automáticos
- Para dashboards o apps más sofisticadas
- Cuando necesitas historial de selecciones
