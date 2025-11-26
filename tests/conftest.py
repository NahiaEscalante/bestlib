"""
Configuración de pytest para tests de BESTLIB
"""
import pytest
import sys
from pathlib import Path

# Añadir BESTLIB al path si no está
bestlib_path = Path(__file__).parent.parent
if str(bestlib_path) not in sys.path:
    sys.path.insert(0, str(bestlib_path))


@pytest.fixture
def sample_dataframe():
    """Fixture: DataFrame de prueba simple"""
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("pandas no está instalado")
    
    return pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10],
        'category': ['A', 'A', 'B', 'B', 'C'],
        'value': [10, 20, 15, 25, 30]
    })


@pytest.fixture
def iris_dataframe():
    """Fixture: DataFrame Iris si existe el archivo"""
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("pandas no está instalado")
    
    iris_file = Path(__file__).parent.parent / 'examples' / 'iris.csv'
    
    if not iris_file.exists():
        pytest.skip("iris.csv no está disponible")
    
    return pd.read_csv(iris_file)


@pytest.fixture
def sample_dicts():
    """Fixture: Lista de diccionarios de prueba"""
    return [
        {'x': 1, 'y': 2, 'category': 'A'},
        {'x': 2, 'y': 4, 'category': 'A'},
        {'x': 3, 'y': 6, 'category': 'B'},
        {'x': 4, 'y': 8, 'category': 'B'},
        {'x': 5, 'y': 10, 'category': 'C'}
    ]

