# 🔧 Solución: ModuleNotFoundError: No module named 'BESTLIB.charts'

## ❌ Problema Identificado

Al intentar importar módulos de `BESTLIB.charts`, se obtiene el error:

```
ModuleNotFoundError: No module named 'BESTLIB.charts'
```

### Causa Raíz

El problema está en el archivo `setup.py` (y `pyproject.toml`). La configuración original era:

```python
packages=["BESTLIB"],  # ❌ Solo incluye el paquete principal
```

Esto significa que cuando instalas el paquete con `pip install`, **solo se instala el paquete principal `BESTLIB`**, pero **NO se instalan los subpaquetes** como:
- `BESTLIB.charts`
- `BESTLIB.core`
- `BESTLIB.data`
- `BESTLIB.layouts`
- `BESTLIB.reactive`
- `BESTLIB.render`
- `BESTLIB.utils`
- `BESTLIB.compat`

Por lo tanto, Python no puede encontrar estos módulos cuando intentas importarlos.

---

## ✅ Solución Implementada

### Cambios Realizados

#### 1. **`setup.py`**

**Antes:**
```python
packages=["BESTLIB"],  # ❌ Solo paquete principal
```

**Después:**
```python
packages=find_packages(),  # ✅ Incluye todos los subpaquetes automáticamente
```

#### 2. **`pyproject.toml`**

**Antes:**
```toml
[tool.setuptools]
packages = ["BESTLIB"]  # ❌ Solo paquete principal
```

**Después:**
```toml
[tool.setuptools]
packages = {find = {}}  # ✅ Encuentra todos los subpaquetes automáticamente
```

### ¿Qué hace `find_packages()`?

`find_packages()` automáticamente:
1. Busca todos los directorios que contienen `__init__.py`
2. Los incluye como paquetes Python válidos
3. Incluye subpaquetes recursivamente

Esto asegura que todos los módulos se instalen correctamente:
- ✅ `BESTLIB`
- ✅ `BESTLIB.charts`
- ✅ `BESTLIB.charts.scatter`
- ✅ `BESTLIB.core`
- ✅ `BESTLIB.data`
- ✅ etc.

---

## 🔄 Pasos para Aplicar la Solución

### Opción 1: Reinstalar el Paquete (Recomendado)

Si instalaste el paquete desde GitHub o localmente, necesitas **reinstalarlo** para que los cambios surtan efecto:

```bash
# Desinstalar versión anterior
pip uninstall bestlib -y

# Reinstalar con los cambios
pip install -e .  # Si estás en el directorio del proyecto
# O
pip install --upgrade --force-reinstall git+https://github.com/NahiaEscalante/bestlib.git@widget_mod
```

### Opción 2: Instalación en Google Colab

```python
# Desinstalar versión anterior
!pip uninstall bestlib -y

# Reinstalar (sin dependencias para Colab)
!pip install --upgrade --no-deps git+https://github.com/NahiaEscalante/bestlib.git@widget_mod
```

### Opción 3: Instalación Local desde Código Fuente

Si tienes el código fuente localmente:

```bash
cd /ruta/al/proyecto/bestlib
pip uninstall bestlib -y
pip install -e .
```

---

## ✅ Verificación

Después de reinstalar, verifica que los imports funcionen:

```python
# Esto debería funcionar ahora
from BESTLIB.charts import ChartRegistry
from BESTLIB.charts.kde import KdeChart
from BESTLIB.matrix import MatrixLayout
from BESTLIB.layouts.reactive import ReactiveMatrixLayout

# Verificar que ChartRegistry funciona
print(f"✅ ChartRegistry: {ChartRegistry is not None}")
print(f"📊 Tipos disponibles: {ChartRegistry.list_types()}")
```

Si todo está correcto, deberías ver:
```
✅ ChartRegistry: True
📊 Tipos disponibles: ['scatter', 'bar', 'histogram', ...]
```

---

## 🔍 Diagnóstico Adicional

Si después de reinstalar sigues teniendo problemas, verifica:

### 1. Verificar Estructura del Paquete Instalado

```python
import BESTLIB
import os

# Ver dónde está instalado BESTLIB
print(f"📍 Ubicación: {BESTLIB.__file__}")

# Verificar que existe el directorio charts
charts_path = os.path.join(os.path.dirname(BESTLIB.__file__), 'charts')
print(f"📁 Existe charts/: {os.path.exists(charts_path)}")
print(f"📄 Existe charts/__init__.py: {os.path.exists(os.path.join(charts_path, '__init__.py'))}")
```

### 2. Verificar Instalación con pip

```bash
# Ver qué archivos se instalaron
pip show -f bestlib | grep -E "\.py$|Location"
```

Deberías ver archivos como:
- `BESTLIB/charts/__init__.py`
- `BESTLIB/charts/registry.py`
- `BESTLIB/core/__init__.py`
- etc.

### 3. Verificar PYTHONPATH

```python
import sys
print("📂 Rutas en PYTHONPATH:")
for path in sys.path:
    print(f"   - {path}")
```

Asegúrate de que la ruta donde está instalado `bestlib` esté en `sys.path`.

---

## 📝 Notas Importantes

1. **Siempre reinstala después de cambios en `setup.py`**: Los cambios en `setup.py` solo surten efecto después de reinstalar el paquete.

2. **En modo desarrollo (`pip install -e .`)**: Si instalas en modo desarrollo, los cambios se reflejan automáticamente, pero aún necesitas reinstalar si cambias `setup.py`.

3. **Caché de Python**: Si tienes problemas persistentes, puede ser caché de Python. Prueba:
   ```python
   import importlib
   import sys
   # Limpiar caché de BESTLIB
   if 'BESTLIB' in sys.modules:
       del sys.modules['BESTLIB']
   if 'BESTLIB.charts' in sys.modules:
       del sys.modules['BESTLIB.charts']
   ```

4. **Reiniciar Kernel**: En Jupyter/Colab, siempre reinicia el kernel después de reinstalar un paquete.

---

## 🎯 Resumen

**Problema**: `setup.py` solo incluía el paquete principal, no los subpaquetes.

**Solución**: Usar `find_packages()` para incluir automáticamente todos los subpaquetes.

**Acción requerida**: Reinstalar el paquete después de los cambios.

---

**Fecha de corrección**: 2024
**Archivos modificados**: 
- `setup.py`
- `pyproject.toml`

