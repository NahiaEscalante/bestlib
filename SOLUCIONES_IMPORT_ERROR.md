# 🔧 Soluciones Propuestas para el Error de Importación

## 📋 Análisis del Problema

**Error:** `ModuleNotFoundError: No module named 'BESTLIB.core'`

**Causa raíz:**
- El `__init__.py` está importando desde `.core`, `.data`, y `.utils` de forma **obligatoria** (sin try/except)
- Cuando el usuario tiene una versión instalada de BESTLIB que no tiene la estructura modular completa, falla
- El import `from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel` falla porque `__init__.py` se ejecuta primero y falla al intentar importar `.core`

**Ubicación del error:**
- `BESTLIB/__init__.py` línea 56: `from .core import (...)`
- `BESTLIB/__init__.py` línea 100: `from .data import (...)`
- `BESTLIB/__init__.py` línea 115: `from .utils import (...)`

---

## 💡 Soluciones Propuestas

### ✅ **Solución 1: Hacer todos los imports modulares opcionales (RECOMENDADA)**

**Ventajas:**
- ✅ Mantiene compatibilidad hacia atrás
- ✅ Permite que BESTLIB funcione con o sin estructura modular
- ✅ No rompe código existente
- ✅ Permite migración gradual

**Desventajas:**
- ⚠️ Algunas funcionalidades avanzadas no estarán disponibles si faltan módulos
- ⚠️ Necesita manejo de errores más cuidadoso

**Implementación:**
```python
# Core module - OPCIONAL
try:
    from .core import (
        BestlibError,
        LayoutError,
        ChartError,
        DataError,
        RenderError,
        CommunicationError,
        Registry,
        LayoutEngine,
        CommManager,
        EventManager,
        get_comm_engine
    )
    HAS_CORE = True
except ImportError:
    HAS_CORE = False
    # Crear clases stub o None
    BestlibError = Exception
    LayoutError = Exception
    ChartError = Exception
    DataError = Exception
    RenderError = Exception
    CommunicationError = Exception
    Registry = None
    LayoutEngine = None
    CommManager = None
    EventManager = None
    get_comm_engine = None

# Data module - OPCIONAL
try:
    from .data import (
        prepare_scatter_data,
        prepare_bar_data,
        # ... etc
    )
    HAS_DATA = True
except ImportError:
    HAS_DATA = False
    # Funciones stub o None
    prepare_scatter_data = None
    # ... etc

# Utils module - OPCIONAL
try:
    from .utils import sanitize_for_json, figsize_to_pixels
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False
    sanitize_for_json = lambda x: x  # Función stub
    figsize_to_pixels = None
```

---

### ✅ **Solución 2: Importación lazy (diferida)**

**Ventajas:**
- ✅ No falla al importar BESTLIB
- ✅ Solo carga módulos cuando se usan
- ✅ Mejor rendimiento inicial

**Desventajas:**
- ⚠️ Errores aparecen más tarde (cuando se usa)
- ⚠️ Más complejo de implementar

**Implementación:**
```python
# En lugar de importar directamente, usar propiedades lazy
class _LazyCore:
    def __getattr__(self, name):
        try:
            from .core import *
            return globals()[name]
        except ImportError:
            raise AttributeError(f"Module 'core' not available. {name} not found")

_core = _LazyCore()
BestlibError = _core.BestlibError  # Solo se importa cuando se accede
```

---

### ✅ **Solución 3: Detectar versión y usar fallback**

**Ventajas:**
- ✅ Detecta automáticamente qué versión tiene el usuario
- ✅ Usa código legacy si no hay módulos modulares

**Desventajas:**
- ⚠️ Más complejo
- ⚠️ Necesita mantener dos versiones del código

**Implementación:**
```python
import os
from pathlib import Path

# Detectar si tenemos estructura modular
_has_modular_structure = (
    (Path(__file__).parent / "core" / "__init__.py").exists() and
    (Path(__file__).parent / "data" / "__init__.py").exists()
)

if _has_modular_structure:
    # Usar versión modular
    from .core import *
    from .data import *
else:
    # Usar versión legacy (sin módulos)
    # Definir clases/funciones básicas o importar desde otros lugares
    pass
```

---

### ✅ **Solución 4: Separar imports en módulos específicos**

**Ventajas:**
- ✅ Usuario puede importar solo lo que necesita
- ✅ No falla si falta algo

**Desventajas:**
- ⚠️ Cambia la API (breaking change)
- ⚠️ Requiere actualizar todos los imports

**Implementación:**
```python
# Usuario importa así:
from BESTLIB.basic import MatrixLayout  # Siempre funciona
from BESTLIB.reactive import ReactiveMatrixLayout  # Solo si existe
from BESTLIB.charts import ChartRegistry  # Solo si existe
```

---

## 🎯 **Recomendación: Solución 1 (Imports Opcionales)**

**Razones:**
1. ✅ Mantiene compatibilidad hacia atrás
2. ✅ No rompe código existente
3. ✅ Permite que BESTLIB funcione en ambos escenarios
4. ✅ Fácil de implementar
5. ✅ El usuario puede seguir usando `from BESTLIB.reactive import ...`

---

## 📝 Plan de Implementación (Solución 1)

### Paso 1: Hacer `.core` opcional
```python
# Core module - OPCIONAL
try:
    from .core import (
        BestlibError, LayoutError, ChartError, DataError,
        RenderError, CommunicationError, Registry, LayoutEngine,
        CommManager, EventManager, get_comm_engine
    )
    HAS_CORE = True
except ImportError:
    HAS_CORE = False
    # Clases base para compatibilidad
    class BestlibError(Exception): pass
    class LayoutError(BestlibError): pass
    class ChartError(BestlibError): pass
    class DataError(BestlibError): pass
    class RenderError(BestlibError): pass
    class CommunicationError(BestlibError): pass
    Registry = None
    LayoutEngine = None
    CommManager = None
    EventManager = None
    get_comm_engine = None
```

### Paso 2: Hacer `.data` opcional
```python
# Data module - OPCIONAL
try:
    from .data import (
        prepare_scatter_data, prepare_bar_data, prepare_histogram_data,
        prepare_boxplot_data, prepare_heatmap_data, prepare_line_data,
        prepare_pie_data, validate_scatter_data, validate_bar_data,
        dataframe_to_dicts, dicts_to_dataframe
    )
    HAS_DATA = True
except ImportError:
    HAS_DATA = False
    # Funciones stub (pueden retornar None o hacer passthrough)
    def prepare_scatter_data(*args, **kwargs):
        return kwargs.get('data')
    # ... etc para otras funciones
```

### Paso 3: Hacer `.utils` opcional
```python
# Utils module - OPCIONAL
try:
    from .utils import sanitize_for_json, figsize_to_pixels
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False
    # Funciones stub básicas
    def sanitize_for_json(obj):
        """Stub básico - solo convierte tipos numpy básicos"""
        import json
        if hasattr(obj, 'item'):  # numpy types
            return obj.item()
        if hasattr(obj, 'tolist'):  # numpy arrays
            return obj.tolist()
        return obj
    
    def figsize_to_pixels(figsize):
        if figsize is None:
            return None
        if isinstance(figsize, (tuple, list)) and len(figsize) == 2:
            w, h = figsize
            return (int(w * 96), int(h * 96)) if w <= 50 else (int(w), int(h))
        return figsize
```

### Paso 4: Actualizar `__all__` condicionalmente
```python
__all__ = [
    "MatrixLayout",
    # ... otros básicos
]

if HAS_CORE:
    __all__.extend([
        "BestlibError", "LayoutError", "ChartError", "DataError",
        "RenderError", "CommunicationError", "Registry", "LayoutEngine",
        "CommManager", "EventManager", "get_comm_engine"
    ])

if HAS_DATA:
    __all__.extend([
        "prepare_scatter_data", "prepare_bar_data", # ... etc
    ])

if HAS_UTILS:
    __all__.extend(["sanitize_for_json", "figsize_to_pixels"])
```

---

## 🧪 Testing

Después de implementar, probar:

1. ✅ `from BESTLIB.reactive import ReactiveMatrixLayout, SelectionModel` (debe funcionar)
2. ✅ `from BESTLIB import ChartRegistry` (debe funcionar si existe)
3. ✅ `from BESTLIB.matrix import MatrixLayout` (debe funcionar siempre)
4. ✅ Verificar que código legacy sigue funcionando
5. ✅ Verificar que código modular sigue funcionando

---

## 📌 Notas Adicionales

- **Compatibilidad:** La Solución 1 mantiene compatibilidad hacia atrás
- **Performance:** Los imports opcionales no afectan el rendimiento
- **Documentación:** Actualizar docs para indicar qué módulos son opcionales
- **Versioning:** Considerar versionar BESTLIB para indicar si tiene estructura modular

