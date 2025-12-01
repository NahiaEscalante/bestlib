"""
Reactive module - Sistema reactivo para BESTLIB
"""
from .selection import ReactiveData, SelectionModel
from .engine import ReactiveEngine
from .linking import LinkManager

# Re-exportar ReactiveMatrixLayout desde layouts para compatibilidad
# ReactiveMatrixLayout ahora está en layouts/reactive.py según estructura modular
# IMPORTANTE: Hacer import lazy para evitar problemas de import circular
# (layouts.reactive importa ..reactive.selection, y reactive/__init__.py importa .selection)

# Variable para cachear el import
_ReactiveMatrixLayout_cache = None

def __getattr__(name):
    """Import lazy de ReactiveMatrixLayout cuando se accede"""
    global _ReactiveMatrixLayout_cache
    if name == 'ReactiveMatrixLayout':
        if _ReactiveMatrixLayout_cache is None:
            try:
                # Intentar import absoluto primero (más confiable)
                from BESTLIB.layouts.reactive import ReactiveMatrixLayout
                _ReactiveMatrixLayout_cache = ReactiveMatrixLayout
            except (ImportError, ModuleNotFoundError, AttributeError):
                # Si falla, intentar import relativo
                try:
                    from ..layouts.reactive import ReactiveMatrixLayout
                    _ReactiveMatrixLayout_cache = ReactiveMatrixLayout
                except (ImportError, ModuleNotFoundError, AttributeError):
                    # Fallback: intentar desde reactive.py legacy (si existe)
                    try:
                        import importlib.util
                        from pathlib import Path
                        reactive_py = Path(__file__).parent.parent / "reactive.py"
                        if reactive_py.exists():
                            spec = importlib.util.spec_from_file_location("reactive_legacy", str(reactive_py))
                            if spec and spec.loader:
                                reactive_legacy = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(reactive_legacy)
                                _ReactiveMatrixLayout_cache = getattr(reactive_legacy, 'ReactiveMatrixLayout', None)
                    except Exception:
                        pass
        return _ReactiveMatrixLayout_cache
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Intentar import inmediato (puede fallar si hay import circular, pero intentamos)
try:
    from BESTLIB.layouts.reactive import ReactiveMatrixLayout
    _ReactiveMatrixLayout_cache = ReactiveMatrixLayout
except (ImportError, ModuleNotFoundError, AttributeError):
    # Si falla, se usará __getattr__ cuando se acceda
    pass

__all__ = ['ReactiveData', 'SelectionModel', 'ReactiveEngine', 'LinkManager', 'ReactiveMatrixLayout']
# ReactiveMatrixLayout se carga de forma lazy usando __getattr__
# Siempre está en __all__ para que esté disponible cuando se acceda

