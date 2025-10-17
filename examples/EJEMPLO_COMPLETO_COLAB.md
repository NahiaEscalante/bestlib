# 📊 EJEMPLO COMPLETO - Análisis de Datos con Brush Selection

Este notebook demuestra cómo usar BESTLIB para visualizar datos, hacer selecciones interactivas y analizar los resultados.

---

## 📦 CELDA 1: Instalación

```python
!pip install --upgrade --force-reinstall git+https://github.com/NahiaEscalante/bestlib.git@pruebas
```

---

## 📚 CELDA 2: Imports

```python
from BESTLIB import MatrixLayout
import random
from collections import Counter
```

---

## 🎲 CELDA 3: Generar datos de ejemplo

```python
# Generar 100 puntos aleatorios con 3 categorías
random.seed(42)

datos = []
for i in range(100):
    categoria = random.choice(['Producto A', 'Producto B', 'Producto C'])
    
    # Diferentes rangos según categoría para crear patrones
    if categoria == 'Producto A':
        x = random.randint(10, 40)
        y = random.randint(40, 80)
    elif categoria == 'Producto B':
        x = random.randint(30, 70)
        y = random.randint(20, 60)
    else:
        x = random.randint(50, 90)
        y = random.randint(50, 95)
    
    datos.append({
        'x': x,
        'y': y,
        'category': categoria,
        'id': i
    })

print(f"✅ Generados {len(datos)} puntos de datos")
print(f"📊 Categorías: {', '.join(set(d['category'] for d in datos))}")
```

---

## 💾 CELDA 4: Variable global y callback

```python
# Variable global donde se guardarán los datos seleccionados
datos_seleccionados = []

def guardar_seleccion(payload):
    """Callback que se ejecuta cuando haces una selección con el brush"""
    global datos_seleccionados
    datos_seleccionados = payload.get('items', [])
    print(f"✅ Seleccionados {len(datos_seleccionados)} puntos")

print("✅ Sistema de selección configurado")
```

---

## 📊 CELDA 5: Visualización con Brush Selection

```python
# Crear layout
layout = MatrixLayout()

# Conectar el callback ANTES de mostrar
layout.on('select', guardar_seleccion)

# Configurar el scatter plot
layout.map({
    'S': {
        'type': 'scatter',
        'data': datos,
        'color': '#4a90e2',
        'pointRadius': 5,
        'axes': True,
        'interactive': True  # Habilita el brush
    }
})

print("👆 Arrastra el mouse sobre el gráfico para seleccionar puntos")
layout.display("S")
```

---

## 📈 CELDA 6: Análisis de los datos seleccionados

```python
if datos_seleccionados:
    print("="*70)
    print(f"📊 ANÁLISIS DE {len(datos_seleccionados)} PUNTOS SELECCIONADOS")
    print("="*70)
    
    # 1. Distribución por categoría
    categorias = Counter([p['category'] for p in datos_seleccionados])
    
    print("\n📌 DISTRIBUCIÓN POR CATEGORÍA:")
    for cat, count in categorias.most_common():
        porcentaje = (count / len(datos_seleccionados)) * 100
        barra = "█" * int(porcentaje / 2)
        print(f"  {cat:15} {count:3} puntos ({porcentaje:5.1f}%) {barra}")
    
    # 2. Estadísticas de X e Y
    xs = [p['x'] for p in datos_seleccionados]
    ys = [p['y'] for p in datos_seleccionados]
    
    print("\n📍 ESTADÍSTICAS DE POSICIÓN:")
    print(f"  X: min={min(xs):.1f}, max={max(xs):.1f}, promedio={sum(xs)/len(xs):.1f}")
    print(f"  Y: min={min(ys):.1f}, max={max(ys):.1f}, promedio={sum(ys)/len(ys):.1f}")
    
    # 3. Centro de la selección
    centro_x = sum(xs) / len(xs)
    centro_y = sum(ys) / len(ys)
    print(f"\n🎯 CENTRO DE LA SELECCIÓN: ({centro_x:.1f}, {centro_y:.1f})")
    
else:
    print("⚠️ No hay datos seleccionados")
    print("💡 Vuelve a la celda anterior y arrastra el mouse sobre el gráfico")
```

---

## 🎨 CELDA 7: Visualizar SOLO los puntos seleccionados

```python
if datos_seleccionados:
    layout_filtrado = MatrixLayout()
    
    layout_filtrado.map({
        'F': {
            'type': 'scatter',
            'data': datos_seleccionados,
            'color': '#27ae60',  # Verde
            'pointRadius': 6,
            'axes': True,
            'interactive': False
        }
    })
    
    print(f"🔍 Mostrando solo los {len(datos_seleccionados)} puntos seleccionados")
    layout_filtrado.display("F")
else:
    print("❌ No hay datos para visualizar")
```

---

## 📊 CELDA 8: Gráfico de barras de categorías seleccionadas

```python
if datos_seleccionados:
    # Preparar datos para el bar chart
    categorias = Counter([p['category'] for p in datos_seleccionados])
    
    bar_data = [
        {'category': cat, 'value': count}
        for cat, count in categorias.items()
    ]
    
    layout_bar = MatrixLayout()
    
    layout_bar.map({
        'B': {
            'type': 'bar',
            'data': bar_data,
            'color': '#e74c3c',
            'axes': True
        }
    })
    
    print("📊 Distribución de categorías en la selección:")
    layout_bar.display("B")
else:
    print("❌ No hay datos para el gráfico")
```

---

## 🔢 CELDA 9: Crear dataset filtrado para análisis adicional

```python
if datos_seleccionados:
    # Crear un DataFrame de pandas si lo necesitas
    try:
        import pandas as pd
        
        df_seleccion = pd.DataFrame(datos_seleccionados)
        
        print("✅ DataFrame creado con los datos seleccionados:")
        print(df_seleccion.describe())
        
        print("\n📋 Primeras 10 filas:")
        print(df_seleccion.head(10))
        
    except ImportError:
        print("💡 Instala pandas para análisis avanzado: !pip install pandas")
        print("\nDatos seleccionados (primeros 5):")
        for i, p in enumerate(datos_seleccionados[:5], 1):
            print(f"  {i}. ID={p['id']}, x={p['x']}, y={p['y']}, cat={p['category']}")
else:
    print("❌ No hay datos seleccionados")
```

---

## 💡 CELDA 10: Comparación antes/después

```python
if datos_seleccionados:
    print("="*70)
    print("📊 COMPARACIÓN: DATOS ORIGINALES vs SELECCIONADOS")
    print("="*70)
    
    # Categorías originales
    cat_original = Counter([p['category'] for p in datos])
    cat_seleccion = Counter([p['category'] for p in datos_seleccionados])
    
    print(f"\n{'Categoría':<20} {'Original':<15} {'Selección':<15} {'Cambio %'}")
    print("-"*70)
    
    for cat in cat_original.keys():
        orig = cat_original[cat]
        sel = cat_seleccion.get(cat, 0)
        cambio = ((sel / orig) * 100) if orig > 0 else 0
        
        print(f"{cat:<20} {orig:<15} {sel:<15} {cambio:>6.1f}%")
    
    print("\n" + "="*70)
    print(f"TOTAL: {len(datos)} puntos → {len(datos_seleccionados)} seleccionados " +
          f"({(len(datos_seleccionados)/len(datos)*100):.1f}%)")
    print("="*70)
else:
    print("❌ No hay datos para comparar")
```

---

## 🎯 INSTRUCCIONES DE USO:

1. **Ejecuta las celdas 1-5** en orden para configurar todo
2. En la **Celda 5**, arrastra el mouse sobre el gráfico para seleccionar puntos
3. Cuando sueltes, se guardarán automáticamente en `datos_seleccionados`
4. **Celdas 6-10** te muestran diferentes formas de analizar y visualizar los datos seleccionados
5. Puedes volver a la Celda 5 y hacer una nueva selección cuando quieras

## ✨ CARACTERÍSTICAS:

- ✅ Selección interactiva con brush
- ✅ Análisis estadístico automático
- ✅ Visualizaciones de los datos filtrados
- ✅ Comparación con dataset original
- ✅ Compatible con pandas para análisis avanzado

---

## 💻 PRÓXIMOS PASOS:

Puedes usar `datos_seleccionados` para:
- Exportar a CSV
- Entrenar modelos de ML
- Crear visualizaciones personalizadas
- Análisis estadístico avanzado
- Y mucho más...
