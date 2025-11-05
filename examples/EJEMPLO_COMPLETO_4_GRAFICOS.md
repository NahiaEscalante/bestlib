# 🎯 Ejemplo Completo: 4 Gráficos Interactivos con Merge

Este ejemplo muestra cómo usar `__merge__` correctamente y crear un dashboard interactivo con:
- ✅ 1 Scatter Plot principal (main)
- ✅ 3 Gráficos secundarios enlazados (Bar Chart, Histogram, Boxplot)
- ✅ Sistema de merge funcionando correctamente
- ✅ Sincronización automática Python ↔ D3.js

## 🔧 Solución al Error de Sintaxis con `__merge__`

**Problema común:** El error `SyntaxError: invalid syntax` con `'__merge__': True` generalmente ocurre por:

1. **Comillas dentro de comillas:** Si usas comillas simples dentro de comillas simples
2. **Indentación incorrecta:** En algunos contextos de Python
3. **Uso incorrecto del diccionario:** El diccionario debe estar correctamente formado

**Solución:** Usar comillas dobles para las claves del diccionario y comillas simples para valores HTML, o viceversa.

## 📝 Ejemplo Completo: Dashboard Interactivo

```python
# ============================================
# CELDA 1: Importar librerías
# ============================================
from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel
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
    'departamento': np.random.choice(['IT', 'Sales', 'Finance', 'HR', 'Marketing'], n),
    'experiencia': np.random.randint(1, 25, n),
    'satisfaccion': np.random.uniform(1, 10, n)
})

print(f"✅ Datos creados: {len(df)} registros")
print(df.head())

# ============================================
# CELDA 3: Crear layout con merge y 4 gráficos
# ============================================
# Layout: Scatter (2x2), Bar (1x2), Histogram (1x2), Boxplot (1x2)
# Layout ASCII:
# SSBB
# SSHH
# XXPP
#
# Donde:
# S = Scatter Plot (principal, 2x2 fusionado)
# B = Bar Chart (1x2 fusionado)
# H = Histogram (1x2 fusionado)  
# X = Espacio vacío o título
# P = Boxplot (1x2 fusionado)

layout = ReactiveMatrixLayout("""
SSBB
SSHH
XXPP
""")

# ============================================
# CELDA 4: Configurar merge (CORRECTO)
# ============================================
# IMPORTANTE: Usar comillas dobles para las claves del diccionario
# y comillas simples para valores HTML, o viceversa consistentemente

from BESTLIB.matrix import MatrixLayout

# Configurar merge para fusionar celdas S, B, H, P
# NOTA: Usa comillas dobles para la clave '__merge__' y comillas simples para valores HTML
MatrixLayout.map({
    "__merge__": ["S", "B", "H", "P"],  # Fusionar estas letras
    "S": None,  # Se configurará con add_scatter
    "B": None,  # Se configurará con add_barchart
    "H": None,  # Se configurará con add_histogram
    "P": None,  # Se configurará con add_boxplot
    "X": "<div style='background: #f5f5f5; padding: 15px; text-align: center; border-radius: 6px;'>" +
         "<h3 style='margin: 0; color: #333;'>📊 Dashboard Interactivo</h3>" +
         "<p style='margin: 5px 0 0 0; color: #666; font-size: 12px;'>Selecciona puntos en el scatter plot</p>" +
         "</div>"
})

# ============================================
# CELDA 5: Agregar gráficos enlazados
# ============================================

# 1. Scatter Plot Principal (MAIN) - con brush selection
layout.add_scatter(
    'S',
    df,
    x_col='edad',
    y_col='salario',
    category_col='departamento',
    interactive=True,  # Habilita brush selection
    axes=True,
    pointRadius=5
)

# 2. Bar Chart enlazado (se actualiza automáticamente)
layout.add_barchart(
    'B',
    category_col='departamento',
    linked_to='S',  # Enlazado al scatter plot 'S'
    axes=True
)

# 3. Histograma enlazado (se actualiza automáticamente)
layout.add_histogram(
    'H',
    column='edad',
    bins=20,
    linked_to='S',  # Enlazado al scatter plot 'S'
    axes=True
)

# 4. Boxplot enlazado (se actualiza automáticamente)
layout.add_boxplot(
    'P',
    column='salario',
    category_col='departamento',
    linked_to='S',  # Enlazado al scatter plot 'S'
    axes=True
)

# ============================================
# CELDA 6: Mostrar el dashboard
# ============================================
layout.display()

print("\n" + "="*60)
print("✅ Dashboard creado exitosamente!")
print("="*60)
print("\n💡 Instrucciones:")
print("   1. Arrastra el mouse en el scatter plot para seleccionar puntos")
print("   2. Los otros 3 gráficos se actualizarán automáticamente")
print("   3. Los datos seleccionados están disponibles en layout.selected_data")
print("="*60)

# ============================================
# CELDA 7: Monitorear selección en tiempo real
# ============================================
# Crear callback para monitorear cambios
def on_selection_change(items, count):
    if count > 0:
        print(f"\n✅ {count} elementos seleccionados")
        df_selected = pd.DataFrame(items)
        print(f"   Edad promedio: {df_selected['edad'].mean():.1f} años")
        print(f"   Salario promedio: ${df_selected['salario'].mean():.0f}")
        print(f"   Departamentos: {dict(df_selected['departamento'].value_counts())}")

# Registrar callback
layout.selection_model.on_change(on_selection_change)

# ============================================
# CELDA 8: Acceder a datos seleccionados
# ============================================
# Después de seleccionar puntos en el scatter plot, puedes acceder a los datos:

# Opción 1: Usar la propiedad selected_data
selected = layout.selected_data
print(f"\n📊 Datos seleccionados disponibles: {len(selected)} elementos")

# Opción 2: Usar el selection_model directamente
selected_items = layout.selection_model.get_items()
selected_count = layout.selection_model.get_count()

print(f"   Count: {selected_count}")
print(f"   Items: {len(selected_items)}")

# Si hay datos seleccionados, mostrar estadísticas
if selected_count > 0:
    df_selected = pd.DataFrame(selected_items)
    print(f"\n📈 Estadísticas de los datos seleccionados:")
    print(df_selected.describe())
```

## 🔍 Explicación del Error de Sintaxis

**Causa del error:**
El error `SyntaxError: invalid syntax` con `'__merge__': True` generalmente ocurre cuando:

1. **Conflicto de comillas:** Si intentas algo como:
   ```python
   MatrixLayout.map({
       '__merge__': True,  # Esto puede fallar si hay comillas mal anidadas
       'A': "<div style='color: blue'>"  # Comillas simples dentro de comillas simples
   })
   ```

2. **Solución correcta:**
   ```python
   # Opción 1: Usar comillas dobles para claves, simples para valores HTML
   MatrixLayout.map({
       "__merge__": ["S", "B"],  # Comillas dobles
       "A": "<div style='color: blue'>"  # Comillas simples en HTML
   })
   
   # Opción 2: Usar comillas simples consistentemente pero escapar HTML
   MatrixLayout.map({
       '__merge__': ['S', 'B'],  # Comillas simples
       'A': '<div style="color: blue">'  # Comillas dobles en HTML
   })
   ```

## 📊 Estructura del Layout

```
┌─────────────────┬─────────────┐
│                 │             │
│   Scatter       │  Bar Chart  │
│   Plot          │             │
│   (Main)        │             │
│   (2x2)         ├─────────────┤
│                 │             │
│                 │  Histogram  │
├─────────────────┴─────────────┤
│     Título / Espacio          │
├───────────────────────────────┤
│         Boxplot               │
│         (1x2)                 │
└───────────────────────────────┘
```

## ✅ Verificación de Funcionamiento

1. **Merge funcionando:** Las celdas S, B, H, P deben aparecer fusionadas
2. **Scatter plot interactivo:** Debe permitir brush selection
3. **Gráficos enlazados:** Bar, Histogram y Boxplot deben actualizarse automáticamente
4. **selected_data disponible:** `layout.selected_data` debe contener los datos seleccionados

## 🎨 Personalización Adicional

### Cambiar colores del scatter plot:
```python
layout.add_scatter(
    'S',
    df,
    x_col='edad',
    y_col='salario',
    category_col='departamento',
    interactive=True,
    colorMap={
        'IT': '#e74c3c',
        'Sales': '#3498db',
        'Finance': '#2ecc71',
        'HR': '#f39c12',
        'Marketing': '#9b59b6'
    }
)
```

### Ajustar número de bins del histograma:
```python
layout.add_histogram(
    'H',
    column='edad',
    bins=30,  # Más bins para mayor detalle
    linked_to='S'
)
```

### Boxplot por categoría:
```python
layout.add_boxplot(
    'P',
    column='salario',
    category_col='departamento',  # Boxplot separado por departamento
    linked_to='S'
)
```

## 🚀 Ejecución en Google Colab

Para ejecutar en Colab, agrega esta celda al inicio:

```python
!pip install git+https://github.com/NahiaEscalante/bestlib.git@pruebas
```

Luego ejecuta todas las celdas en orden.

## 📝 Notas Importantes

1. **Orden de ejecución:** Debe ejecutarse en el orden mostrado (celda por celda)
2. **Merge:** El merge se aplica automáticamente cuando las celdas tienen la misma letra
3. **Enlazamiento:** Todos los gráficos secundarios están enlazados al scatter plot 'S'
4. **Sincronización:** Los gráficos se actualizan en tiempo real sin necesidad de re-ejecutar celdas

## ✨ Resultado Esperado

- ✅ Dashboard visual con 4 gráficos organizados
- ✅ Scatter plot principal con brush selection funcionando
- ✅ 3 gráficos secundarios que se actualizan automáticamente
- ✅ Datos seleccionados disponibles en Python inmediatamente
- ✅ Sin errores de sintaxis
- ✅ Comunicación bidireccional Python ↔ D3.js completa

