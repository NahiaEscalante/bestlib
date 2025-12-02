# Proceso de release

1. **Pruebas locales**
   ```bash
   make install
   make lint
   pytest
   ```
2. **Bundle JS**
   ```bash
   cd js
   npm install
   npm run build
   ```
3. **Build Python**
   ```bash
   make build
   ```
   Se generan `dist/*.whl` y `dist/*.tar.gz`.
4. **Publicar**
   ```bash
   python -m pip install --upgrade twine
   twine upload dist/*
   ```
5. **Tag**
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

