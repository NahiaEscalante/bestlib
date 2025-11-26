"""
Tests de compatibilidad con código legacy

Verifica que el código legacy aún funciona (con warnings) para mantener
compatibilidad hacia atrás hasta v0.2.0
"""
import pytest
import warnings


class TestLegacyMatrixLayoutCompat:
    """Tests de compatibilidad con MatrixLayout legacy"""
    
    def test_legacy_import_works(self):
        """Test: Import legacy funciona pero emite warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Import legacy
            from BESTLIB.matrix import MatrixLayout
            
            # Debe funcionar
            assert MatrixLayout is not None
            
            # Debe emitir DeprecationWarning
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
    
    def test_legacy_matrixlayout_creates_instance(self):
        """Test: MatrixLayout legacy puede crear instancia"""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            
            from BESTLIB.matrix import MatrixLayout
            
            layout = MatrixLayout("A")
            assert layout is not None
            assert hasattr(layout, 'div_id')


class TestLegacyReactiveCompat:
    """Tests de compatibilidad con ReactiveMatrixLayout legacy"""
    
    def test_legacy_reactive_import_works(self):
        """Test: Import reactive legacy funciona pero emite warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            from BESTLIB.reactive import ReactiveMatrixLayout
            
            assert ReactiveMatrixLayout is not None
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)


class TestLegacyCompatWrappers:
    """Tests para wrappers de compat/"""
    
    def test_compat_chart_wrappers_work(self):
        """Test: Wrappers de compat funcionan con warnings"""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas no está instalado")
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            from BESTLIB.compat import map_scatter
            
            df = pd.DataFrame({
                'x': [1, 2, 3],
                'y': [4, 5, 6]
            })
            
            # Debe funcionar
            spec = map_scatter('S', df, x_col='x', y_col='y')
            assert spec is not None
            assert spec['type'] == 'scatter'
            
            # Debe emitir DeprecationWarning
            assert len(w) >= 1


class TestModernAPIEquivalence:
    """Tests de equivalencia entre API legacy y moderna"""
    
    def test_matrixlayout_same_class(self):
        """Test: MatrixLayout de API pública es el mismo que el modular"""
        from BESTLIB import MatrixLayout
        from BESTLIB.layouts.matrix import MatrixLayout as ModularMatrixLayout
        
        # Deben ser la misma clase
        assert MatrixLayout is ModularMatrixLayout
    
    def test_reactive_matrixlayout_same_class(self):
        """Test: ReactiveMatrixLayout de API pública es el modular"""
        from BESTLIB import ReactiveMatrixLayout
        from BESTLIB.layouts.reactive import ReactiveMatrixLayout as ModularReactive
        
        # Deben ser la misma clase
        assert ReactiveMatrixLayout is ModularReactive


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

