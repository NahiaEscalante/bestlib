#!/bin/bash

echo ">>> Installing BESTLIB for Google Colab..."

# Instalar BESTLIB directamente desde Git
# El pyproject.toml ya tiene dependencias compatibles con Colab
pip install --upgrade \
    git+https://github.com/NahiaEscalante/bestlib.git@8-fixing-main

echo ">>> FINISHED. Restart Runtime in Colab if needed."
echo ">>> BESTLIB should now work correctly in Colab."

