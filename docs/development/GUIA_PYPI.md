# 📦 Guía para Subir BESTLIB a PyPI

## ✅ Estado: Proyecto Listo para PyPI

El proyecto ha sido configurado con todos los archivos necesarios para publicar en PyPI.

## 📋 Archivos Configurados

- ✅ `setup.py` - Configuración completa con metadata
- ✅ `pyproject.toml` - Configuración moderna de build
- ✅ `LICENSE` - Licencia MIT
- ✅ `MANIFEST.in` - Inclusión de archivos JS/CSS
- ✅ `.gitignore` - Actualizado con exclusiones de build
- ✅ `README.md` - Documentación completa
- ✅ `CHANGELOG.md` - Historial de cambios
- ✅ Versión sincronizada (0.1.0) en todos los archivos

## 🚀 Pasos para Subir a PyPI

### 1. Instalar Herramientas Necesarias

```bash
pip install --upgrade build twine
```

### 2. Verificar Configuración

Antes de construir, verifica que todo esté correcto:

```bash
# Verificar que setup.py es válido
python setup.py check

# Verificar estructura del paquete
python -c "from setuptools import find_packages; print(find_packages())"
```

### 3. Limpiar Builds Anteriores (Opcional)

```bash
rm -rf build/ dist/ *.egg-info/
```

### 4. Construir el Paquete

```bash
python -m build
```

Esto creará:
- `dist/bestlib-0.1.0.tar.gz` (source distribution)
- `dist/bestlib-0.1.0-py3-none-any.whl` (wheel)

### 5. Verificar los Archivos de Distribución

```bash
twine check dist/*
```

Esto verificará que:
- Los metadatos estén correctos
- Los archivos requeridos estén incluidos
- No haya errores de formato

### 6. Subir a PyPI Test (Recomendado Primero)

**IMPORTANTE:** Prueba primero en TestPyPI para verificar que todo funcione:

```bash
# Subir a TestPyPI
twine upload --repository testpypi dist/*
```

Luego prueba la instalación desde TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ bestlib
```

### 7. Subir a PyPI Real

Una vez verificado en TestPyPI, sube a PyPI real:

```bash
twine upload dist/*
```

Se te pedirá:
- **Username:** `__token__` (literalmente)
- **Password:** Tu API token de PyPI

### 8. Configurar Token de PyPI (Opcional pero Recomendado)

Para evitar ingresar credenciales cada vez, crea `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-tu-token-aqui

[testpypi]
username = __token__
password = pypi-tu-token-de-test-aqui
```

**Cómo obtener un token:**
1. Ve a https://pypi.org/manage/account/token/
2. Crea un nuevo token (API token)
3. Copia el token (solo se muestra una vez)

## ⚠️ Notas Importantes

### Antes de Subir

1. **Actualizar URLs en setup.py y pyproject.toml:**
   - Revisa que las URLs de GitHub sean correctas
   - Si no tienes repositorio público, puedes comentar las URLs

2. **Email del Autor (Opcional):**
   - Si quieres agregar email, edita `setup.py` línea `author_email`

3. **Verificar que los archivos JS/CSS estén incluidos:**
   ```bash
   python -m build
   tar -tzf dist/bestlib-0.1.0.tar.gz | grep -E '\.(js|css)$'
   ```

### Después de Subir

1. **Verificar en PyPI:**
   - Visita https://pypi.org/project/bestlib/
   - Verifica que la descripción, README y metadata estén correctos

2. **Probar Instalación:**
   ```bash
   pip install bestlib
   python -c "from BESTLIB import MatrixLayout; print('OK')"
   ```

## 🔄 Actualizar Versión

Para futuras versiones:

1. Actualiza la versión en:
   - `setup.py` (línea `version`)
   - `pyproject.toml` (línea `version`)
   - `BESTLIB/__init__.py` (línea `__version__`)

2. Actualiza `CHANGELOG.md`

3. Repite los pasos 4-7

## 📝 Checklist Final

Antes de ejecutar `twine upload`:

- [ ] Versión actualizada en todos los archivos
- [ ] README.md actualizado y sin errores
- [ ] LICENSE presente
- [ ] MANIFEST.in incluye todos los archivos necesarios
- [ ] `twine check dist/*` pasa sin errores
- [ ] Probado en TestPyPI (recomendado)
- [ ] Token de PyPI configurado

## 🐛 Solución de Problemas

### Error: "File already exists"
- La versión ya existe en PyPI
- Incrementa la versión (ej: 0.1.0 → 0.1.1)

### Error: "Invalid distribution"
- Verifica que `MANIFEST.in` incluya todos los archivos necesarios
- Ejecuta `python -m build --clean` y vuelve a construir

### Error: "Missing required files"
- Verifica que `LICENSE` y `README.md` estén en la raíz
- Verifica que `MANIFEST.in` incluya estos archivos

### Archivos JS/CSS no incluidos
- Verifica que `package_data` en `setup.py` esté correcto
- Verifica que `MANIFEST.in` tenga `recursive-include BESTLIB *.js *.css`

## 📚 Recursos

- [PyPI Packaging Guide](https://packaging.python.org/en/latest/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Setuptools Documentation](https://setuptools.readthedocs.io/)

---

**¡Buena suerte con el lanzamiento! 🚀**

