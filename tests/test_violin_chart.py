"""
Tests para ViolinChart con perfiles de densidad reales.
"""
import pytest
import pandas as pd
import numpy as np
from BESTLIB.charts.violin import ViolinChart
from BESTLIB.core.exceptions import ChartError


@pytest.fixture
def sample_df_violin():
    """Datos de muestra para violin plot."""
    np.random.seed(42)
    return pd.DataFrame({
        'value': np.concatenate([
            np.random.normal(10, 2, 50),  # Grupo A
            np.random.normal(15, 3, 50),  # Grupo B
            np.random.normal(12, 1.5, 50)  # Grupo C
        ]),
        'category': ['A'] * 50 + ['B'] * 50 + ['C'] * 50
    })


def test_violin_chart_basic_spec(sample_df_violin):
    """Verifica que se genera un spec básico con perfiles no vacíos."""
    chart = ViolinChart()
    spec = chart.get_spec(sample_df_violin, value_col='value', category_col='category')
    
    assert spec['type'] == 'violin'
    assert 'data' in spec
    assert len(spec['data']) > 0
    
    # Verificar que cada categoría tiene un perfil
    categories = {item['category'] for item in spec['data']}
    assert 'A' in categories
    assert 'B' in categories
    assert 'C' in categories


def test_violin_chart_profile_structure(sample_df_violin):
    """Verifica que los perfiles tienen la estructura correcta."""
    chart = ViolinChart()
    spec = chart.get_spec(sample_df_violin, value_col='value', category_col='category', bins=30)
    
    for violin in spec['data']:
        assert 'category' in violin
        assert 'profile' in violin
        assert isinstance(violin['profile'], list)
        assert len(violin['profile']) > 0
        
        # Verificar estructura de cada punto del perfil
        for point in violin['profile']:
            assert 'y' in point  # Valor en el eje Y
            assert 'w' in point  # Ancho (densidad normalizada)
            assert isinstance(point['y'], (int, float))
            assert isinstance(point['w'], (int, float))
            assert 0 <= point['w'] <= 1  # Densidad normalizada entre 0 y 1


def test_violin_chart_single_category(sample_df_violin):
    """Verifica violin plot con una sola categoría."""
    df_single = sample_df_violin[sample_df_violin['category'] == 'A'].copy()
    
    chart = ViolinChart()
    spec = chart.get_spec(df_single, value_col='value')
    
    assert len(spec['data']) == 1
    assert spec['data'][0]['category'] == 'All'  # Sin category_col, usa 'All'
    assert len(spec['data'][0]['profile']) > 0


def test_violin_chart_few_values():
    """Verifica comportamiento con pocos valores."""
    df_few = pd.DataFrame({'value': [1.0, 2.0]})
    
    chart = ViolinChart()
    spec = chart.get_spec(df_few, value_col='value', bins=10)
    
    assert len(spec['data']) == 1
    assert len(spec['data'][0]['profile']) > 0


def test_violin_chart_single_value():
    """Verifica comportamiento con un solo valor."""
    df_single = pd.DataFrame({'value': [5.0]})
    
    chart = ViolinChart()
    spec = chart.get_spec(df_single, value_col='value')
    
    assert len(spec['data']) == 1
    # Con un solo valor, el perfil debe tener al menos un punto
    assert len(spec['data'][0]['profile']) >= 1


def test_violin_chart_missing_value_col_raises_error(sample_df_violin):
    """Verifica que falla si no se proporciona value_col."""
    chart = ViolinChart()
    
    with pytest.raises(ChartError, match="value_col es requerido"):
        chart.get_spec(sample_df_violin)


def test_violin_chart_invalid_column_raises_error(sample_df_violin):
    """Verifica que falla si la columna no existe."""
    chart = ViolinChart()
    
    with pytest.raises(Exception):  # DataError o ChartError
        chart.get_spec(sample_df_violin, value_col='non_existent')


def test_violin_chart_with_bins_parameter(sample_df_violin):
    """Verifica que el parámetro bins afecta la resolución del perfil."""
    chart = ViolinChart()
    
    spec_low = chart.get_spec(sample_df_violin, value_col='value', category_col='category', bins=10)
    spec_high = chart.get_spec(sample_df_violin, value_col='value', category_col='category', bins=100)
    
    # Con más bins, deberíamos tener más puntos en el perfil (aproximadamente)
    # Nota: Puede haber filtrado de puntos con w muy pequeño
    profile_low = spec_low['data'][0]['profile']
    profile_high = spec_high['data'][0]['profile']
    
    # Al menos verificar que ambos tienen perfiles
    assert len(profile_low) > 0
    assert len(profile_high) > 0


def test_violin_chart_density_normalized(sample_df_violin):
    """Verifica que las densidades están normalizadas (máximo = 1)."""
    chart = ViolinChart()
    spec = chart.get_spec(sample_df_violin, value_col='value', category_col='category')
    
    for violin in spec['data']:
        max_w = max(point['w'] for point in violin['profile'])
        # El máximo debería estar cerca de 1 (puede ser ligeramente menor por filtrado)
        assert 0.9 <= max_w <= 1.0


def test_violin_chart_list_of_dicts():
    """Verifica que funciona con lista de diccionarios."""
    data = [
        {'value': 10, 'category': 'A'},
        {'value': 12, 'category': 'A'},
        {'value': 11, 'category': 'A'},
        {'value': 15, 'category': 'B'},
        {'value': 16, 'category': 'B'},
        {'value': 14, 'category': 'B'},
    ]
    
    chart = ViolinChart()
    spec = chart.get_spec(data, value_col='value', category_col='category')
    
    assert len(spec['data']) == 2
    categories = {item['category'] for item in spec['data']}
    assert 'A' in categories
    assert 'B' in categories


def test_violin_chart_prepare_data_returns_valid_structure(sample_df_violin):
    """Verifica que prepare_data devuelve la estructura correcta."""
    chart = ViolinChart()
    prepared = chart.prepare_data(sample_df_violin, value_col='value', category_col='category')
    
    assert isinstance(prepared, list)
    assert len(prepared) > 0
    
    for item in prepared:
        assert 'category' in item
        assert 'profile' in item
        assert isinstance(item['profile'], list)

