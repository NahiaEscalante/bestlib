# Fix Completo: Import Defensivo de Pandas en Charts

## Problema

Cuando pandas está corrupto o parcialmente inicializado, BESTLIB fallaba al importar módulos de charts porque todos los archivos de `BESTLIB/charts/` importaban pandas al nivel del módulo.

**Error**:
```
AttributeError: partially initialized module 'pandas' has no attribute '_pandas_parser_CAPI' 
(most likely due to a circular import)
```

## Solución Aplicada

Se implementó un **import defensivo de pandas** en **TODOS** los archivos de charts que lo usan:

### Archivos con Pandas y Numpy (7 archivos):
1. `BESTLIB/charts/kde.py`
2. `BESTLIB/charts/rug.py`
3. `BESTLIB/charts/ecdf.py`
4. `BESTLIB/charts/qqplot.py`
5. `BESTLIB/charts/distplot.py`
6. `BESTLIB/charts/funnel.py`
7. `BESTLIB/charts/polar.py`
8. `BESTLIB/charts/hist2d.py`
9. `BESTLIB/charts/ridgeline.py`

### Archivos con Solo Pandas (7 archivos):
1. `BESTLIB/charts/scatter.py`
2. `BESTLIB/charts/ribbon.py`
3. `BESTLIB/charts/line_plot.py`
4. `BESTLIB/charts/hexbin.py`
5. `BESTLIB/charts/step_plot.py`
6. `BESTLIB/charts/fill_between.py`
7. `BESTLIB/charts/errorbars.py`

## Patrón de Import Defensivo

### Para archivos con Pandas y Numpy:

```python
# Import de pandas y numpy de forma defensiva para evitar errores de importación circular
HAS_PANDAS = False
HAS_NUMPY = False
pd = None
np = None
try:
    # Verificar que pandas no esté parcialmente inicializado
    import sys
    if 'pandas' in sys.modules:
        try:
            pd_test = sys.modules['pandas']
            _ = pd_test.__version__
        except (AttributeError, ImportError):
            del sys.modules['pandas']
            modules_to_remove = [k for k in sys.modules.keys() if k.startswith('pandas.')]
            for mod in modules_to_remove:
                try:
                    del sys.modules[mod]
                except:
                    pass
    import pandas as pd
    _ = pd.__version__
    HAS_PANDAS = True
except (ImportError, AttributeError, ModuleNotFoundError, Exception):
    HAS_PANDAS = False
    pd = None

try:
    import numpy as np
    HAS_NUMPY = True
except (ImportError, AttributeError, ModuleNotFoundError, Exception):
    HAS_NUMPY = False
    np = None
```

### Para archivos con Solo Pandas:

```python
# Import de pandas de forma defensiva para evitar errores de importación circular
HAS_PANDAS = False
pd = None
try:
    # Verificar que pandas no esté parcialmente inicializado
    import sys
    if 'pandas' in sys.modules:
        try:
            pd_test = sys.modules['pandas']
            _ = pd_test.__version__
        except (AttributeError, ImportError):
            del sys.modules['pandas']
            modules_to_remove = [k for k in sys.modules.keys() if k.startswith('pandas.')]
            for mod in modules_to_remove:
                try:
                    del sys.modules[mod]
                except:
                    pass
    import pandas as pd
    _ = pd.__version__
    HAS_PANDAS = True
except (ImportError, AttributeError, ModuleNotFoundError, Exception):
    HAS_PANDAS = False
    pd = None
```

## Archivos Modificados

**Total: 16 archivos en `BESTLIB/charts/`**

1. `kde.py` ✅
2. `rug.py` ✅
3. `ecdf.py` ✅
4. `qqplot.py` ✅
5. `distplot.py` ✅
6. `funnel.py` ✅
7. `polar.py` ✅
8. `hist2d.py` ✅
9. `ridgeline.py` ✅
10. `scatter.py` ✅
11. `ribbon.py` ✅
12. `line_plot.py` ✅
13. `hexbin.py` ✅
14. `step_plot.py` ✅
15. `fill_between.py` ✅
16. `errorbars.py` ✅

## Verificación

Ahora puedes importar BESTLIB charts incluso si pandas está corrupto:

```python
# Esto funcionará incluso si pandas está corrupto
from BESTLIB.charts import ChartRegistry
from BESTLIB.charts.kde import KdeChart
print("✅ Funciona!")
```

## Beneficios

✅ **BESTLIB charts pueden importarse incluso si pandas está corrupto**
✅ **Limpia automáticamente pandas corrupto antes de importar**
✅ **No rompe la funcionalidad si pandas no está disponible**
✅ **Permite que el usuario reinicie pandas después de importar BESTLIB**

## Resumen Total de Fixes

**Archivos con import defensivo de pandas:**
- ✅ `BESTLIB/layouts/matrix.py`
- ✅ `BESTLIB/matrix.py`
- ✅ `BESTLIB/layouts/reactive.py`
- ✅ `BESTLIB/reactive.py`
- ✅ **16 archivos en `BESTLIB/charts/`** (este fix)

**Total: 20 archivos** con import defensivo de pandas

## Nota Importante

Este fix **no soluciona el problema de pandas corrupto**, pero permite que BESTLIB se importe correctamente incluso en ese escenario. Si pandas está corrupto, el usuario aún necesitará:

1. Reiniciar el runtime/kernel (recomendado), O
2. Reinstalar pandas: `!pip uninstall -y pandas && !pip install pandas`

Pero ahora BESTLIB no fallará al importarse debido a pandas corrupto, **ni siquiera al importar módulos de charts**.

