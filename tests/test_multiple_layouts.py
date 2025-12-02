"""
Tests para verificar que múltiples layouts simultáneos no interfieren entre sí.
"""
import pytest
import pandas as pd
from BESTLIB.layouts.matrix import MatrixLayout
from BESTLIB.layouts.reactive import ReactiveMatrixLayout
from BESTLIB.reactive.selection import SelectionModel


@pytest.fixture
def sample_df1():
    return pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 12, 15, 11, 13],
        'category': ['A', 'B', 'A', 'C', 'B']
    })


@pytest.fixture
def sample_df2():
    return pd.DataFrame({
        'a': [5, 6, 7, 8, 9],
        'b': [20, 22, 25, 21, 23],
        'group': ['X', 'Y', 'X', 'Z', 'Y']
    })


def test_two_matrix_layouts_independent_maps(sample_df1, sample_df2):
    """
    Verifica que dos MatrixLayout con letras diferentes no interfieran entre sí.
    """
    # Crear primer layout con letra 'A'
    layout1 = MatrixLayout("A")
    layout1._register_spec('A', {'type': 'scatter', 'data': sample_df1.to_dict('records')})
    
    # Crear segundo layout con letra 'B'
    layout2 = MatrixLayout("B")
    layout2._register_spec('B', {'type': 'bar', 'data': sample_df2.to_dict('records')})
    
    # Verificar que cada layout tiene solo su spec
    assert 'A' in layout1._map
    assert 'B' not in layout1._map
    
    assert 'B' in layout2._map
    assert 'A' not in layout2._map


def test_two_matrix_layouts_same_letter_independent(sample_df1, sample_df2):
    """
    Verifica que dos MatrixLayout con la misma letra pero diferentes datos no interfieran.
    """
    # Crear dos layouts con la misma letra 'S'
    layout1 = MatrixLayout("S")
    layout1._register_spec('S', {'type': 'scatter', 'data': sample_df1.to_dict('records'), 'x_col': 'x'})
    
    layout2 = MatrixLayout("S")
    layout2._register_spec('S', {'type': 'scatter', 'data': sample_df2.to_dict('records'), 'x_col': 'a'})
    
    # Verificar que cada layout tiene su propio spec
    assert layout1._map['S']['x_col'] == 'x'
    assert layout2._map['S']['x_col'] == 'a'
    
    # Verificar que los datos son diferentes
    assert layout1._map['S']['data'] != layout2._map['S']['data']


def test_reactive_layout_independent_from_matrix_layout(sample_df1, sample_df2):
    """
    Verifica que ReactiveMatrixLayout no interfiera con MatrixLayout.
    """
    # Crear MatrixLayout con letra 'A'
    matrix_layout = MatrixLayout("A")
    matrix_layout._register_spec('A', {'type': 'scatter', 'data': sample_df1.to_dict('records')})
    
    # Crear ReactiveMatrixLayout con letra 'B'
    reactive_layout = ReactiveMatrixLayout("B")
    reactive_layout._layout._register_spec('B', {'type': 'bar', 'data': sample_df2.to_dict('records')})
    
    # Verificar que no interfieren
    assert 'A' in matrix_layout._map
    assert 'B' not in matrix_layout._map
    
    assert 'B' in reactive_layout._layout._map
    assert 'A' not in reactive_layout._layout._map


def test_multiple_reactive_layouts_independent(sample_df1, sample_df2):
    """
    Verifica que múltiples ReactiveMatrixLayout no interfieran entre sí.
    """
    # Crear primer ReactiveMatrixLayout con layout "SB"
    layout1 = ReactiveMatrixLayout("SB")
    layout1.set_data(sample_df1)
    layout1.add_scatter('S', x_col='x', y_col='y', category_col='category')
    layout1.add_barchart('B', category_col='category')
    
    # Crear segundo ReactiveMatrixLayout con layout "XY"
    layout2 = ReactiveMatrixLayout("XY")
    layout2.set_data(sample_df2)
    layout2.add_scatter('X', x_col='a', y_col='b', category_col='group')
    layout2.add_barchart('Y', category_col='group')
    
    # Verificar que cada layout tiene solo sus letras
    assert 'S' in layout1._layout._map
    assert 'B' in layout1._layout._map
    assert 'X' not in layout1._layout._map
    assert 'Y' not in layout1._layout._map
    
    assert 'X' in layout2._layout._map
    assert 'Y' in layout2._layout._map
    assert 'S' not in layout2._layout._map
    assert 'B' not in layout2._layout._map


def test_layout_with_extra_letters_in_map_renders_only_layout_letters(sample_df1, sample_df2):
    """
    Verifica que si _map tiene letras extra, solo se renderizan las del layout actual.
    """
    layout = MatrixLayout("A")
    
    # Agregar specs para letras que no están en el layout
    layout._register_spec('A', {'type': 'scatter', 'data': sample_df1.to_dict('records')})
    layout._register_spec('B', {'type': 'bar', 'data': sample_df2.to_dict('records')})
    layout._register_spec('C', {'type': 'histogram', 'data': []})
    
    # Preparar datos para renderizado
    data = layout._prepare_repr_data()
    
    # Verificar que solo 'A' está en el mapping final (y metadatos)
    mapping_merged = data['mapping_merged']
    
    # Filtrar metadatos (claves que empiezan con __)
    chart_letters = {k for k in mapping_merged.keys() if not k.startswith('__')}
    
    # Solo debe tener 'A'
    assert chart_letters == {'A'}
    assert 'B' not in chart_letters
    assert 'C' not in chart_letters


def test_no_error_when_layout_has_unmapped_letters(sample_df1):
    """
    Verifica que no hay error si el layout tiene letras sin specs (solo warning en debug).
    """
    layout = MatrixLayout("ABC")
    
    # Solo agregar spec para 'A'
    layout._register_spec('A', {'type': 'scatter', 'data': sample_df1.to_dict('records')})
    
    # Preparar datos para renderizado (no debe lanzar excepción)
    try:
        data = layout._prepare_repr_data()
        # Verificar que 'A' está en el mapping
        assert 'A' in data['mapping_merged']
    except Exception as e:
        pytest.fail(f"No debería lanzar excepción: {e}")


def test_reactive_layout_with_complex_grid(sample_df1):
    """
    Verifica que un ReactiveMatrixLayout con grid complejo funciona correctamente.
    """
    layout = ReactiveMatrixLayout("""
SSH
BXP
""")
    layout.set_data(sample_df1)
    
    # Agregar charts
    layout.add_scatter('S', x_col='x', y_col='y', category_col='category')
    layout.add_histogram('H', column='x')
    layout.add_barchart('B', category_col='category')
    layout.add_boxplot('X', column='y', category_col='category')
    layout.add_pie('P', category_col='category')
    
    # Verificar que todas las letras están en el map
    assert 'S' in layout._layout._map
    assert 'H' in layout._layout._map
    assert 'B' in layout._layout._map
    assert 'X' in layout._layout._map
    assert 'P' in layout._layout._map
    
    # Verificar que no hay letras extra
    chart_letters = {k for k in layout._layout._map.keys() if not k.startswith('__')}
    assert chart_letters == {'S', 'H', 'B', 'X', 'P'}

