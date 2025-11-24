import sys
sys.path.insert(0, 'c:/Users/USUARIO/Desktop/visualizacion/bestlib')

import pandas as pd
import numpy as np
from BESTLIB import MatrixLayout
from sklearn.datasets import load_iris

# Cargar datos
iris = load_iris()
df_iris = pd.DataFrame(iris.data, columns=iris.feature_names)
df_iris['species'] = iris.target_names[iris.target]
df_iris.columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'species']

print("Dataset Iris cargado:")
print(df_iris.head())
print(f"\nColumnas: {list(df_iris.columns)}")
print(f"Shape: {df_iris.shape}")

# Probar KDE
print("\n" + "="*50)
print("Probando KDE...")
print("="*50)

try:
    layout11 = MatrixLayout("K")
    layout11.map_kde('K', df_iris, column='petal_length',
                     xLabel='Petal Length', yLabel='Density', title='KDE: Petal Length')
    print("✅ KDE creado exitosamente")
    
    # Ver la especificación generada
    print("\nEspecificación generada:")
    import json
    print(json.dumps(layout11._map, indent=2))
    
except Exception as e:
    print(f"❌ Error al crear KDE: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
