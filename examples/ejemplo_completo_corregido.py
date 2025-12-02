"""
Ejemplo completo y funcional de BESTLIB con todos los bugs corregidos.
Copia y pega este código en Google Colab o Jupyter Notebook.
"""

# ============================================================================
# PASO 1: Instalar BESTLIB (solo en Colab)
# ============================================================================
# En Colab, ejecuta esto primero:
# !pip install --no-deps git+https://github.com/NahiaEscalante/bestlib.git@11-main-fixing

# ============================================================================
# PASO 2: Importar y preparar datos
# ============================================================================
from BESTLIB.layouts.reactive import ReactiveMatrixLayout
import pandas as pd
import numpy as np

# Crear datos de muestra (similar a iris pero con nombres simples)
np.random.seed(42)
df_iris = pd.DataFrame({
    'petal_length': np.concatenate([
        np.random.normal(1.5, 0.2, 50),   # setosa
        np.random.normal(4.5, 0.5, 50),   # versicolor
        np.random.normal(5.5, 0.6, 50)    # virginica
    ]),
    'petal_width': np.concatenate([
        np.random.normal(0.3, 0.1, 50),
        np.random.normal(1.3, 0.2, 50),
        np.random.normal(2.0, 0.3, 50)
    ]),
    'sepal_length': np.concatenate([
        np.random.normal(5.0, 0.4, 50),
        np.random.normal(6.0, 0.5, 50),
        np.random.normal(6.5, 0.6, 50)
    ]),
    'sepal_width': np.concatenate([
        np.random.normal(3.4, 0.3, 50),
        np.random.normal(2.8, 0.3, 50),
        np.random.normal(3.0, 0.3, 50)
    ]),
    'species': ['setosa'] * 50 + ['versicolor'] * 50 + ['virginica'] * 50
})

print("✅ Datos creados:")
print(df_iris.head())
print(f"\nShape: {df_iris.shape}")
print(f"Columnas: {list(df_iris.columns)}")

# ============================================================================
# EJEMPLO 1: Scatter + Boxplot enlazado (el que fallaba antes)
# ============================================================================
print("\n" + "="*60)
print("EJEMPLO 1: Scatter + Boxplot")
print("="*60)

demo1 = ReactiveMatrixLayout("""
S
X
""")
demo1.set_data(df_iris)

demo1.add_scatter(
    'S',
    x_col='petal_length',
    y_col='petal_width',
    category_col='species',
    interactive=True,
    title='SCATTER: Arrastra para seleccionar'
)

demo1.add_boxplot(
    'X',
    column='petal_length',
    category_col='species',
    linked_to='S',
    title='BOXPLOT: Actualizado dinámicamente'
)

print("✅ Demo 1 creado sin errores")
demo1.display()

# ============================================================================
# EJEMPLO 2: Scatter + Bar enlazado
# ============================================================================
print("\n" + "="*60)
print("EJEMPLO 2: Scatter + Bar")
print("="*60)

demo2 = ReactiveMatrixLayout("""
S
B
""")
demo2.set_data(df_iris)

demo2.add_scatter(
    'S',
    x_col='sepal_length',
    y_col='sepal_width',
    category_col='species',
    interactive=True,
    title='SCATTER: Selecciona puntos'
)

demo2.add_barchart(
    'B',
    category_col='species',
    value_col='petal_length',
    linked_to='S',
    title='BAR: Actualizado por selección'
)

print("✅ Demo 2 creado sin errores")
demo2.display()

# ============================================================================
# EJEMPLO 3: Dashboard completo 2x3 con Violin
# ============================================================================
print("\n" + "="*60)
print("EJEMPLO 3: Dashboard completo con Violin")
print("="*60)

dashboard = ReactiveMatrixLayout("""
SSH
BXV
""")
dashboard.set_data(df_iris)

# Scatter principal (control)
dashboard.add_scatter(
    'S',
    x_col='petal_length',
    y_col='petal_width',
    category_col='species',
    interactive=True,
    title='CONTROL: Selecciona aquí'
)

# Histogram enlazado
dashboard.add_histogram(
    'H',
    column='sepal_length',
    bins=15,
    linked_to='S',
    title='Distribución Sépalo'
)

# Bar chart enlazado
dashboard.add_barchart(
    'B',
    category_col='species',
    value_col='petal_length',
    linked_to='S',
    title='Conteo por Especie'
)

# Boxplot enlazado
dashboard.add_boxplot(
    'X',
    column='sepal_width',
    category_col='species',
    linked_to='S',
    title='Ancho Sépalo'
)

# Violin enlazado (ahora con KDE real)
dashboard.add_violin(
    'V',
    value_col='petal_length',
    category_col='species',
    linked_to='S',
    title='Densidad Pétalo'
)

print("✅ Dashboard creado sin errores")
dashboard.display()

# ============================================================================
# EJEMPLO 4: Verificar que múltiples dashboards no interfieren
# ============================================================================
print("\n" + "="*60)
print("EJEMPLO 4: Múltiples dashboards independientes")
print("="*60)

# Primer dashboard con letras AB
layout_a = ReactiveMatrixLayout("AB")
layout_a.set_data(df_iris)
layout_a.add_scatter('A', x_col='petal_length', y_col='petal_width', category_col='species')
layout_a.add_barchart('B', category_col='species')

print("✅ Layout A creado (letras: A, B)")

# Segundo dashboard con letras XY (no debe dar error de "letras inexistentes")
layout_b = ReactiveMatrixLayout("XY")
layout_b.set_data(df_iris)
layout_b.add_scatter('X', x_col='sepal_length', y_col='sepal_width', category_col='species')
layout_b.add_barchart('Y', category_col='species')

print("✅ Layout B creado (letras: X, Y)")
print("✅ No hay errores de 'letras inexistentes'")

layout_a.display()
layout_b.display()

# ============================================================================
# EJEMPLO 5: Usando datos reales de sklearn (opcional)
# ============================================================================
print("\n" + "="*60)
print("EJEMPLO 5: Con datos reales de sklearn")
print("="*60)

try:
    from sklearn.datasets import load_iris
    
    iris = load_iris(as_frame=True)
    df_real = iris.frame
    
    # Renombrar columnas para quitar espacios
    df_real.columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'target']
    df_real['species'] = df_real['target'].map({0: 'setosa', 1: 'versicolor', 2: 'virginica'})
    
    print("✅ Datos de sklearn cargados")
    
    # Crear dashboard con datos reales
    real_dashboard = ReactiveMatrixLayout("SB")
    real_dashboard.set_data(df_real)
    
    real_dashboard.add_scatter(
        'S',
        x_col='petal_length',
        y_col='petal_width',
        category_col='species',
        interactive=True,
        title='Iris Dataset'
    )
    
    real_dashboard.add_boxplot(
        'B',
        column='petal_length',
        category_col='species',
        linked_to='S',
        title='Distribución por Especie'
    )
    
    print("✅ Dashboard con datos reales creado")
    real_dashboard.display()
    
except ImportError:
    print("⚠️ sklearn no está instalado, saltando ejemplo 5")

print("\n" + "="*60)
print("✅ TODOS LOS EJEMPLOS COMPLETADOS SIN ERRORES")
print("="*60)

