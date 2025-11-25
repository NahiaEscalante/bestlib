"""
Utilidades para conversión de figsize
"""
from typing import Any, Dict, Optional, Tuple


def figsize_to_pixels(figsize: Optional[Tuple[float, float]]) -> Optional[Tuple[int, int]]:
    """
    Convierte figsize de pulgadas a píxeles (asumiendo 96 DPI).
    
    Args:
        figsize: Tupla (width, height) en pulgadas o píxeles, o None
        
    Returns:
        Tupla (width, height) en píxeles, o None
    
    Raises:
        TypeError: Si figsize no es None, tuple o list, o si los valores no son numéricos.
    """
    if figsize is None:
        return None
    if not isinstance(figsize, (tuple, list)) or len(figsize) != 2:
        raise TypeError(f"figsize must be tuple/list of 2 numbers, received: {type(figsize).__name__}")
    width, height = figsize
    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
        raise TypeError(f"figsize values must be numeric, received: width={type(width).__name__}, height={type(height).__name__}")
    # Si los valores son > 50, asumimos que ya están en píxeles
    # Si son <= 50, asumimos que están en pulgadas
    if width > 50 and height > 50:
        return (int(width), int(height))
    else:
        # Convertir de pulgadas a píxeles (96 DPI)
        return (int(width * 96), int(height * 96))


def process_figsize_in_kwargs(kwargs: Dict[str, Any]) -> None:
    """
    Procesa figsize en kwargs, convirtiéndolo a píxeles si existe.
    
    Args:
        kwargs: Diccionario de argumentos que puede contener 'figsize'
    
    Raises:
        TypeError: Si kwargs no es dict.
    """
    if not isinstance(kwargs, dict):
        raise TypeError(f"kwargs must be dict, received: {type(kwargs).__name__}")
    if 'figsize' in kwargs:
        figsize_px = figsize_to_pixels(kwargs['figsize'])
        if figsize_px:
            kwargs['figsize'] = figsize_px
        else:
            del kwargs['figsize']

