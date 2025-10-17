# CELDAS COMPLETAS PARA COLAB - CON DEBUG

## Celda 1: Instalación
```python
!pip install --upgrade --force-reinstall git+https://github.com/NahiaEscalante/bestlib.git@pruebas
```

## Celda 2: Import y activar DEBUG
```python
from BESTLIB import MatrixLayout
import random

# 🔍 ACTIVAR DEBUG PARA VER QUÉ PASA
MatrixLayout.set_debug(True)

# Forzar registro del comm
print("Registrando comunicación...")
resultado = MatrixLayout.register_comm(force=True)
print(f"Registro exitoso: {resultado}")
```

## Celda 3: Datos de prueba
```python
# Generar datos aleatorios
random.seed(42)
datos = [
    {'x': random.randint(5, 95), 'y': random.randint(5, 95), 
     'category': random.choice(['A', 'B', 'C'])}
    for _ in range(50)
]

print(f"Datos generados: {len(datos)} puntos")
print("Primeros 3:", datos[:3])
```

## Celda 4: Variable global para guardar selección
```python
# Variable global donde se guardarán los datos seleccionados
datos_seleccionados = []

def guardar_seleccion(payload):
    """Esta función se ejecuta cuando haces una selección en el brush"""
    global datos_seleccionados
    datos_seleccionados = payload.get('items', [])
    
    print("\n" + "="*60)
    print(f"🎯 SELECCIÓN RECIBIDA: {len(datos_seleccionados)} puntos")
    print("="*60)
    
    if datos_seleccionados:
        print("\nPrimeros 3 puntos seleccionados:")
        for i, punto in enumerate(datos_seleccionados[:3], 1):
            print(f"  {i}. x={punto['x']}, y={punto['y']}, categoría={punto['category']}")
    else:
        print("⚠️ No hay puntos en la selección")

print("✓ Función guardar_seleccion definida")
```

## Celda 5: Scatter plot con BRUSH (INTERACTIVO)
```python
layout_scatter = MatrixLayout()

# Conectar el evento ANTES de display
layout_scatter.on('select', guardar_seleccion)

layout_scatter.map({
    'S': {
        'type': 'scatter',
        'data': datos,
        'color': '#4a90e2',
        'pointRadius': 4,
        'axes': True,
        'interactive': True  # Habilita el brush
    }
})

print("\n📊 Haz una selección arrastrando el mouse sobre el gráfico")
print("Cuando sueltes, verás los datos seleccionados aquí abajo")
print("-" * 60)

layout_scatter.display("S")
```

## Celda 6: Verificar que se guardaron los datos
```python
if datos_seleccionados:
    print(f"\n✅ HAY {len(datos_seleccionados)} PUNTOS SELECCIONADOS")
    print("\nTODOS los puntos seleccionados:")
    for i, p in enumerate(datos_seleccionados, 1):
        print(f"{i}. x={p['x']:.1f}, y={p['y']:.1f}, cat={p['category']}")
else:
    print("❌ No hay datos seleccionados todavía")
    print("💡 Vuelve a la celda anterior y haz una selección con el mouse")
```

## Celda 7: Análisis de los datos seleccionados
```python
if datos_seleccionados:
    print(f"\n📊 ANÁLISIS DE {len(datos_seleccionados)} PUNTOS SELECCIONADOS")
    print("="*60)
    
    # Agrupar por categoría
    from collections import Counter
    categorias_count = Counter([p['category'] for p in datos_seleccionados])
    
    print("\n📌 Distribución por categoría:")
    for cat, count in categorias_count.items():
        porcentaje = (count / len(datos_seleccionados)) * 100
        print(f"   {cat}: {count} puntos ({porcentaje:.1f}%)")
    
    # Calcular promedios
    avg_x = sum([p['x'] for p in datos_seleccionados]) / len(datos_seleccionados)
    avg_y = sum([p['y'] for p in datos_seleccionados]) / len(datos_seleccionados)
    
    print(f"\n📍 Centro de la selección:")
    print(f"   X promedio: {avg_x:.2f}")
    print(f"   Y promedio: {avg_y:.2f}")
    
    # Rangos
    xs = [p['x'] for p in datos_seleccionados]
    ys = [p['y'] for p in datos_seleccionados]
    
    print(f"\n📏 Rangos:")
    print(f"   X: {min(xs):.1f} - {max(xs):.1f}")
    print(f"   Y: {min(ys):.1f} - {max(ys):.1f}")
else:
    print("❌ No hay datos para analizar")
```

## Celda 8: Visualizar SOLO los datos seleccionados
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
            'interactive': False  # No necesita brush
        }
    })
    
    print(f"\n🔍 Visualizando {len(datos_seleccionados)} puntos seleccionados")
    layout_filtrado.display("F")
else:
    print("❌ No hay datos seleccionados para visualizar")
```

## INSTRUCCIONES DE USO:

1. Ejecuta las celdas en orden (1 → 8)
2. En la **Celda 5**: Arrastra el mouse sobre el gráfico para hacer una selección
3. Cuando sueltes el mouse, verás mensajes de debug en la consola
4. La **Celda 6** mostrará los datos guardados
5. Las **Celdas 7-8** harán análisis y visualización

## SOLUCIÓN DE PROBLEMAS:

Si no funciona:
1. Abre la consola del navegador (F12 → Console)
2. Busca mensajes que empiecen con:
   - "Brush ended - selected items:"
   - "sendEvent called:"
   - "📩 [MatrixLayout] Evento recibido:"
3. Revisa si hay errores en rojo
