# Fix: Sistema de Debug en BESTLIB

## Problema Corregido

**Error**: `AttributeError: type object 'MatrixLayout' has no attribute '_debug'`

**Causa**: 
- `MatrixLayout` tenía `set_debug()` pero `_debug` ya existía como variable de clase
- `ReactiveMatrixLayout` no tenía ni `_debug` ni `set_debug()`
- `ReactiveMatrixLayout` intentaba leer `MatrixLayout._debug` directamente, lo cual funcionaba pero no era consistente

## Solución Aplicada

### 1. MatrixLayout (`BESTLIB/matrix.py`)

✅ **Ya tenía** `_debug = False` como variable de clase (línea 31)
✅ **Mejorado** `set_debug()` para usar `bool(enabled)` para asegurar conversión correcta

**Cambio**:
```python
@classmethod
def set_debug(cls, enabled: bool):
    cls._debug = bool(enabled)  # Asegurar conversión a bool
```

### 2. ReactiveMatrixLayout (`BESTLIB/reactive.py`)

✅ **Agregado** `_debug = False` como variable de clase
✅ **Agregado** método `set_debug()` idéntico a `MatrixLayout`
✅ **Reemplazadas** todas las referencias a `MatrixLayout._debug` por `self._debug or MatrixLayout._debug`

**Cambios**:

1. **Variable de clase y método**:
```python
class ReactiveMatrixLayout:
    _debug = False  # Modo debug para ver mensajes detallados
    
    @classmethod
    def set_debug(cls, enabled: bool):
        """
        Activa/desactiva mensajes de debug.
        
        Args:
            enabled (bool): Si True, activa mensajes detallados de debug.
                           Si False, solo muestra errores críticos.
        """
        cls._debug = bool(enabled)
```

2. **Reemplazo de referencias** (37+ ocurrencias):
```python
# ANTES:
if MatrixLayout._debug:
    print(...)

# DESPUÉS:
if self._debug or MatrixLayout._debug:
    print(...)
```

Esto permite que `ReactiveMatrixLayout` tenga su propio sistema de debug independiente, pero también respete el debug de `MatrixLayout` para compatibilidad.

## Archivos Modificados

1. **`BESTLIB/matrix.py`**:
   - Mejorado `set_debug()` para usar `bool(enabled)`

2. **`BESTLIB/reactive.py`**:
   - Agregado `_debug = False` como variable de clase
   - Agregado método `set_debug()`
   - Reemplazadas todas las referencias a `MatrixLayout._debug` por `self._debug or MatrixLayout._debug`

## Uso

Ahora ambos sistemas funcionan correctamente:

```python
# Activar debug en MatrixLayout
MatrixLayout.set_debug(True)

# Activar debug en ReactiveMatrixLayout
ReactiveMatrixLayout.set_debug(True)

# Crear layout reactivo
layout = ReactiveMatrixLayout("AS\nHX")
layout.set_data(df)

# Funciona sin errores
layout.add_scatter('A', x_col='x', y_col='y')
layout.add_rug('R', column='value', xLabel='Value')
layout.display()
```

## Compatibilidad

- ✅ `MatrixLayout.set_debug(True)` funciona
- ✅ `ReactiveMatrixLayout.set_debug(True)` funciona
- ✅ Ambos pueden tener debug activado independientemente
- ✅ `ReactiveMatrixLayout` respeta el debug de `MatrixLayout` si el suyo está desactivado
- ✅ No se rompe código existente

## Notas Adicionales

- Los labels (`xLabel`, `yLabel`) ya se pasan correctamente a través de `**kwargs` en todos los métodos `add_*`
- `map_rug` procesa datos correctamente a través de `ChartRegistry.get('rug')` y `chart.get_spec()`
- No se requirieron cambios adicionales en el procesamiento de datos

