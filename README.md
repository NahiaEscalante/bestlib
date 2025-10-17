# BESTLIB

Librería para crear visualizaciones interactivas con D3.js en Jupyter notebooks y Google Colab.

## Instalación

```bash
pip install git+https://github.com/NahiaEscalante/bestlib.git@pruebas
```

## Uso Básico

```python
from BESTLIB.matrix import MatrixLayout

# Crear visualización
MatrixLayout.map({
    'C': {
        "type": "circle",
        "cx": 50,
        "cy": 50,
        "r": 40,
        "fill": "#e74c3c"
    }
})

MatrixLayout("C").display()
```

## Características

- ✅ Visualizaciones con D3.js
- ✅ Gráficos de barras y dispersión
- ✅ Interactividad con callbacks Python
- ✅ Compatible con Google Colab y Jupyter

## Documentación

Ver [docs/README.md](docs/README.md) para más información.
