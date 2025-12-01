"""
Utilidades para conversión de figsize
"""


def figsize_to_pixels(figsize):
    """
    Convierte figsize de pulgadas a píxeles (asumiendo 96 DPI).
    
    Args:
        figsize: Tupla (width, height) en pulgadas o píxeles, o None
        
    Returns:
        Tupla (width, height) en píxeles, o None
    """
    if figsize is None:
        return None
    if isinstance(figsize, (tuple, list)) and len(figsize) == 2:
        # Si los valores son > 50, asumimos que ya están en píxeles
        # Si son <= 50, asumimos que están en pulgadas
        width, height = figsize
        if width > 50 and height > 50:
            return (int(width), int(height))
        else:
            # Convertir de pulgadas a píxeles (96 DPI)
            return (int(width * 96), int(height * 96))
    return None


def process_figsize_in_kwargs(kwargs):
    """
    Procesa figsize en kwargs, convirtiéndolo a píxeles si existe.
    
    Args:
        kwargs: Diccionario de argumentos que puede contener 'figsize'
    """
    if 'figsize' in kwargs:
        figsize_px = figsize_to_pixels(kwargs['figsize'])
        if figsize_px:
            kwargs['figsize'] = figsize_px
        else:
            del kwargs['figsize']

