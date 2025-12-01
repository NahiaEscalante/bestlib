"""
Tests básicos para BESTLIB
"""
import pytest
import pandas as pd
import numpy as np


class TestImports:
    """Tests de importación"""
    
    def test_import_bestlib(self):
        """Test que BESTLIB se puede importar"""
        import bestlib
        assert bestlib is not None
        
    def test_import_matrix_layout(self):
        """Test que MatrixLayout se puede importar"""
        from bestlib import MatrixLayout
        assert MatrixLayout is not None
        
    def test_import_reactive_layout(self):
        """Test que ReactiveMatrixLayout se puede importar"""
        from bestlib import ReactiveMatrixLayout
        assert ReactiveMatrixLayout is not None
        
    def test_version(self):
        """Test que la versión está definida"""
        import bestlib
        assert hasattr(bestlib, '__version__')
        assert bestlib.__version__ == "2.0.0"


class TestChartRegistry:
    """Tests para ChartRegistry"""
    
    def test_chart_registry_import(self):
        """Test que ChartRegistry se puede importar"""
        from bestlib import ChartRegistry
        assert ChartRegistry is not None
        
    def test_list_chart_types(self):
        """Test que list_chart_types funciona"""
        import bestlib
        chart_types = bestlib.list_chart_types()
        assert isinstance(chart_types, list)
        # Verificar que hay al menos algunos tipos básicos
        expected_types = ['scatter', 'bar', 'line', 'histogram']
        for t in expected_types:
            assert t in chart_types, f"Expected chart type '{t}' not found"


class TestMatrixLayout:
    """Tests para MatrixLayout"""
    
    def test_create_simple_layout(self):
        """Test crear layout simple"""
        from bestlib import MatrixLayout
        layout = MatrixLayout("A")
        assert layout is not None
        
    def test_create_2x2_layout(self):
        """Test crear layout 2x2"""
        from bestlib import MatrixLayout
        layout = MatrixLayout('''
            A | B
            --+--
            C | D
        ''')
        assert layout is not None
        
    def test_layout_with_data(self):
        """Test agregar datos al layout"""
        from bestlib import MatrixLayout
        
        df = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })
        
        layout = MatrixLayout("scatter")
        layout['scatter'] = {
            'type': 'scatter',
            'data': df,
            'x_col': 'x',
            'y_col': 'y'
        }
        assert layout is not None


class TestAPIHelpers:
    """Tests para API helpers"""
    
    def test_quick_scatter(self):
        """Test quick_scatter helper"""
        from bestlib.api import quick_scatter
        
        df = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })
        
        layout = quick_scatter(df, 'x', 'y')
        assert layout is not None
        
    def test_quick_bar(self):
        """Test quick_bar helper"""
        from bestlib.api import quick_bar
        
        df = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 30]
        })
        
        layout = quick_bar(df, 'category', 'value')
        assert layout is not None
        
    def test_quick_histogram(self):
        """Test quick_histogram helper"""
        from bestlib.api import quick_histogram
        
        df = pd.DataFrame({
            'value': np.random.randn(100)
        })
        
        layout = quick_histogram(df, 'value')
        assert layout is not None


class TestExceptions:
    """Tests para excepciones customizadas"""
    
    def test_import_exceptions(self):
        """Test que las excepciones se pueden importar"""
        from bestlib import ChartError, DataError, LayoutError
        assert ChartError is not None
        assert DataError is not None
        assert LayoutError is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
