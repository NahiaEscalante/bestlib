#!/bin/bash

echo ">>> Resetting Colab environment for BESTLIB compatibility..."

pip install --upgrade --force-reinstall \
    ipython==7.34.0 \
    ipywidgets==7.7.1 \
    pandas==2.2.2 \
    numpy==2.2.0 \
    decorator==4.4.2

echo ">>> Installing BESTLIB (fixed dependencies)..."

pip install --upgrade --force-reinstall \
    git+https://github.com/NahiaEscalante/bestlib.git@8-fixing-main

echo ">>> FINISHED. Restart Runtime in Colab."

