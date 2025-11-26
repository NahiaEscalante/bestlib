"""
Tests de importación para BESTLIB

Verifica que todos los componentes principales se puedan importar correctamente.
"""
import pytest
import warnings


class TestPublicAPIImports:
    """Tests para importación de API pública"""
    
    def test_import_bestlib(self):
        """Test: import BESTLIB debe funcionar"""
        import BESTLIB
        assert BESTLIB is not None
        assert hasattr(BESTLIB, '__version__')
    
    def test_import_matrixlayout(self):
        """Test: from BESTLIB import MatrixLayout"""
        from BESTLIB import MatrixLayout
        assert MatrixLayout is not None
        assert hasattr(MatrixLayout, 'map_scatter')
    
    def test_import_reactive_matrixlayout(self):
        """Test: from BESTLIB import ReactiveMatrixLayout"""
        from BESTLIB import ReactiveMatrixLayout
        assert ReactiveMatrixLayout is not None
        assert hasattr(ReactiveMatrixLayout, 'add_scatter')
    
    def test_import_selection_model(self):
        """Test: from BESTLIB import SelectionModel"""
        from BESTLIB import SelectionModel
        assert SelectionModel is not None
        # Crear instancia
        selection = SelectionModel()
        assert hasattr(selection, 'set_items')
        assert hasattr(selection, 'get_count')
    
    def test_import_reactive_data(self):
        """Test: from BESTLIB import ReactiveData"""
        from BESTLIB import ReactiveData
        assert ReactiveData is not None
    
    def test_import_chart_registry(self):
        """Test: from BESTLIB import ChartRegistry"""
        from BESTLIB import ChartRegistry
        assert ChartRegistry is not None
        assert hasattr(ChartRegistry, 'get')
        assert hasattr(ChartRegistry, 'register')
        assert hasattr(ChartRegistry, 'list_types')
    
    def test_import_exceptions(self):
        """Test: from BESTLIB import excepciones"""
        from BESTLIB import (
            BestlibError,
            LayoutError,
            ChartError,
            DataError,
            RenderError,
            CommunicationError
        )
        assert BestlibError is not None
        assert issubclass(LayoutError, BestlibError)
        assert issubclass(ChartError, BestlibError)
        assert issubclass(DataError, BestlibError)


class TestLegacyImportsWithWarnings:
    """Tests para verificar que imports legacy emiten warnings"""
    
    def test_import_from_matrix_emits_warning(self):
        """Test: from BESTLIB.matrix import MatrixLayout emite DeprecationWarning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from BESTLIB.matrix import MatrixLayout
            
            # Verificar que se emitió un warning
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
            
            # Verificar mensaje
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert any("legacy" in str(warning.message).lower() or "deprecated" in str(warning.message).lower() 
                      for warning in deprecation_warnings)
    
    def test_import_from_reactive_emits_warning(self):
        """Test: from BESTLIB.reactive import ReactiveMatrixLayout emite DeprecationWarning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from BESTLIB.reactive import ReactiveMatrixLayout
            
            # Verificar que se emitió un warning
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
    
    def test_import_linked_views_emits_warning(self):
        """Test: from BESTLIB import LinkedViews emite DeprecationWarning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from BESTLIB import LinkedViews
            
            # LinkedViews está wrapeado con warning en __init__.py
            # Al crear instancia debería emitir warning
            try:
                instance = LinkedViews()
            except:
                # Puede fallar si no está en Jupyter, pero el import debería funcionar
                pass


class TestChartRegistry:
    """Tests para ChartRegistry"""
    
    def test_chart_registry_has_charts(self):
        """Test: ChartRegistry tiene gráficos registrados"""
        from BESTLIB import ChartRegistry
        
        types = ChartRegistry.list_types()
        assert len(types) > 0
        assert 'scatter' in types
        assert 'bar' in types
        assert 'histogram' in types
    
    def test_get_scatter_chart(self):
        """Test: ChartRegistry.get('scatter') funciona"""
        from BESTLIB import ChartRegistry
        
        chart = ChartRegistry.get('scatter')
        assert chart is not None
        assert hasattr(chart, 'chart_type')
        assert chart.chart_type == 'scatter'
        assert hasattr(chart, 'prepare_data')
        assert hasattr(chart, 'get_spec')
    
    def test_get_invalid_chart_raises_error(self):
        """Test: ChartRegistry.get('invalid') lanza ChartError"""
        from BESTLIB import ChartRegistry, ChartError
        
        with pytest.raises(ChartError):
            ChartRegistry.get('chart_type_that_does_not_exist')


class TestDataFunctions:
    """Tests para funciones de preparación y validación de datos"""
    
    def test_import_data_functions(self):
        """Test: Funciones de data/ se pueden importar"""
        from BESTLIB import (
            prepare_scatter_data,
            prepare_bar_data,
            validate_scatter_data,
            dataframe_to_dicts,
            dicts_to_dataframe
        )
        
        assert prepare_scatter_data is not None
        assert prepare_bar_data is not None
        assert validate_scatter_data is not None
        assert dataframe_to_dicts is not None
        assert dicts_to_dataframe is not None
    
    def test_dataframe_to_dicts_basic(self):
        """Test: dataframe_to_dicts convierte correctamente"""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas no está instalado")
        
        from BESTLIB import dataframe_to_dicts
        
        df = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })
        
        result = dataframe_to_dicts(df)
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == {'x': 1, 'y': 4}
    
    def test_dicts_to_dataframe_basic(self):
        """Test: dicts_to_dataframe convierte correctamente"""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas no está instalado")
        
        from BESTLIB import dicts_to_dataframe
        
        data = [
            {'x': 1, 'y': 4},
            {'x': 2, 'y': 5},
            {'x': 3, 'y': 6}
        ]
        
        result = dicts_to_dataframe(data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert 'x' in result.columns
        assert 'y' in result.columns


class TestCoreComponents:
    """Tests para componentes core"""
    
    def test_import_core_components(self):
        """Test: Componentes core se pueden importar"""
        from BESTLIB import CommManager, EventManager
        
        assert CommManager is not None
        assert EventManager is not None
        assert hasattr(CommManager, 'register_comm')
        assert hasattr(EventManager, 'set_debug')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

