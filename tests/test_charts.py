"""
Tests para Charts (ChartRegistry y clases de gráficos)
"""
import pytest


class TestChartRegistry:
    """Tests para ChartRegistry"""
    
    def test_list_available_charts(self):
        """Test: list_types() retorna tipos de gráficos"""
        from BESTLIB import ChartRegistry
        
        types = ChartRegistry.list_types()
        assert isinstance(types, list)
        assert len(types) > 0
        
        # Verificar que gráficos básicos estén registrados
        assert 'scatter' in types
        assert 'bar' in types
        assert 'histogram' in types
        assert 'boxplot' in types
        assert 'heatmap' in types
        assert 'line' in types
        assert 'pie' in types
    
    def test_get_existing_chart(self):
        """Test: get() retorna instancia de gráfico"""
        from BESTLIB import ChartRegistry
        
        chart = ChartRegistry.get('scatter')
        assert chart is not None
        assert chart.chart_type == 'scatter'
    
    def test_get_nonexistent_chart_raises_error(self):
        """Test: get() con tipo inválido lanza ChartError"""
        from BESTLIB import ChartRegistry, ChartError
        
        with pytest.raises(ChartError):
            ChartRegistry.get('nonexistent_chart_type')
    
    def test_is_registered(self):
        """Test: is_registered() verifica si un tipo está registrado"""
        from BESTLIB import ChartRegistry
        
        assert ChartRegistry.is_registered('scatter') == True
        assert ChartRegistry.is_registered('bar') == True
        assert ChartRegistry.is_registered('nonexistent') == False


class TestScatterChart:
    """Tests para ScatterChart"""
    
    def test_scatter_chart_type(self):
        """Test: ScatterChart tiene chart_type correcto"""
        from BESTLIB import ChartRegistry
        
        chart = ChartRegistry.get('scatter')
        assert chart.chart_type == 'scatter'
    
    def test_scatter_chart_has_required_methods(self):
        """Test: ScatterChart tiene métodos requeridos"""
        from BESTLIB import ChartRegistry
        
        chart = ChartRegistry.get('scatter')
        assert hasattr(chart, 'validate_data')
        assert hasattr(chart, 'prepare_data')
        assert hasattr(chart, 'get_spec')
    
    def test_scatter_chart_prepare_data(self):
        """Test: ScatterChart.prepare_data() funciona"""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas no está instalado")
        
        from BESTLIB import ChartRegistry
        
        df = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6],
            'species': ['A', 'A', 'B']
        })
        
        chart = ChartRegistry.get('scatter')
        processed, original = chart.prepare_data(
            df, 
            x_col='x', 
            y_col='y', 
            category_col='species'
        )
        
        assert isinstance(processed, list)
        assert len(processed) == 3
        assert 'x' in processed[0]
        assert 'y' in processed[0]
        assert 'category' in processed[0]


class TestBarChart:
    """Tests para BarChart"""
    
    def test_bar_chart_type(self):
        """Test: BarChart tiene chart_type correcto"""
        from BESTLIB import ChartRegistry
        
        chart = ChartRegistry.get('bar')
        assert chart.chart_type == 'bar'
    
    def test_bar_chart_get_spec(self):
        """Test: BarChart.get_spec() genera spec válido"""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas no está instalado")
        
        from BESTLIB import ChartRegistry
        
        df = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 30]
        })
        
        chart = ChartRegistry.get('bar')
        spec = chart.get_spec(df, category_col='category', value_col='value')
        
        assert spec is not None
        assert spec['type'] == 'bar'
        assert 'data' in spec
        assert isinstance(spec['data'], list)


class TestHistogramChart:
    """Tests para HistogramChart"""
    
    def test_histogram_chart_type(self):
        """Test: HistogramChart tiene chart_type correcto"""
        from BESTLIB import ChartRegistry
        
        chart = ChartRegistry.get('histogram')
        assert chart.chart_type == 'histogram'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

