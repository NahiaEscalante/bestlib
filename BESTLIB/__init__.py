from .matrix import MatrixLayout

# Intentar importar módulo reactivo (opcional)
try:
    from .reactive import ReactiveMatrixLayout, SelectionModel
    HAS_REACTIVE = True
except ImportError:
    HAS_REACTIVE = False
    ReactiveMatrixLayout = None
    SelectionModel = None

# Importar sistema de vistas enlazadas
try:
    from .linked import LinkedViews
    HAS_LINKED = True
except ImportError:
    HAS_LINKED = False
    LinkedViews = None

# Construir __all__ dinámicamente
__all__ = ["MatrixLayout"]

if HAS_REACTIVE:
    __all__.extend(["ReactiveMatrixLayout", "SelectionModel"])

if HAS_LINKED:
    __all__.append("LinkedViews")

# Registrar automáticamente el comm al importar
# Esto asegura que la comunicación bidireccional funcione sin configuración extra
try:
    MatrixLayout.register_comm()
except Exception:
    # Silenciar errores si no estamos en Jupyter
    # (ej: al importar en scripts, tests, etc.)
    pass
