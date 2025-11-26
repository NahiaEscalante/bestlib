"""
Tests para MatrixLayout

Tests básicos de creación y configuración (sin renderizado en Jupyter).
"""
import pytest


class TestMatrixLayoutCreation:
    """Tests de creación de MatrixLayout"""
    
    def test_create_simple_layout(self):
        """Test: Crear MatrixLayout simple"""
        from BESTLIB import MatrixLayout
        
        layout = MatrixLayout("A")
        assert layout is not None
        assert hasattr(layout, 'div_id')
        assert hasattr(layout, 'ascii_layout')
        assert layout.ascii_layout == "A"
    
    def test_create_complex_layout(self):
        """Test: Crear MatrixLayout con ASCII complejo"""
        from BESTLIB import MatrixLayout
        
        ascii_layout = """
        ABC
        DDD
        EFG
        """
        layout = MatrixLayout(ascii_layout)
        assert layout is not None
        assert hasattr(layout, '_grid')
    
    def test_create_with_figsize(self):
        """Test: Crear MatrixLayout con figsize"""
        from BESTLIB import MatrixLayout
        
        layout = MatrixLayout("A", figsize=(8, 6))
        assert layout is not None
        assert layout._figsize == (8, 6)
    
    def test_create_with_dimensions(self):
        """Test: Crear MatrixLayout con dimensiones personalizadas"""
        from BESTLIB import MatrixLayout
        
        layout = MatrixLayout(
            "AB",
            row_heights=[400],
            col_widths=[500, 500],
            gap=20,
            cell_padding=10
        )
        assert layout is not None
        assert layout._row_heights == [400]
        assert layout._col_widths == [500, 500]
        assert layout._gap == 20
        assert layout._cell_padding == 10


class TestMatrixLayoutMapping:
    """Tests de mapeo de gráficos"""
    
    def test_map_scatter_basic(self):
        """Test: map_scatter configura spec correctamente"""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas no está instalado")
        
        from BESTLIB import MatrixLayout
        
        # Datos de prueba
        df = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6],
            'species': ['A', 'A', 'B']
        })
        
        # Mapear scatter
        spec = MatrixLayout.map_scatter('S', df, 
                                       x_col='x', 
                                       y_col='y', 
                                       category_col='species')
        
        assert spec is not None
        assert spec['type'] == 'scatter'
        assert 'data' in spec
        assert len(spec['data']) == 3
    
    def test_map_barchart_basic(self):
        """Test: map_barchart configura spec correctamente"""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas no está instalado")
        
        from BESTLIB import MatrixLayout
        
        df = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 30]
        })
        
        spec = MatrixLayout.map_barchart('B', df, 
                                        category_col='category', 
                                        value_col='value')
        
        assert spec is not None
        assert spec['type'] == 'bar'
        assert 'data' in spec
    
    def test_map_histogram_basic(self):
        """Test: map_histogram configura spec correctamente"""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas no está instalado")
        
        from BESTLIB import MatrixLayout
        
        df = pd.DataFrame({
            'values': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })
        
        spec = MatrixLayout.map_histogram('H', df, value_col='values', bins=5)
        
        assert spec is not None
        assert spec['type'] == 'histogram'


class TestMatrixLayoutEvents:
    """Tests del sistema de eventos"""
    
    def test_register_event_handler(self):
        """Test: Registrar handler de evento"""
        from BESTLIB import MatrixLayout
        
        layout = MatrixLayout("A")
        
        called = {'count': 0}
        
        def handler(payload):
            called['count'] += 1
        
        layout.on('select', handler)
        assert layout._event_manager is not None
    
    def test_set_debug(self):
        """Test: set_debug activa/desactiva debug"""
        from BESTLIB import MatrixLayout
        
        MatrixLayout.set_debug(True)
        assert MatrixLayout._debug == True
        
        MatrixLayout.set_debug(False)
        assert MatrixLayout._debug == False


class TestReactiveMatrixLayout:
    """Tests para ReactiveMatrixLayout"""
    
    def test_create_reactive_layout(self):
        """Test: Crear ReactiveMatrixLayout"""
        from BESTLIB import ReactiveMatrixLayout, SelectionModel
        
        selection = SelectionModel()
        layout = ReactiveMatrixLayout("A", selection_model=selection)
        
        assert layout is not None
        assert hasattr(layout, 'add_scatter')
        assert hasattr(layout, 'add_barchart')
        assert hasattr(layout, 'set_data')
    
    def test_set_data(self):
        """Test: set_data configura datos"""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas no está instalado")
        
        from BESTLIB import ReactiveMatrixLayout, SelectionModel
        
        df = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })
        
        layout = ReactiveMatrixLayout("A", selection_model=SelectionModel())
        layout.set_data(df)
        
        assert layout._data is not None
        # Verificar que los datos se guardaron
        assert len(layout._data) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

