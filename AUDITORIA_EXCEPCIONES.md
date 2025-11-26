# Auditoría de Manejo de Excepciones en BESTLIB

**Fecha:** Diciembre 2024  
**Alcance:** Todos los bloques `except Exception:` y `except:` en BESTLIB  
**Estado:** Auditoría completa con clasificación y recomendaciones

---

## Resumen Ejecutivo

### Estadísticas

- **Total de bloques `except Exception:` o `except:`:** 372+
- **Categorías:**
  - Imports opcionales: ~40% (ACEPTABLE)
  - Compatibilidad/fallbacks: ~30% (REVISAR)
  - Silenciamiento de errores: ~20% (PROBLEMÁTICO)
  - Otros: ~10%

### Evaluación

| Categoría | Estado | Acción |
|-----------|--------|--------|
| Imports opcionales | ✅ ACEPTABLE | Mantener pero documentar mejor |
| Compatibilidad | ⚠️ REVISAR | Algunos son necesarios, otros no |
| Silenciamiento | ❌ PROBLEMÁTICO | Reemplazar por logging |
| Legacy code | ⚠️ TOLERABLE | Se eliminarán con el código legacy |

---

## Clasificación Detallada

### 1. Imports Opcionales (ACEPTABLE)

**Patrón:**
```python
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None
```

**Ubicaciones:**
- Todos los módulos de charts/
- layouts/matrix.py
- layouts/reactive.py
- data/validators.py, preparators.py

**Evaluación:** ✅ **CORRECTO**
- Permite que BESTLIB funcione sin todas las dependencias
- Patrón estándar para dependencias opcionales
- Bien documentado con flags HAS_*

**Recomendación:** MANTENER tal cual

---

### 2. Imports de Charts con Silenciamiento (ACEPTABLE con mejoras)

**Patrón en charts/__init__.py:**
```python
try:
    from .scatter import ScatterChart
except (ImportError, AttributeError, Exception):
    pass
```

**Ubicación:** `BESTLIB/charts/__init__.py` (29 bloques)

**Problema:**
- `except Exception:` es muy amplio
- Puede ocultar errores de sintaxis en los archivos de charts

**Evaluación:** ⚠️ **MEJORABLE**

**Solución propuesta:**
```python
try:
    from .scatter import ScatterChart
except (ImportError, ModuleNotFoundError) as e:
    # Chart no disponible, log pero continuar
    import logging
    logging.getLogger('BESTLIB').debug(f"ScatterChart no disponible: {e}")
    ScatterChart = None
```

**Beneficio:** 
- Captura solo errores de import
- Errores de sintaxis se propagan
- Logging ayuda a debugging

---

### 3. Fallbacks de Compatibilidad (REVISAR CASO POR CASO)

**Patrón:**
```python
try:
    from .layouts.matrix import MatrixLayout
except (ImportError, ModuleNotFoundError, AttributeError):
    try:
        from .matrix import MatrixLayout
    except ImportError:
        MatrixLayout = None
```

**Ubicación:** Ya corregido en nuevo `__init__.py` ✅

**Evaluación:** ✅ **RESUELTO** en código modular, ⚠️ **TOLERABLE** en legacy

---

### 4. Silenciamiento de Errores en Comm/Events (PROBLEMÁTICO)

**Patrón en código legacy:**
```python
try:
    CommManager.register_comm()
except Exception:
    # Silenciar errores si no estamos en Jupyter
    pass
```

**Ubicaciones:**
- `BESTLIB/__init__.py` (nuevo, líneas 169-176)
- `BESTLIB/matrix.py` (legacy, múltiples)
- `BESTLIB/reactive.py` (legacy, múltiples)

**Problema:**
- Puede ocultar errores reales de comm registration
- No hay logging de qué falló
- Dificulta debugging

**Evaluación:** ⚠️ **MEJORABLE en código modular**, ❌ **PROBLEMÁTICO en legacy**

**Solución propuesta para código modular:**
```python
import logging
logger = logging.getLogger('BESTLIB')

try:
    CommManager.register_comm()
except ImportError as e:
    # No estamos en Jupyter, esto es esperado
    logger.debug(f"Comm no registrado (no en Jupyter): {e}")
except Exception as e:
    # Error inesperado, loggear con warning
    logger.warning(f"Error al registrar comm: {e}")
```

---

### 5. Conversión de Datos con Silenciamiento (PROBLEMÁTICO)

**Patrón encontrado:**
```python
try:
    df = pd.DataFrame(items)
except Exception:
    # Si falla conversión, usar lista
    df = items
```

**Ubicaciones:**
- `layouts/reactive.py` (múltiples callbacks de actualización)
- Código de selección y linking

**Problema:**
- Errores reales de datos se ocultan
- Usuario no sabe por qué falló la conversión

**Solución propuesta:**
```python
try:
    df = pd.DataFrame(items)
except (ValueError, TypeError) as e:
    logger.warning(f"No se pudo convertir items a DataFrame: {e}. Usando lista.")
    df = items
except Exception as e:
    logger.error(f"Error inesperado al convertir a DataFrame: {e}")
    raise  # Re-raise errores inesperados
```

---

### 6. Pandas Corrupto Detection (ACEPTABLE pero mejorable)

**Patrón encontrado:**
```python
try:
    pd_test = sys.modules['pandas']
    _ = pd_test.__version__
except (AttributeError, ImportError):
    del sys.modules['pandas']
    # ... limpiar submódulos
```

**Ubicaciones:**
- Múltiples módulos (matrix.py, reactive.py, layouts/matrix.py, charts/scatter.py, etc.)

**Evaluación:** ✅ **NECESARIO** (workaround para bug de pandas)

**Mejora propuesta:**
- Centralizar en un solo helper en `utils/pandas_compat.py`
- Todos los módulos importan desde allí
- Logging cuando se detecta pandas corrupto

---

## Recomendaciones Prioritarias

### ALTA PRIORIDAD (Hacer Ahora)

1. **Centralizar detección de pandas corrupto**
   - Crear `BESTLIB/utils/pandas_compat.py`
   - Exportar `get_pandas()` que maneja la detección
   - Reemplazar código duplicado en todos los módulos

2. **Mejorar silenciamiento en código modular**
   - En `layouts/matrix.py` y `layouts/reactive.py`
   - Añadir logging para errores de comm/eventos
   - Capturar excepciones específicas en lugar de `Exception`

3. **Añadir logging module**
   - Crear `BESTLIB/utils/logging.py` con logger configurado
   - Usar en lugar de `print()` para mensajes de debug
   - Diferentes niveles: DEBUG, INFO, WARNING, ERROR

### MEDIA PRIORIDAD (Hacer Pronto)

4. **Mejorar imports de charts/**
   - En `charts/__init__.py`
   - Capturar solo `ImportError`, `ModuleNotFoundError`
   - Log cuando un chart no está disponible

5. **Validar datos con excepciones claras**
   - En `data/validators.py`
   - Lanzar `DataError` con mensajes específicos
   - No silenciar errores de validación

### BAJA PRIORIDAD (Código Legacy)

6. **No modificar `except Exception:` en legacy**
   - `BESTLIB/matrix.py`
   - `BESTLIB/reactive.py`
   - Se eliminarán en v0.2.0

---

## Plan de Implementación

### Fase 1: Centralizar Pandas Detection (AHORA)

**Crear:** `BESTLIB/utils/pandas_compat.py`

```python
"""
Helper para detección y manejo de pandas corrupto
"""
import logging
import sys

logger = logging.getLogger('BESTLIB.pandas')

_HAS_PANDAS = None
_pd = None


def get_pandas():
    """
    Obtiene pandas de forma segura, manejando el caso de pandas corrupto.
    
    Returns:
        tuple: (HAS_PANDAS: bool, pd: module or None)
    """
    global _HAS_PANDAS, _pd
    
    if _HAS_PANDAS is not None:
        return _HAS_PANDAS, _pd
    
    try:
        # Verificar que pandas no esté parcialmente inicializado
        if 'pandas' in sys.modules:
            try:
                pd_test = sys.modules['pandas']
                _ = pd_test.__version__
            except (AttributeError, ImportError) as e:
                logger.warning(f"Pandas detectado corrupto, limpiando: {e}")
                del sys.modules['pandas']
                modules_to_remove = [k for k in list(sys.modules.keys()) 
                                    if k.startswith('pandas.')]
                for mod in modules_to_remove:
                    try:
                        del sys.modules[mod]
                    except Exception:
                        pass
        
        import pandas as pd
        _ = pd.__version__
        _HAS_PANDAS = True
        _pd = pd
        logger.debug(f"Pandas {pd.__version__} disponible")
        
    except (ImportError, ModuleNotFoundError) as e:
        logger.debug(f"Pandas no disponible: {e}")
        _HAS_PANDAS = False
        _pd = None
    except Exception as e:
        logger.error(f"Error inesperado al importar pandas: {e}")
        _HAS_PANDAS = False
        _pd = None
    
    return _HAS_PANDAS, _pd


# Uso en otros módulos:
# from ..utils.pandas_compat import get_pandas
# HAS_PANDAS, pd = get_pandas()
```

**Beneficio:**
- Eliminar ~200 líneas de código duplicado
- Mejor logging
- Manejo centralizado de errores

---

### Fase 2: Añadir Logging Module (AHORA)

**Crear:** `BESTLIB/utils/logging_config.py`

```python
"""
Configuración de logging para BESTLIB
"""
import logging


def get_logger(name='BESTLIB'):
    """
    Obtiene logger configurado para BESTLIB.
    
    Args:
        name: Nombre del logger (default: 'BESTLIB')
    
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Solo configurar si no tiene handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(name)s] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Por defecto, solo WARNING y superiores
        logger.setLevel(logging.WARNING)
    
    return logger


def set_log_level(level):
    """
    Establece el nivel de logging para BESTLIB.
    
    Args:
        level: 'DEBUG', 'INFO', 'WARNING', 'ERROR', o logging.LEVEL
    """
    logger = get_logger()
    
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    logger.setLevel(level)


# Uso en otros módulos:
# from ..utils.logging_config import get_logger
# logger = get_logger(__name__)
# logger.warning("Algo pasó")
```

---

### Fase 3: Aplicar en Código Modular (AHORA)

**Prioridad en:**
1. `BESTLIB/layouts/matrix.py`
2. `BESTLIB/layouts/reactive.py`
3. `BESTLIB/core/comm.py`
4. `BESTLIB/core/events.py`

**Reemplazar:**
```python
# ❌ ANTES
try:
    CommManager.register_comm()
except Exception:
    pass

# ✅ DESPUÉS
from ..utils.logging_config import get_logger
logger = get_logger(__name__)

try:
    CommManager.register_comm()
except ImportError as e:
    logger.debug(f"Comm no registrado (no en Jupyter): {e}")
except Exception as e:
    logger.warning(f"Error al registrar comm: {e}")
```

---

## Implementación Específica por Módulo

### BESTLIB/charts/__init__.py

**Problema actual:**
```python
try:
    from .scatter import ScatterChart
except (ImportError, AttributeError, Exception):
    pass
```

**Solución:**
```python
import logging
logger = logging.getLogger('BESTLIB.charts')

try:
    from .scatter import ScatterChart
except (ImportError, ModuleNotFoundError) as e:
    logger.debug(f"ScatterChart no disponible: {e}")
    ScatterChart = None
except Exception as e:
    logger.error(f"Error inesperado importando ScatterChart: {e}")
    raise  # Re-raise errores inesperados
```

---

### BESTLIB/layouts/reactive.py

**Problema actual (múltiples ubicaciones):**
```python
except Exception as e:
    # Silenciar error de conversión
    pass
```

**Solución:**
```python
except (ValueError, TypeError) as e:
    logger.warning(f"Error de conversión: {e}")
    # Fallback apropiado
except Exception as e:
    logger.error(f"Error inesperado: {e}")
    raise
```

---

### BESTLIB/__init__.py (Nuevo)

**Estado actual:**
```python
try:
    CommManager.register_comm()
    try:
        MatrixLayout.register_comm()
    except Exception:
        pass
except Exception:
    pass
```

**Mejora propuesta:**
```python
import logging
logger = logging.getLogger('BESTLIB')

try:
    CommManager.register_comm()
    try:
        MatrixLayout.register_comm()
    except ImportError:
        logger.debug("MatrixLayout.register_comm() no disponible (no en Jupyter)")
    except Exception as e:
        logger.warning(f"Error al registrar comm en MatrixLayout: {e}")
except ImportError:
    logger.debug("CommManager no disponible (no en Jupyter)")
except Exception as e:
    logger.warning(f"Error al registrar comm: {e}")
```

---

## Decisiones de Diseño

### ✅ Cuándo usar `except Exception:` es ACEPTABLE:

1. **Top-level de módulos/archivos** cuando se importan en entornos variados (scripts, Jupyter, tests)
2. **Callbacks de Jupyter** que no deben romper el kernel
3. **Código de inicialización** que no debe impedir que la librería se cargue

### ❌ Cuándo es PROBLEMÁTICO:

1. **Dentro de lógica de negocio** (preparación de datos, validación, renderizado)
2. **Cuando oculta errores de usuario** (datos inválidos, parámetros incorrectos)
3. **Cuando no hay logging** de qué falló

---

## Plan de Acción

### Código Modular (Hacer AHORA)

1. ✅ Crear `utils/pandas_compat.py` - Centralizar detección de pandas
2. ✅ Crear `utils/logging_config.py` - Configurar logging
3. ⏳ Aplicar en `layouts/matrix.py`
4. ⏳ Aplicar en `layouts/reactive.py`
5. ⏳ Aplicar en `core/comm.py`
6. ⏳ Aplicar en `charts/__init__.py`

### Código Legacy (NO modificar)

- ❌ NO modificar `matrix.py` legacy
- ❌ NO modificar `reactive.py` legacy
- Se eliminarán en v0.2.0 de todas formas

---

## Métricas de Mejora

### Antes (Estado actual)

- `except Exception:` genéricos: 372+
- Logging: Mínimo (solo `print()` en debug)
- Errores silenciados: ~20% de los casos

### Después (Meta para v0.1.5)

- `except Exception:` reducidos a <50 en código modular
- Logging estructurado en todos los módulos core
- Errores silenciados: <5% (solo casos justificados)

### Después (Meta para v0.2.0)

- `except Exception:` solo en casos justificados (<20 total)
- Logging completo con niveles apropiados
- Todos los errores reportados apropiadamente

---

## Conclusión

### Estado Actual

- ⚠️ Manejo de excepciones mejorable pero no crítico
- ✅ Imports opcionales bien manejados
- ❌ Algunos silenciamientos problemáticos en código modular
- ⚠️ Legacy code tiene muchos problemas pero será eliminado

### Acciones Inmediatas

1. ✅ Crear helpers de pandas y logging (documentado arriba)
2. ⏳ Aplicar en código modular (prioridad media)
3. ❌ Ignorar código legacy (será eliminado)

### Acciones Futuras (v0.2.0)

- Con eliminación de legacy, ~200+ `except Exception:` desaparecerán automáticamente
- Solo quedarán los necesarios en código modular
- Mantenimiento más fácil

---

**Última actualización:** Diciembre 2024  
**Estado:** ✅ Auditoría completada - Plan de mejora documentado

