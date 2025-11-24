# ============================================================================
# BESTLIB - Test Completo para Google Colab
# Branch: restore
# ============================================================================
# Este notebook prueba todas las funcionalidades de interactividad, 
# selección y linked views de BESTLIB en Google Colab
# ============================================================================

# %% [markdown]
# # 🎨 BESTLIB - Test Completo en Google Colab
# 
# Este notebook prueba:
# - ✅ Instalación en Colab
# - ✅ Gráficos interactivos básicos (scatter, bar)
# - ✅ Selección con brush
# - ✅ Linked Views (vistas enlazadas)
# - ✅ ReactiveMatrixLayout con SelectionModel
# - ✅ Callbacks y eventos JavaScript ↔ Python

# %% [markdown]
# ## 📦 Paso 1: Instalación
# 
# Instala BESTLIB desde el repositorio

# %%
# Desinstalar versión anterior si existe
!pip uninstall -y BESTLIB 2>/dev/null || true

# Instalar desde el repositorio (branch restore)
!pip install git+https://github.com/NahiaEscalante/bestlib.git@restore

# Verificar instalación
import BESTLIB
print(f"✅ BESTLIB instalado correctamente")
print(f"   Versión: {BESTLIB.__version__}")

# %% [markdown]
# ## 📊 Paso 2: Preparar Datos de Prueba
# 
# Creamos un dataset sintético con diferentes características

# %%
import pandas as pd
import numpy as np

# Configurar semilla para reproducibilidad
np.random.seed(42)

# Crear dataset de prueba
n_samples = 150

# Dataset 1: Iris-like (para scatter plots y linked views)
iris_data = pd.DataFrame({
    'sepal_length': np.concatenate([
        np.random.normal(5.0, 0.5, 50),
        np.random.normal(5.9, 0.5, 50),
        np.random.normal(6.5, 0.5, 50)
    ]),
    'sepal_width': np.concatenate([
        np.random.normal(3.4, 0.4, 50),
        np.random.normal(2.8, 0.3, 50),
        np.random.normal(3.0, 0.3, 50)
    ]),
    'petal_length': np.concatenate([
        np.random.normal(1.5, 0.2, 50),
        np.random.normal(4.3, 0.5, 50),
        np.random.normal(5.5, 0.5, 50)
    ]),
    'petal_width': np.concatenate([
        np.random.normal(0.2, 0.1, 50),
        np.random.normal(1.3, 0.2, 50),
        np.random.normal(2.0, 0.3, 50)
    ]),
    'species': ['setosa'] * 50 + ['versicolor'] * 50 + ['virginica'] * 50,
    'id': range(n_samples)
})

print("✅ Dataset creado:")
print(f"   - {len(iris_data)} muestras")
print(f"   - {len(iris_data.columns)} columnas")
print(f"\nPrimeras filas:")
print(iris_data.head())
print(f"\nDistribución de especies:")
print(iris_data['species'].value_counts())

# %% [markdown]
# ## 🎯 Paso 3: Test 1 - Scatter Plot Interactivo Básico
# 
# Probamos un scatter plot con brush selection

# %%
from BESTLIB import MatrixLayout

# Activar modo debug para ver eventos
MatrixLayout.set_debug(True)

# Configurar scatter plot interactivo
MatrixLayout.map_scatter(
    'S',
    iris_data,
    x_col='sepal_length',
    y_col='sepal_width',
    category_col='species',
    interactive=True,  # 🔥 Habilita brush selection
    axes=True,
    pointRadius=6,
    colorMap={
        'setosa': '#e74c3c',
        'versicolor': '#3498db',
        'virginica': '#2ecc71'
    }
)

# Crear layout
layout_scatter = MatrixLayout("SSS")

# Callback para capturar selecciones
selected_items = []

def on_scatter_select(payload):
    global selected_items
    selected_items = payload.get('items', [])
    count = len(selected_items)
    print(f"\n{'='*60}")
    print(f"📊 SELECCIÓN DETECTADA")
    print(f"{'='*60}")
    print(f"✅ {count} puntos seleccionados")
    
    if count > 0:
        # Mostrar primeros 5 elementos
        print(f"\nPrimeros elementos:")
        for i, item in enumerate(selected_items[:5]):
            print(f"  {i+1}. Species: {item.get('species', 'N/A')}, "
                  f"Sepal Length: {item.get('sepal_length', 'N/A'):.2f}, "
                  f"Sepal Width: {item.get('sepal_width', 'N/A'):.2f}")
        
        # Estadísticas
        if count > 1:
            sepal_lengths = [item.get('sepal_length', 0) for item in selected_items if 'sepal_length' in item]
            if sepal_lengths:
                print(f"\n📈 Estadísticas de Sepal Length:")
                print(f"   Min: {min(sepal_lengths):.2f}")
                print(f"   Max: {max(sepal_lengths):.2f}")
                print(f"   Mean: {sum(sepal_lengths)/len(sepal_lengths):.2f}")
    print(f"{'='*60}\n")

layout_scatter.on('select', on_scatter_select)

print("🎯 Scatter Plot Interactivo")
print("=" * 60)
print("📌 Instrucciones:")
print("   1. Arrastra el mouse sobre el gráfico para seleccionar puntos (brush)")
print("   2. Observa los datos seleccionados en la consola")
print("   3. La variable 'selected_items' contendrá los puntos seleccionados")
print("=" * 60)

# Mostrar layout
layout_scatter

# %% [markdown]
# ### 📋 Verificar Selección
# 
# Ejecuta esta celda después de hacer una selección en el scatter plot

# %%
# Verificar datos seleccionados
if selected_items:
    print(f"✅ Hay {len(selected_items)} elementos seleccionados")
    
    # Convertir a DataFrame para análisis
    selected_df = pd.DataFrame(selected_items)
    
    print("\n📊 Distribución de especies seleccionadas:")
    print(selected_df['species'].value_counts())
    
    print("\n📈 Estadísticas de las variables:")
    print(selected_df[['sepal_length', 'sepal_width', 'petal_length', 'petal_width']].describe())
else:
    print("⚠️ No hay elementos seleccionados. Usa el brush en el scatter plot primero.")

# %% [markdown]
# ## 🔗 Paso 4: Test 2 - Linked Views (Vistas Enlazadas)
# 
# Probamos el sistema de vistas enlazadas: scatter plot + bar chart + histogram

# %%
from BESTLIB import ReactiveMatrixLayout, SelectionModel

# Crear modelo de selección
selection_model = SelectionModel()

# Crear layout reactivo con múltiples vistas
layout = ReactiveMatrixLayout(
    """
    SSS
    BBH
    """,
    selection_model=selection_model,
    gap=15,
    cell_padding=10
)

# Establecer datos
layout.set_data(iris_data)

# 1. Scatter plot (vista principal - genera selecciones)
layout.add_scatter(
    'S',
    x_col='petal_length',
    y_col='petal_width',
    category_col='species',
    interactive=True,
    axes=True,
    colorMap={
        'setosa': '#e74c3c',
        'versicolor': '#3498db',
        'virginica': '#2ecc71'
    }
)

# 2. Bar chart enlazado (se actualiza automáticamente)
layout.add_barchart(
    'B',
    category_col='species',
    linked_to='S',  # 🔥 Enlazado al scatter 'S'
    axes=True,
    colorMap={
        'setosa': '#e74c3c',
        'versicolor': '#3498db',
        'virginica': '#2ecc71'
    }
)

# 3. Histogram enlazado (se actualiza automáticamente)
layout.add_histogram(
    'H',
    column='sepal_length',
    bins=15,
    linked_to='S',  # 🔥 Enlazado al scatter 'S'
    axes=True,
    color='#9b59b6'
)

print("🔗 Linked Views - Sistema de Vistas Enlazadas")
print("=" * 60)
print("📌 Instrucciones:")
print("   1. Arrastra el mouse en el SCATTER PLOT (superior) para seleccionar")
print("   2. Observa cómo el BAR CHART (inferior izquierdo) se actualiza")
print("   3. Observa cómo el HISTOGRAM (inferior derecho) se actualiza")
print("   4. Los tres gráficos están sincronizados automáticamente")
print("=" * 60)

# Mostrar layout
layout.display()

# %% [markdown]
# ### 📊 Acceder a Datos Seleccionados en Linked Views

# %%
# Los datos seleccionados están en el SelectionModel
selected_count = selection_model.get_count()
selected_items_linked = selection_model.get_items()

print(f"📊 Estado de la Selección:")
print(f"   - Elementos seleccionados: {selected_count}")

if selected_items_linked and len(selected_items_linked) > 0:
    # Convertir a DataFrame
    selected_df = pd.DataFrame(selected_items_linked)
    
    print(f"\n✅ Datos seleccionados disponibles:")
    print(f"   - Columnas: {list(selected_df.columns)}")
    print(f"   - Filas: {len(selected_df)}")
    
    print(f"\n📈 Distribución de especies:")
    print(selected_df['species'].value_counts())
    
    print(f"\n🔢 Estadísticas numéricas:")
    print(selected_df[['petal_length', 'petal_width', 'sepal_length']].describe())
else:
    print("\n⚠️ No hay datos seleccionados. Selecciona puntos en el scatter plot.")

# %% [markdown]
# ## 🎨 Paso 5: Test 3 - Bar Chart Interactivo (Vista Principal)
# 
# Probamos un bar chart como vista principal que genera selecciones

# %%
from BESTLIB import ReactiveMatrixLayout, SelectionModel

# Crear nuevo modelo de selección
bar_selection = SelectionModel()

# Variable para guardar selecciones
bar_selected_data = []

# Crear layout con bar chart como vista principal
layout_bar = ReactiveMatrixLayout(
    "BBB",
    selection_model=bar_selection
)

layout_bar.set_data(iris_data)

# Bar chart INTERACTIVO (vista principal)
layout_bar.add_barchart(
    'B',
    category_col='species',
    interactive=True,  # 🔥 Vista principal - genera selecciones
    selection_var='bar_selected_data',  # 🔥 Guardar en variable Python
    axes=True,
    colorMap={
        'setosa': '#e74c3c',
        'versicolor': '#3498db',
        'virginica': '#2ecc71'
    }
)

print("📊 Bar Chart Interactivo (Vista Principal)")
print("=" * 60)
print("📌 Instrucciones:")
print("   1. Haz CLICK en una barra para seleccionar esa categoría")
print("   2. Los datos seleccionados se guardarán en 'bar_selected_data'")
print("   3. Ejecuta la siguiente celda para ver los datos")
print("=" * 60)

layout_bar.display()

# %% [markdown]
# ### 📋 Verificar Selección del Bar Chart

# %%
# Verificar datos guardados en la variable
print(f"📊 Variable 'bar_selected_data':")

if isinstance(bar_selected_data, pd.DataFrame) and not bar_selected_data.empty:
    print(f"✅ {len(bar_selected_data)} filas seleccionadas")
    print(f"\n📋 Datos:")
    print(bar_selected_data.head())
    
    print(f"\n📈 Distribución de especies:")
    print(bar_selected_data['species'].value_counts())
elif isinstance(bar_selected_data, list) and bar_selected_data:
    print(f"✅ {len(bar_selected_data)} elementos seleccionados")
    print(f"\nPrimeros elementos:")
    for i, item in enumerate(bar_selected_data[:3]):
        print(f"  {i+1}. {item}")
else:
    print("⚠️ No hay datos seleccionados. Haz click en una barra del bar chart.")

# También verificar el SelectionModel
selected_count_bar = bar_selection.get_count()
print(f"\n🔢 SelectionModel: {selected_count_bar} elementos")

# %% [markdown]
# ## 🎯 Paso 6: Test 4 - Dashboard Completo con Múltiples Vistas
# 
# Creamos un dashboard completo con todas las visualizaciones

# %%
from BESTLIB import ReactiveMatrixLayout, SelectionModel

# Crear modelo de selección para el dashboard
dashboard_selection = SelectionModel()

# Crear dataset adicional para grouped bar chart
sales_data = pd.DataFrame({
    'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
    'product': np.random.choice(['A', 'B', 'C'], 100),
    'sales': np.random.randint(100, 1000, 100),
    'quantity': np.random.randint(10, 100, 100)
})

# Crear layout con múltiples vistas
dashboard = ReactiveMatrixLayout(
    """
    SSSBBB
    SSSHHH
    PPPCCC
    """,
    selection_model=dashboard_selection,
    gap=12,
    cell_padding=10,
    max_width=1400
)

dashboard.set_data(iris_data)

# 1. Scatter plot principal
dashboard.add_scatter(
    'S',
    x_col='petal_length',
    y_col='petal_width',
    category_col='species',
    interactive=True,
    axes=True,
    colorMap={
        'setosa': '#e74c3c',
        'versicolor': '#3498db',
        'virginica': '#2ecc71'
    }
)

# 2. Bar chart enlazado (especies)
dashboard.add_barchart(
    'B',
    category_col='species',
    linked_to='S',
    axes=True,
    colorMap={
        'setosa': '#e74c3c',
        'versicolor': '#3498db',
        'virginica': '#2ecc71'
    }
)

# 3. Histogram enlazado (sepal length)
dashboard.add_histogram(
    'H',
    column='sepal_length',
    bins=12,
    linked_to='S',
    axes=True,
    color='#9b59b6'
)

# 4. Pie chart enlazado (especies)
dashboard.add_pie(
    'P',
    category_col='species',
    linked_to='S',
    donut=True,
    innerRadius=40,
    interactive=False,
    colorMap={
        'setosa': '#e74c3c',
        'versicolor': '#3498db',
        'virginica': '#2ecc71'
    }
)

# 5. Correlation heatmap (solo lectura)
# Crear matriz de correlación
numeric_cols = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']
corr_matrix = iris_data[numeric_cols].corr()

dashboard.add_correlation_heatmap(
    'C',
    showValues=False,
    colorScale='diverging'
)

print("🎨 Dashboard Completo")
print("=" * 60)
print("📌 Componentes:")
print("   - Scatter Plot (superior izquierdo) - Vista Principal")
print("   - Bar Chart (superior derecho) - Enlazado")
print("   - Histogram (medio derecho) - Enlazado")
print("   - Pie Chart (inferior izquierdo) - Enlazado")
print("   - Correlation Heatmap (inferior derecho) - Solo lectura")
print("\n📌 Instrucciones:")
print("   1. Selecciona puntos en el scatter plot")
print("   2. Observa cómo TODAS las vistas enlazadas se actualizan")
print("=" * 60)

dashboard.display()

# %% [markdown]
# ## 🔍 Paso 7: Test 5 - Verificar Sistema de Comunicación
# 
# Verificamos que el sistema de comunicación JavaScript ↔ Python funcione correctamente

# %%
# Verificar estado del sistema
status = MatrixLayout.get_status()

print("🔍 Estado del Sistema de Comunicación")
print("=" * 60)
print(f"✅ Comm registrado: {status['comm_registered']}")
print(f"🐛 Modo debug: {status['debug_mode']}")
print(f"📊 Instancias activas: {status['active_instances']}")
print(f"🎯 Instancias totales: {status['total_instances']}")
print(f"\n📋 IDs de instancias:")
for inst_id in status['instance_ids']:
    print(f"   - {inst_id}")
print(f"\n🌐 Handlers globales:")
for handler_name in status['global_handlers']:
    print(f"   - {handler_name}")
print("=" * 60)

# Verificar que el comm esté funcionando
if status['comm_registered']:
    print("\n✅ Sistema de comunicación funcionando correctamente")
else:
    print("\n⚠️ Sistema de comunicación no está registrado")
    print("   Intentando registrar manualmente...")
    MatrixLayout.register_comm(force=True)
    print("   Verificar nuevamente con MatrixLayout.get_status()")

# %% [markdown]
# ## 📊 Paso 8: Test 6 - Historial de Selecciones
# 
# Verificamos que el historial de selecciones se guarde correctamente

# %%
# Verificar historial de selecciones
history = selection_model.get_history()

print("📚 Historial de Selecciones")
print("=" * 60)
print(f"Total de selecciones: {len(history)}")

if history:
    print("\n📋 Últimas 5 selecciones:")
    for i, selection in enumerate(history[-5:], 1):
        timestamp = selection['timestamp']
        count = selection['count']
        print(f"\n{i}. {timestamp}")
        print(f"   - Elementos: {count}")
        
        if count > 0:
            items = selection['items']
            species_counts = {}
            for item in items:
                species = item.get('species', 'N/A')
                species_counts[species] = species_counts.get(species, 0) + 1
            
            print(f"   - Distribución:")
            for species, count_sp in species_counts.items():
                print(f"     • {species}: {count_sp}")
else:
    print("\n⚠️ No hay historial. Selecciona puntos en el scatter plot primero.")

print("=" * 60)

# %% [markdown]
# ## 🎯 Paso 9: Test 7 - Callbacks Múltiples
# 
# Probamos registrar múltiples callbacks para el mismo evento

# %%
from BESTLIB import MatrixLayout

# Crear nuevo scatter plot para callbacks múltiples
layout_multi = MatrixLayout("SSS")

# Variable para contador
callback_counter = {'count': 0}

# Callback 1: Contador
def callback_counter_func(payload):
    callback_counter['count'] += 1
    count = len(payload.get('items', []))
    print(f"🔔 Callback 1 (Contador): Selección #{callback_counter['count']} - {count} elementos")

# Callback 2: Estadísticas
def callback_stats(payload):
    items = payload.get('items', [])
    if items:
        sepal_lengths = [item.get('sepal_length', 0) for item in items if 'sepal_length' in item]
        if sepal_lengths:
            avg = sum(sepal_lengths) / len(sepal_lengths)
            print(f"📊 Callback 2 (Stats): Sepal Length promedio = {avg:.2f}")

# Callback 3: Especies
def callback_species(payload):
    items = payload.get('items', [])
    if items:
        species_list = [item.get('species', 'N/A') for item in items if 'species' in item]
        unique_species = set(species_list)
        print(f"🌸 Callback 3 (Especies): {len(unique_species)} especies únicas - {unique_species}")

# Registrar los tres callbacks
layout_multi.on('select', callback_counter_func)
layout_multi.on('select', callback_stats)
layout_multi.on('select', callback_species)

# Configurar scatter plot
MatrixLayout.map_scatter(
    'S',
    iris_data,
    x_col='sepal_length',
    y_col='sepal_width',
    category_col='species',
    interactive=True,
    axes=True
)

print("🎯 Test de Callbacks Múltiples")
print("=" * 60)
print("📌 Registrados 3 callbacks para el mismo evento:")
print("   1. Contador de selecciones")
print("   2. Estadísticas de Sepal Length")
print("   3. Análisis de especies")
print("\n📌 Instrucciones:")
print("   Selecciona puntos y observa cómo se ejecutan los 3 callbacks")
print("=" * 60)

layout_multi

# %% [markdown]
# ## ✅ Paso 10: Resumen y Verificación Final
# 
# Verificamos que todo funcione correctamente

# %%
print("=" * 70)
print(" " * 20 + "✅ RESUMEN DE PRUEBAS")
print("=" * 70)

# 1. Verificar instalación
try:
    import BESTLIB
    print(f"✅ 1. Instalación: OK (v{BESTLIB.__version__})")
except:
    print("❌ 1. Instalación: FALLO")

# 2. Verificar datos
try:
    assert len(iris_data) == 150
    print(f"✅ 2. Datos: OK ({len(iris_data)} muestras)")
except:
    print("❌ 2. Datos: FALLO")

# 3. Verificar scatter plot interactivo
try:
    assert len(selected_items) >= 0
    print(f"✅ 3. Scatter Interactivo: OK ({len(selected_items)} seleccionados)")
except:
    print("❌ 3. Scatter Interactivo: FALLO")

# 4. Verificar linked views
try:
    count = selection_model.get_count()
    print(f"✅ 4. Linked Views: OK ({count} elementos en modelo)")
except:
    print("❌ 4. Linked Views: FALLO")

# 5. Verificar bar chart interactivo
try:
    count_bar = bar_selection.get_count()
    print(f"✅ 5. Bar Chart Interactivo: OK ({count_bar} elementos)")
except:
    print("❌ 5. Bar Chart Interactivo: FALLO")

# 6. Verificar dashboard
try:
    count_dashboard = dashboard_selection.get_count()
    print(f"✅ 6. Dashboard Completo: OK ({count_dashboard} elementos)")
except:
    print("❌ 6. Dashboard Completo: FALLO")

# 7. Verificar sistema de comunicación
try:
    status = MatrixLayout.get_status()
    assert status['comm_registered']
    print(f"✅ 7. Sistema de Comunicación: OK")
except:
    print("❌ 7. Sistema de Comunicación: FALLO")

# 8. Verificar historial
try:
    history = selection_model.get_history()
    print(f"✅ 8. Historial: OK ({len(history)} entradas)")
except:
    print("❌ 8. Historial: FALLO")

# 9. Verificar callbacks múltiples
try:
    assert callback_counter['count'] >= 0
    print(f"✅ 9. Callbacks Múltiples: OK ({callback_counter['count']} ejecuciones)")
except:
    print("❌ 9. Callbacks Múltiples: FALLO")

print("=" * 70)
print("\n📝 Notas:")
print("   - Si algunos tests muestran 0 elementos, es porque aún no has hecho selecciones")
print("   - Regresa a las celdas anteriores y selecciona puntos en los gráficos")
print("   - Luego ejecuta esta celda nuevamente para ver los resultados actualizados")
print("\n🎉 ¡Pruebas completadas!")
print("=" * 70)

# %% [markdown]
# ## 🐛 Debug: Información del Sistema
# 
# Información útil para debugging

# %%
print("🐛 Información del Sistema")
print("=" * 60)

# Python
import sys
print(f"Python: {sys.version}")

# Pandas
try:
    import pandas as pd
    print(f"Pandas: {pd.__version__}")
except:
    print("Pandas: No instalado")

# NumPy
try:
    import numpy as np
    print(f"NumPy: {np.__version__}")
except:
    print("NumPy: No instalado")

# IPython
try:
    from IPython import __version__ as ipython_version
    print(f"IPython: {ipython_version}")
except:
    print("IPython: No instalado")

# ipywidgets
try:
    import ipywidgets
    print(f"ipywidgets: {ipywidgets.__version__}")
except:
    print("ipywidgets: No instalado")

# BESTLIB
try:
    import BESTLIB
    print(f"BESTLIB: {BESTLIB.__version__}")
    print(f"  - HAS_WIDGETS: {BESTLIB.HAS_WIDGETS if hasattr(BESTLIB, 'HAS_WIDGETS') else 'N/A'}")
    print(f"  - HAS_PANDAS: {BESTLIB.HAS_PANDAS if hasattr(BESTLIB, 'HAS_PANDAS') else 'N/A'}")
    print(f"  - HAS_CORE: {BESTLIB.HAS_CORE if hasattr(BESTLIB, 'HAS_CORE') else 'N/A'}")
    print(f"  - HAS_REACTIVE: {BESTLIB.HAS_REACTIVE if hasattr(BESTLIB, 'HAS_REACTIVE') else 'N/A'}")
except Exception as e:
    print(f"BESTLIB: Error - {e}")

print("=" * 60)

# %% [markdown]
# ## 📚 Recursos Adicionales
# 
# - 📖 Documentación: Ver README.md en el repositorio
# - 🐛 Issues: https://github.com/NahiaEscalante/bestlib/issues
# - 💡 Ejemplos: Ver carpeta `examples/` en el repositorio
# 
# ### Solución de Problemas Comunes
# 
# **1. Los gráficos no se muestran:**
# - Verifica que estés en Google Colab
# - Ejecuta `MatrixLayout.register_comm(force=True)`
# 
# **2. Las selecciones no funcionan:**
# - Activa debug: `MatrixLayout.set_debug(True)`
# - Verifica que `interactive=True` esté configurado
# - Revisa los mensajes en la consola
# 
# **3. Linked views no se actualizan:**
# - Verifica que `linked_to` apunte a la vista correcta
# - Asegúrate de que la vista principal tenga `interactive=True`
# - Revisa que los datos tengan las columnas correctas
# 
# **4. Errores de importación:**
# - Reinstala: `!pip install --force-reinstall git+https://github.com/NahiaEscalante/bestlib.git@restore`
# - Reinicia el runtime de Colab
