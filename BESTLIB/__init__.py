from .matrix import MatrixLayout

# Intentar importar módulo reactivo (opcional)
try:
    from .reactive import ReactiveMatrixLayout, SelectionModel
    HAS_REACTIVE = True
    __all__ = ["MatrixLayout", "ReactiveMatrixLayout", "SelectionModel"]
except ImportError:
    # Si ipywidgets no está instalado, solo exportar MatrixLayout
    HAS_REACTIVE = False
    __all__ = ["MatrixLayout"]

# Registrar automáticamente el comm al importar
# Esto asegura que la comunicación bidireccional funcione sin configuración extra
try:
    MatrixLayout.register_comm()
except Exception:
    # Silenciar errores si no estamos en Jupyter
    # (ej: al importar en scripts, tests, etc.)
    pass
