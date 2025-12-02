# Investigación de Nuevos Errores en BESTLIB

## Resumen Ejecutivo

Este documento presenta una investigación detallada de los nuevos errores encontrados después de realizar cambios en la librería BESTLIB. Los errores se clasifican en tres categorías principales:

1. **Errores de conversión de tipos** (Timestamp a float)
2. **Errores de estructura de datos** (datos incompletos en specs)
3. **Errores de métodos faltantes** (AttributeError para métodos no implementados)

---

## 1. Errores de Conversión de Tipos

### 1.1. TypeError: "float() argument must be a string or a real number, not 'Timestamp'"

**Gráfico afectado:**
- Line Chart

**Error completo:**
```
TypeError: float() argument must be a string or a real number, not 'Timestamp'
```

**Ubicación del error:**
- `BESTLIB/data/preparators.py:401` en la función `prepare_line_data()`

**Código problemático:**
```python
series[name] = [{'x': float(x), 'y': float(y), 'series': str(name)} 
                for x, y in zip(sdf[x_col], sdf[y_col])]
```

**Análisis:**

El problema ocurre cuando `x_col` contiene objetos `Timestamp` de pandas (por ejemplo, cuando se usa `pd.date_range` o columnas de tipo datetime). La función `float()` no puede convertir directamente un objeto `Timestamp` a float.

**Flujo del error:**

1. Usuario crea DataFrame con columna de fechas (tipo `Timestamp`):
   ```python
   df = pd.DataFrame({
       'date': pd.date_range('2024-01-01', periods=10),
       'value': np.random.randn(10)
   })
   ```

2. Usuario llama `layout.add_line('L', x_col='date', y_col='value')`

3. `add_line()` → `_register_chart()` → `LineChart.get_spec()` → `prepare_line_data()`

4. `prepare_line_data()` intenta convertir `x` (que es un `Timestamp`) a `float()`, causando el error

**Causa raíz:**

La función `prepare_line_data()` asume que los valores en `x_col` y `y_col` son numéricos o pueden convertirse directamente a `float()`. No maneja tipos de datos temporales como `Timestamp`, `datetime`, o `Period`.

**Evidencia:**

- `BESTLIB/data/preparators.py:401`: Intenta `float(x)` sin verificar el tipo
- `BESTLIB/data/preparators.py:405`: Similar problema en la línea sin `series_col`
- `BESTLIB/data/preparators.py:412`: Similar problema para listas de diccionarios

**Supuestos:**

1. **Supuesto 1**: La función fue diseñada originalmente para datos numéricos solamente, y el soporte para fechas nunca fue implementado.

2. **Supuesto 2**: Existe una función de conversión de fechas a números (por ejemplo, usando `timestamp()` o `toordinal()`), pero no se está utilizando.

3. **Supuesto 3**: El problema es similar al que se encontró anteriormente con `Line Plot`, donde se cambió el ejemplo para usar valores numéricos en lugar de fechas, pero el código subyacente nunca se corrigió.

**Solución propuesta:**

Convertir `Timestamp` a número antes de aplicar `float()`:
```python
# Convertir Timestamp a número (timestamp Unix o ordinal)
if isinstance(x, pd.Timestamp):
    x = x.timestamp()  # o x.toordinal() dependiendo del caso
elif hasattr(x, 'timestamp'):
    x = x.timestamp()
```

**Conclusión:**

El problema es que `prepare_line_data()` no maneja tipos temporales. Necesita detectar y convertir `Timestamp` y otros tipos de fecha a números antes de aplicar `float()`.

---

## 2. Errores de Estructura de Datos

### 2.1. RadViz: "Se encontraron 100 puntos pero ninguno tiene _weights válidos o coordenadas válidas"

**Gráfico afectado:**
- RadViz

**Error visual:**
```
Error en RadViz:
Se encontraron 100 puntos pero ninguno tiene _weights válidos o coordenadas válidas
Features: f1, f2, f3
Verifica que los datos tengan _weights con 3 valores normalizados
```

**Ubicación del error:**
- `BESTLIB/matrix.js:2818-2831` en la función `renderRadVizD3()`

**Análisis:**

El renderer JavaScript de RadViz valida que cada punto tenga:
1. `_weights`: Array con la misma longitud que `features`
2. `x` y `y`: Coordenadas válidas (no null, no NaN)

El error indica que los puntos en el spec NO tienen estos campos.

**Flujo del problema:**

1. Usuario llama `layout.add_radviz('R', features=['f1', 'f2', 'f3'])`

2. `add_radviz()` en `BESTLIB/layouts/reactive.py:3224` llama:
   ```python
   self._register_chart(letter, 'radviz', self._data, features=features, class_col=class_col, **kwargs)
   ```

3. `_register_chart()` → `ChartRegistry.get('radviz')` → `RadvizChart.get_spec()`

4. `RadvizChart.get_spec()` (`BESTLIB/charts/radviz.py:44-58`):
   - Llama `prepare_data()` que retorna `records` (lista de diccionarios simples)
   - Crea spec: `{'type': 'radviz', 'data': records, 'features': features, ...}`
   - **NO calcula** `_weights` ni coordenadas `x`, `y`

5. El spec llega a JavaScript con puntos que son solo records (diccionarios con valores de features), pero sin `_weights` ni coordenadas calculadas

**Comparación con implementación legacy:**

`MatrixLayout.map_radviz()` (`BESTLIB/matrix.py:1580-1683`):
- **SÍ calcula** `_weights` normalizados (línea 1633-1636)
- **SÍ calcula** coordenadas `x`, `y` (línea 1643-1644)
- **SÍ agrega** `_weights` al punto (línea 1664)
- Crea spec: `{'type': 'radviz', 'data': points, 'features': feats, ...}` donde `points` tiene `x`, `y`, `_weights`

**Causa raíz:**

Hay **dos implementaciones diferentes** de RadViz:

1. **Implementación nueva** (`RadvizChart` en `BESTLIB/charts/radviz.py`):
   - Usa `prepare_data()` que solo retorna records simples
   - NO calcula `_weights` ni coordenadas
   - Genera spec con datos incompletos

2. **Implementación legacy** (`MatrixLayout.map_radviz()` en `BESTLIB/matrix.py`):
   - Calcula `_weights` normalizados
   - Calcula coordenadas `x`, `y` usando proyección ponderada
   - Genera spec con datos completos

Cuando se usa `_register_chart()` (que usa `ChartRegistry`), se obtiene la implementación nueva que genera datos incompletos.

**Evidencia:**

- `BESTLIB/charts/radviz.py:26-42`: `prepare_data()` solo retorna records, no calcula `_weights` ni coordenadas
- `BESTLIB/matrix.py:1629-1666`: `map_radviz()` calcula `_weights` y coordenadas
- `BESTLIB/layouts/reactive.py:3224`: Usa `_register_chart()` que llama a `RadvizChart`, no a `map_radviz()`

**Supuestos:**

1. **Supuesto 1**: `RadvizChart` fue creado como una clase nueva pero nunca se implementó la lógica de cálculo de `_weights` y coordenadas, asumiendo que se haría en el renderer JavaScript.

2. **Supuesto 2**: El renderer JavaScript espera que los datos vengan pre-procesados desde Python (con `_weights` y coordenadas), no que calcule todo desde cero.

3. **Supuesto 3**: Hay una inconsistencia en el diseño: algunos gráficos procesan datos en Python (como `map_radviz()`), mientras que otros esperan que JavaScript haga el procesamiento.

**Conclusión:**

El problema es que `RadvizChart.get_spec()` no calcula `_weights` ni coordenadas, pero el renderer JavaScript los requiere. La implementación en `RadvizChart` está incompleta comparada con `MatrixLayout.map_radviz()`.

---

### 2.2. Star Coordinates: "No hay puntos válidos para Star Coordinates"

**Gráfico afectado:**
- Star Coordinates

**Error visual:**
```
Error: No hay puntos válidos para Star Coordinates
Los puntos deben tener _weights con 3 valores normalizados y coordenadas válidas
```

**Ubicación del error:**
- `BESTLIB/matrix.js:3346-3359` en la función `renderStarCoordinatesD3()`

**Análisis:**

Similar al problema de RadViz, pero con Star Coordinates.

**Flujo del problema:**

1. Usuario llama `layout.add_star_coordinates('S', features=['f1', 'f2', 'f3'])`

2. `add_star_coordinates()` en `BESTLIB/layouts/reactive.py:3267` llama:
   ```python
   self._register_chart(letter, 'star_coordinates', self._data, features=features, class_col=class_col, **kwargs)
   ```

3. `_register_chart()` → `ChartRegistry.get('star_coordinates')` → `StarCoordinatesChart.get_spec()`

4. `StarCoordinatesChart.get_spec()` (`BESTLIB/charts/star_coordinates.py:44-58`):
   - Llama `prepare_data()` que retorna `records` (lista de diccionarios simples)
   - Crea spec: `{'type': 'star_coordinates', 'data': records, 'features': features, ...}`
   - **NO calcula** `_weights` ni coordenadas `x`, `y`

**Comparación con implementación legacy:**

`MatrixLayout.map_star_coordinates()` (`BESTLIB/matrix.py:1686-1814`):
- **SÍ calcula** `_weights` normalizados y los reordena alfabéticamente (línea 1745-1752)
- **SÍ calcula** coordenadas `x`, `y` usando proyección ponderada (línea 1761-1762)
- **SÍ normaliza** coordenadas a círculo unitario (línea 1766-1770)
- **SÍ agrega** `_weights` al punto (línea 1793)

**Causa raíz:**

Mismo problema que RadViz: `StarCoordinatesChart.get_spec()` no calcula `_weights` ni coordenadas, pero el renderer JavaScript los requiere.

**Evidencia:**

- `BESTLIB/charts/star_coordinates.py:26-42`: `prepare_data()` solo retorna records, no calcula `_weights` ni coordenadas
- `BESTLIB/matrix.py:1741-1795`: `map_star_coordinates()` calcula `_weights` y coordenadas con normalización adicional

**Conclusión:**

El problema es idéntico al de RadViz: `StarCoordinatesChart.get_spec()` está incompleto comparado con `MatrixLayout.map_star_coordinates()`.

---

## 3. Errores de Métodos Faltantes

### 3.1. AttributeError: "'ReactiveMatrixLayout' object has no attribute 'add_ridgeline'"

**Gráficos afectados:**
- Ridgeline Plot (Joy Plot)
- Ribbon Plot
- Histogram 2D
- Polar Plot
- Funnel Plot

**Error completo:**
```
AttributeError: 'ReactiveMatrixLayout' object has no attribute 'add_ridgeline'
```

**Análisis:**

Los métodos `add_ridgeline()`, `add_ribbon()`, `add_hist2d()`, `add_polar()`, y `add_funnel()` existen en `BESTLIB/reactive.py` pero NO en `BESTLIB/layouts/reactive.py`.

**Evidencia:**

1. **Métodos existen en `BESTLIB/reactive.py`:**
   - `add_ridgeline()` (línea 3758)
   - `add_ribbon()` (línea 3783)
   - `add_hist2d()` (línea 3808)
   - `add_polar()` (línea 3833)
   - `add_funnel()` (línea 3858)

2. **Métodos NO existen en `BESTLIB/layouts/reactive.py`:**
   - Búsqueda no encontró estos métodos en `BESTLIB/layouts/reactive.py`

3. **Importación de ReactiveMatrixLayout:**
   - `BESTLIB/__init__.py:79`: Importa desde `BESTLIB.layouts.reactive`
   - `BESTLIB/layouts/__init__.py:5`: Importa desde `.reactive`
   - `BESTLIB/reactive/__init__.py:23-49`: Importa desde `BESTLIB.layouts.reactive`

**Causa raíz:**

Hay **dos implementaciones de `ReactiveMatrixLayout`**:

1. **`BESTLIB/reactive.py`** (legacy):
   - Contiene métodos como `add_ridgeline()`, `add_ribbon()`, `add_hist2d()`, `add_polar()`, `add_funnel()`
   - También contiene `add_kde()`, `add_distplot()`, etc.

2. **`BESTLIB/layouts/reactive.py`** (nuevo):
   - NO contiene estos métodos
   - Solo contiene métodos básicos y algunos avanzados

Cuando se importa `ReactiveMatrixLayout` desde `BESTLIB.layouts.reactive` (que es lo que hace `BESTLIB/__init__.py`), se obtiene la implementación nueva que NO tiene estos métodos.

**Flujo del problema:**

1. Usuario importa: `from BESTLIB.reactive import ReactiveMatrixLayout`
   - O simplemente: `from BESTLIB import ReactiveMatrixLayout`

2. `BESTLIB/__init__.py` importa desde `BESTLIB.layouts.reactive`

3. Se obtiene instancia de `ReactiveMatrixLayout` desde `BESTLIB/layouts/reactive.py`

4. Usuario intenta llamar `layout.add_ridgeline(...)`

5. El método no existe en `BESTLIB/layouts/reactive.py`, causando `AttributeError`

**Supuestos:**

1. **Supuesto 1**: Los métodos fueron implementados en `BESTLIB/reactive.py` pero nunca se migraron a `BESTLIB/layouts/reactive.py` durante la refactorización.

2. **Supuesto 2**: `BESTLIB/layouts/reactive.py` es una versión "limpia" o "modular" que no incluye todos los métodos de la versión legacy.

3. **Supuesto 3**: La intención era mantener `BESTLIB/reactive.py` como implementación legacy y `BESTLIB/layouts/reactive.py` como nueva, pero los imports están apuntando a la nueva que está incompleta.

**Evidencia adicional:**

- `BESTLIB/reactive.py:3758-3881`: Todos los métodos existen y están implementados
- `BESTLIB/layouts/reactive.py`: No contiene estos métodos (verificado con búsqueda)

**Conclusión:**

El problema es que hay dos implementaciones de `ReactiveMatrixLayout`, y los imports están usando la versión nueva (`BESTLIB/layouts/reactive.py`) que no tiene todos los métodos de la versión legacy (`BESTLIB/reactive.py`).

---

## 4. Resumen de Problemas por Categoría

### 4.1. Problemas de Conversión de Tipos

**Gráficos afectados:**
- Line Chart (Timestamp no se puede convertir a float)

**Solución propuesta:**
- Detectar tipos temporales (`Timestamp`, `datetime`) y convertirlos a números antes de aplicar `float()`

### 4.2. Problemas de Estructura de Datos

**Gráficos afectados:**
- RadViz (no calcula `_weights` ni coordenadas)
- Star Coordinates (no calcula `_weights` ni coordenadas)

**Solución propuesta:**
- Implementar cálculo de `_weights` y coordenadas en `RadvizChart.get_spec()` y `StarCoordinatesChart.get_spec()`
- O cambiar `add_radviz()` y `add_star_coordinates()` para usar `MatrixLayout.map_radviz()` y `MatrixLayout.map_star_coordinates()` directamente en lugar de `_register_chart()`

### 4.3. Problemas de Métodos Faltantes

**Gráficos afectados:**
- Ridgeline Plot
- Ribbon Plot
- Histogram 2D
- Polar Plot
- Funnel Plot

**Solución propuesta:**
- Migrar métodos de `BESTLIB/reactive.py` a `BESTLIB/layouts/reactive.py`
- O cambiar los imports para usar `BESTLIB/reactive.py` en lugar de `BESTLIB/layouts/reactive.py`
- O crear un sistema de herencia/composición donde `BESTLIB/layouts/reactive.py` herede o delegue a `BESTLIB/reactive.py`

---

## 5. Patrones Identificados

### 5.1. Inconsistencia entre ChartRegistry y MatrixLayout.map_*

**Patrón:**
- Algunos gráficos tienen implementaciones en `ChartRegistry` (nuevas clases como `RadvizChart`, `StarCoordinatesChart`)
- Estas implementaciones están incompletas comparadas con `MatrixLayout.map_*()` (legacy)
- Cuando se usa `_register_chart()`, se obtiene la implementación nueva e incompleta
- Cuando se usa `MatrixLayout.map_*()` directamente, se obtiene la implementación legacy completa

**Gráficos afectados:**
- RadViz
- Star Coordinates
- Posiblemente otros

**Recomendación:**
- Completar las implementaciones en `ChartRegistry` para que calculen todos los datos necesarios
- O usar `MatrixLayout.map_*()` directamente en lugar de `_register_chart()` para estos gráficos específicos

### 5.2. Duplicación de Implementaciones

**Patrón:**
- Hay dos archivos con `ReactiveMatrixLayout`:
  - `BESTLIB/reactive.py` (legacy, completo)
  - `BESTLIB/layouts/reactive.py` (nuevo, incompleto)
- Los imports están usando la versión nueva que está incompleta
- Algunos métodos existen solo en la versión legacy

**Gráficos afectados:**
- Ridgeline Plot
- Ribbon Plot
- Histogram 2D
- Polar Plot
- Funnel Plot
- KDE (mencionado en investigación anterior)

**Recomendación:**
- Unificar las implementaciones
- Migrar todos los métodos de `BESTLIB/reactive.py` a `BESTLIB/layouts/reactive.py`
- O cambiar los imports para usar la versión legacy hasta que la nueva esté completa

### 5.3. Falta de Manejo de Tipos Temporales

**Patrón:**
- Las funciones de preparación de datos asumen tipos numéricos
- No manejan tipos temporales (`Timestamp`, `datetime`, `Period`)
- Causan errores cuando se intenta convertir estos tipos a `float()`

**Gráficos afectados:**
- Line Chart
- Posiblemente Line Plot (ya corregido en ejemplo pero no en código)

**Recomendación:**
- Agregar detección y conversión de tipos temporales en todas las funciones de preparación de datos
- Crear función auxiliar para convertir fechas a números

---

## 6. Recomendaciones Prioritarias

### Prioridad Alta

1. **Corregir RadViz y Star Coordinates:**
   - Implementar cálculo de `_weights` y coordenadas en `RadvizChart.get_spec()` y `StarCoordinatesChart.get_spec()`
   - O cambiar `add_radviz()` y `add_star_coordinates()` para usar `MatrixLayout.map_*()` directamente

2. **Agregar métodos faltantes:**
   - Migrar `add_ridgeline()`, `add_ribbon()`, `add_hist2d()`, `add_polar()`, `add_funnel()` a `BESTLIB/layouts/reactive.py`
   - O unificar las implementaciones de `ReactiveMatrixLayout`

3. **Corregir manejo de Timestamp:**
   - Agregar conversión de tipos temporales en `prepare_line_data()`
   - Extender a otras funciones de preparación de datos si es necesario

### Prioridad Media

4. **Estandarizar uso de ChartRegistry vs MatrixLayout.map_*:**
   - Decidir cuándo usar cada uno
   - Asegurar que todas las implementaciones en `ChartRegistry` estén completas

5. **Documentar diferencias entre implementaciones:**
   - Documentar qué métodos están en cada implementación de `ReactiveMatrixLayout`
   - Crear guía de migración si es necesario

### Prioridad Baja

6. **Crear tests para tipos temporales:**
   - Agregar tests que usen `Timestamp` y otros tipos temporales
   - Asegurar que todos los gráficos que aceptan fechas funcionen correctamente

---

## 7. Notas Finales

Esta investigación se realizó **sin modificar ningún código**, solo analizando el código existente. Todos los supuestos y conclusiones están basados en evidencia del código fuente.

Los errores identificados son principalmente causados por:

1. **Inconsistencias entre implementaciones nuevas y legacy**
2. **Falta de migración completa de métodos durante refactorización**
3. **Falta de manejo de tipos de datos no numéricos**

Para resolver estos problemas, se recomienda:

1. Primero, completar las implementaciones en `ChartRegistry` o cambiar para usar `MatrixLayout.map_*()` directamente
2. Segundo, migrar todos los métodos faltantes a `BESTLIB/layouts/reactive.py` o unificar las implementaciones
3. Tercero, agregar manejo de tipos temporales en las funciones de preparación de datos

