from .matrix import MatrixLayout

# Registrar automáticamente el comm al importar
# Esto asegura que la comunicación bidireccional funcione sin configuración extra
try:
    MatrixLayout.register_comm()
except Exception:
    # Silenciar errores si no estamos en Jupyter
    # (ej: al importar en scripts, tests, etc.)
    pass

__all__ = ["MatrixLayout"]
