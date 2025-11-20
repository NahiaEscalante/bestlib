# 📦 Instalación de BESTLIB en Google Colab

## ❌ Error Común

Si ves este error:
```
ModuleNotFoundError: No module named 'BESTLIB.layouts'
```

Significa que BESTLIB no está instalado o no está en el path de Python.

---

## ✅ Solución: Instalación en Colab

### Opción 1: Instalar desde Git (Recomendado)

```python
# 1. Clonar el repositorio
!git clone https://github.com/tu-usuario/bestlib.git
# O si es un repositorio privado, usa tu URL

# 2. Instalar BESTLIB
%cd bestlib
!pip install -e .

# 3. Verificar instalación
from BESTLIB.layouts import MatrixLayout
print("✅ BESTLIB instalado correctamente")
```

### Opción 2: Instalar desde directorio local (si subiste los archivos)

```python
# 1. Subir BESTLIB a Colab (usando el panel de archivos o drive)

# 2. Agregar al path
import sys
sys.path.insert(0, '/content/BESTLIB')  # Ajusta la ruta según donde esté

# 3. Verificar
from BESTLIB.layouts import MatrixLayout
print("✅ BESTLIB importado correctamente")
```

### Opción 3: Instalar desde Google Drive

```python
# 1. Montar Google Drive
from google.colab import drive
drive.mount('/content/drive')

# 2. Agregar al path
import sys
sys.path.insert(0, '/content/drive/MyDrive/ruta/a/bestlib')

# 3. Verificar
from BESTLIB.layouts import MatrixLayout
print("✅ BESTLIB importado correctamente")
```

---

## 🔧 Verificación de Instalación

Ejecuta este código para verificar que todo funciona:

```python
# Verificar que BESTLIB está instalado
try:
    from BESTLIB.layouts import MatrixLayout
    print("✅ BESTLIB.layouts importado correctamente")
    
    # Verificar que MatrixLayout tiene los métodos nuevos
    methods = [m for m in dir(MatrixLayout) if m.startswith('map_')]
    print(f"✅ Métodos disponibles: {len(methods)}")
    print(f"   Métodos: {', '.join(sorted(methods)[:10])}...")
    
    # Crear una instancia de prueba
    layout = MatrixLayout("L")
    print("✅ MatrixLayout creado correctamente")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("\n📋 Soluciones:")
    print("1. Asegúrate de haber ejecutado: !pip install -e .")
    print("2. Verifica que estás en el directorio correcto")
    print("3. Reinicia el runtime: Runtime → Restart runtime")
```

---

## 🐛 Solución de Problemas

### Problema 1: "No module named 'BESTLIB'"

**Solución:**
```python
# Verificar que BESTLIB está en el path
import sys
print("Paths de Python:")
for p in sys.path:
    print(f"  - {p}")

# Si BESTLIB no está, agregarlo
import os
bestlib_path = "/content/bestlib"  # Ajusta según tu caso
if os.path.exists(bestlib_path):
    sys.path.insert(0, bestlib_path)
    print(f"✅ BESTLIB agregado al path: {bestlib_path}")
else:
    print(f"❌ BESTLIB no encontrado en: {bestlib_path}")
```

### Problema 2: "No module named 'BESTLIB.layouts'"

**Solución:**
```python
# Verificar estructura de directorios
import os
bestlib_path = "/content/bestlib/BESTLIB"  # Ajusta según tu caso
if os.path.exists(bestlib_path):
    print("✅ Directorio BESTLIB encontrado")
    print("Contenido:")
    for item in os.listdir(bestlib_path):
        print(f"  - {item}")
    
    # Verificar que layouts existe
    layouts_path = os.path.join(bestlib_path, "layouts")
    if os.path.exists(layouts_path):
        print("✅ Directorio layouts encontrado")
        print("Contenido:")
        for item in os.listdir(layouts_path):
            print(f"  - {item}")
    else:
        print("❌ Directorio layouts NO encontrado")
else:
    print("❌ Directorio BESTLIB NO encontrado")
```

### Problema 3: "AttributeError: 'MatrixLayout' object has no attribute 'map_line_plot'"

**Solución:**
```python
# Reiniciar el runtime y reinstalar
# Runtime → Restart runtime

# Luego reinstalar
!pip install -e . --force-reinstall --no-cache-dir

# Verificar que los métodos están disponibles
from BESTLIB.layouts import MatrixLayout
import inspect
methods = [m for m in dir(MatrixLayout) if m.startswith('map_')]
print(f"Métodos map_* disponibles: {methods}")
```

---

## 📝 Ejemplo Completo de Instalación y Uso

```python
# ==========================================
# 1. INSTALACIÓN
# ==========================================
!git clone https://github.com/tu-usuario/bestlib.git
%cd bestlib
!pip install -e .

# ==========================================
# 2. VERIFICACIÓN
# ==========================================
from BESTLIB.layouts import MatrixLayout
import pandas as pd

# Verificar métodos disponibles
methods = [m for m in dir(MatrixLayout) if m.startswith('map_')]
print(f"✅ Métodos disponibles: {len(methods)}")

# ==========================================
# 3. USO
# ==========================================
# Cargar datos
df = pd.read_csv("/mnt/data/iris.csv")

# Crear layout
layout = MatrixLayout("L")

# Agregar gráfico
layout.map_line_plot(
    "L",
    df,
    x_col="sepal_length",
    y_col="sepal_width",
    strokeWidth=2,
    markers=True
)

# Mostrar
layout.display()
```

---

## 🔄 Reinicio del Runtime

Si después de instalar sigues teniendo problemas:

1. **Reinicia el runtime**: `Runtime → Restart runtime`
2. **Reinstala BESTLIB**: Ejecuta `!pip install -e .` de nuevo
3. **Verifica el import**: Ejecuta el código de verificación

---

## 📌 Notas Importantes

1. **Siempre reinicia el runtime** después de instalar BESTLIB
2. **Usa `!pip install -e .`** en lugar de `!pip install .` para desarrollo
3. **Verifica el path** si tienes problemas de importación
4. **Los métodos `map_*`** están disponibles en `MatrixLayout` después de la instalación correcta

---

**Si sigues teniendo problemas, verifica:**
- ✅ Que el repositorio se clonó correctamente
- ✅ Que estás en el directorio correcto (`%cd bestlib`)
- ✅ Que ejecutaste `!pip install -e .`
- ✅ Que reiniciaste el runtime después de instalar

