#!/bin/bash

echo ">>> Resetting Colab environment for BESTLIB compatibility..."

# Paso 1: Fijar versiones críticas que Colab requiere
# Estas versiones son compatibles con google-colab y evitan conflictos
pip install --upgrade --force-reinstall \
    ipython==7.34.0 \
    ipywidgets==7.7.1 \
    pandas==2.2.2 \
    numpy==1.26.4 \
    decorator==4.4.2

# Paso 2: Instalar dependencias básicas de BESTLIB que no causan conflictos
pip install \
    python-dateutil>=2.8.2 \
    pytz>=2020.1 \
    traitlets>=5.0 \
    matplotlib-inline>=0.1.5

echo ">>> Installing BESTLIB (with compatible dependencies)..."

# Paso 3: Instalar BESTLIB desde Git
# Usar --no-build-isolation para evitar que pip resuelva dependencias automáticamente
pip install --no-build-isolation \
    git+https://github.com/NahiaEscalante/bestlib.git@8-fixing-main

echo ">>> FINISHED. Restart Runtime in Colab."
echo ">>> Note: If you see dependency conflicts, they should not affect BESTLIB functionality."

