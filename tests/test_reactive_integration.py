"""
Tests de integración para ReactiveMatrixLayout con scatter, boxplot y violin.
"""
import pytest
import pandas as pd
import numpy as np
from BESTLIB.layouts.reactive import ReactiveMatrixLayout
from BESTLIB.reactive.selection import SelectionModel


@pytest.fixture
def sample_iris_df():
    """Datos de muestra similares a iris."""
    np.random.seed(42)
    return pd.DataFrame({
        'petal_length': np.concatenate([
            np.random.normal(1.5, 0.2, 50),
            np.random.normal(4.5, 0.5, 50),
            np.random.normal(5.5, 0.6, 50)
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
        'species': ['setosa'] * 50 + ['versicolor'] * 50 + ['virginica'] * 50
    })


def test_reactive_layout_scatter_boxplot(sample_iris_df):
    """Test básico: scatter + boxplot enlazado."""
    layout = ReactiveMatrixLayout("""
S
X
""")
    layout.set_data(sample_iris_df)
    
    # Agregar scatter
    layout.add_scatter(
        'S',
        x_col='petal_length',
        y_col='petal_width',
        category_col='species',
        interactive=True
    )
    
    # Agregar boxplot enlazado
    layout.add_boxplot(
        'X',
        column='petal_length',
        category_col='species',
        linked_to='S'
    )
    
    # Verificar que ambos charts están en el map
    assert 'S' in layout._layout._map
    assert 'X' in layout._layout._map
    
    # Verificar que el boxplot tiene __linked_to__
    assert layout._layout._map['X'].get('__linked_to__') == 'S'


def test_reactive_layout_scatter_violin(sample_iris_df):
    """Test: scatter + violin enlazado."""
    layout = ReactiveMatrixLayout("""
S
V
""")
    layout.set_data(sample_iris_df)
    
    # Agregar scatter
    layout.add_scatter(
        'S',
        x_col='petal_length',
        y_col='petal_width',
        category_col='species',
        interactive=True
    )
    
    # Agregar violin enlazado
    layout.add_violin(
        'V',
        value_col='petal_length',
        category_col='species',
        linked_to='S'
    )
    
    # Verificar que ambos charts están en el map
    assert 'S' in layout._layout._map
    assert 'V' in layout._layout._map
    
    # Verificar que el violin tiene datos con perfiles
    violin_spec = layout._layout._map['V']
    assert 'data' in violin_spec
    assert len(violin_spec['data']) > 0
    
    # Verificar que cada categoría tiene un perfil
    for violin_data in violin_spec['data']:
        assert 'category' in violin_data
        assert 'profile' in violin_data
        assert len(violin_data['profile']) > 0


def test_reactive_layout_multiple_charts(sample_iris_df):
    """Test completo: scatter + boxplot + violin + bar."""
    layout = ReactiveMatrixLayout("""
SSH
BXV
""")
    layout.set_data(sample_iris_df)
    
    # Agregar scatter principal
    layout.add_scatter(
        'S',
        x_col='petal_length',
        y_col='petal_width',
        category_col='species',
        interactive=True
    )
    
    # Agregar histogram
    layout.add_histogram(
        'H',
        column='sepal_length',
        bins=15,
        linked_to='S'
    )
    
    # Agregar bar chart
    layout.add_barchart(
        'B',
        category_col='species',
        value_col='petal_length',
        linked_to='S'
    )
    
    # Agregar boxplot
    layout.add_boxplot(
        'X',
        column='petal_width',
        category_col='species',
        linked_to='S'
    )
    
    # Agregar violin
    layout.add_violin(
        'V',
        value_col='petal_length',
        category_col='species',
        linked_to='S'
    )
    
    # Verificar que todos los charts están en el map
    assert 'S' in layout._layout._map
    assert 'H' in layout._layout._map
    assert 'B' in layout._layout._map
    assert 'X' in layout._layout._map
    assert 'V' in layout._layout._map
    
    # Verificar que no hay letras extra
    chart_letters = {k for k in layout._layout._map.keys() if not k.startswith('__')}
    assert chart_letters == {'S', 'H', 'B', 'X', 'V'}


def test_no_attribute_error_on_boxplot(sample_iris_df):
    """Test específico para el bug reportado: AttributeError en add_boxplot."""
    layout = ReactiveMatrixLayout("SX")
    layout.set_data(sample_iris_df)
    
    layout.add_scatter(
        'S',
        x_col='petal_length',
        y_col='petal_width',
        category_col='species',
        interactive=True
    )
    
    # Esto no debe lanzar AttributeError
    try:
        layout.add_boxplot(
            'X',
            column='petal_length',
            category_col='species',
            linked_to='S'
        )
    except AttributeError as e:
        pytest.fail(f"add_boxplot lanzó AttributeError: {e}")
    
    # Verificar que se creó correctamente
    assert 'X' in layout._layout._map


def test_no_letters_not_in_layout_error(sample_iris_df):
    """Test para verificar que no aparece error de 'letras inexistentes'."""
    # Crear primer layout
    layout1 = ReactiveMatrixLayout("AB")
    layout1.set_data(sample_iris_df)
    layout1.add_scatter('A', x_col='petal_length', y_col='petal_width')
    layout1.add_barchart('B', category_col='species')
    
    # Crear segundo layout con letras diferentes
    layout2 = ReactiveMatrixLayout("XY")
    layout2.set_data(sample_iris_df)
    
    # Esto no debe lanzar error de "letras inexistentes"
    try:
        layout2.add_scatter('X', x_col='petal_length', y_col='petal_width')
        layout2.add_barchart('Y', category_col='species')
    except Exception as e:
        if "letras inexistentes" in str(e):
            pytest.fail(f"Error de letras inexistentes: {e}")
    
    # Verificar que cada layout tiene solo sus letras
    assert 'A' in layout1._layout._map
    assert 'B' in layout1._layout._map
    assert 'X' not in layout1._layout._map
    assert 'Y' not in layout1._layout._map
    
    assert 'X' in layout2._layout._map
    assert 'Y' in layout2._layout._map
    assert 'A' not in layout2._layout._map
    assert 'B' not in layout2._layout._map

