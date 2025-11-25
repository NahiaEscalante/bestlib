#!/usr/bin/env python3
"""
Script para normalizar todos los archivos que usan HAS_PANDAS.
Reemplaza HAS_PANDAS por has_pandas() y get_pandas().
"""
import re
import os
from pathlib import Path

# Patrón para encontrar y reemplazar HAS_PANDAS
PATTERNS = [
    # Reemplazar bloque completo de importación
    (
        r'# Import de pandas.*?\n(?:import sys.*?\n)?HAS_PANDAS = False\n(?:HAS_NUMPY = False\n)?(?:pd = None\n)?(?:np = None\n)?try:.*?except.*?HAS_PANDAS = False\n(?:pd = None\n)?(?:np = None\n)?',
        '# ✅ MED-003: Eliminado HAS_PANDAS - usar has_pandas() y get_pandas() siempre\nfrom ...utils.imports import has_pandas, get_pandas\n'
    ),
    # Reemplazar HAS_PANDAS and isinstance(data, pd.DataFrame)
    (
        r'if HAS_PANDAS and isinstance\(data, pd\.DataFrame\):',
        'if has_pandas():\n            pd = get_pandas()\n            if pd is not None and isinstance(data, pd.DataFrame):'
    ),
    # Reemplazar if not HAS_PANDAS
    (
        r'if not HAS_PANDAS',
        'if not has_pandas()'
    ),
    # Reemplazar if HAS_PANDAS
    (
        r'if HAS_PANDAS',
        'if has_pandas()'
    ),
]

def normalize_file(filepath):
    """Normaliza un archivo reemplazando HAS_PANDAS."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Aplicar reemplazos
        for pattern, replacement in PATTERNS:
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Normalizado: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error en {filepath}: {e}")
        return False

if __name__ == '__main__':
    # Buscar todos los archivos Python en BESTLIB/charts
    charts_dir = Path('BESTLIB/charts')
    files = list(charts_dir.glob('*.py'))
    
    normalized = 0
    for filepath in files:
        if normalize_file(filepath):
            normalized += 1
    
    print(f"\n✅ Normalizados {normalized} archivos")

