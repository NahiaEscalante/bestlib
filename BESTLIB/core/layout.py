"""
Layout Engine - Parsing y gestión de layouts ASCII
"""
from typing import Optional
from .exceptions import LayoutError


class Grid:
    """Representación de un grid de layout"""
    
    def __init__(self, rows: int, cols: int):
        """
        Inicializa un grid.
        
        Args:
            rows (int): Número de filas
            cols (int): Número de columnas
        
        Raises:
            ValueError: Si rows o cols no son int > 0
        """
        if not isinstance(rows, int) or rows <= 0:
            raise ValueError(f"rows debe ser int > 0, recibido: {rows!r}")
        if not isinstance(cols, int) or cols <= 0:
            raise ValueError(f"cols debe ser int > 0, recibido: {cols!r}")
        
        self.rows = rows
        self.cols = cols
        self.cells = {}  # {cell_id: {'row': int, 'col': int, 'letter': str}}
    
    def add_cell(self, cell_id: str, row: int, col: int, letter: str) -> None:
        """
        Agrega una celda al grid.
        
        Args:
            cell_id (str): ID de la celda
            row (int): Fila (>= 0)
            col (int): Columna (>= 0)
            letter (str): Letra de la celda (longitud 1)
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if not isinstance(cell_id, str) or not cell_id:
            raise ValueError(f"cell_id must be non-empty str, received: {cell_id!r}")
        if not isinstance(row, int) or row < 0:
            raise ValueError(f"row must be int >= 0, received: {row!r}")
        if not isinstance(col, int) or col < 0:
            raise ValueError(f"col must be int >= 0, received: {col!r}")
        if not isinstance(letter, str) or len(letter) != 1:
            raise ValueError(f"letter must be str of length 1, received: {letter!r}")
        
        self.cells[cell_id] = {
            'row': row,
            'col': col,
            'letter': letter
        }
    
    def get_cell(self, cell_id: str) -> Optional[dict]:
        """
        Obtiene información de una celda
        
        Args:
            cell_id (str): ID de la celda
        
        Returns:
            dict: Información de la celda o None si no existe
        """
        return self.cells.get(cell_id)


class LayoutEngine:
    """
    Motor de parsing y gestión de layouts ASCII.
    Convierte layouts ASCII en estructura de grid.
    """
    
    @staticmethod
    def parse_ascii_layout(ascii_layout: str) -> "Grid":
        """
        Parsea un layout ASCII en estructura de grid.
        
        Args:
            ascii_layout (str): Layout ASCII (ej: "AB\nCD")
        
        Returns:
            Grid: Estructura de grid parseada
        
        Raises:
            LayoutError: Si el layout es inválido o está vacío
        """
        if not ascii_layout:
            raise LayoutError("ascii_layout no puede estar vacío")
        
        # ✅ NUEVO: Validar caracteres problemáticos
        import string
        allowed_chars = string.ascii_letters + string.digits + '\n'
        problematic_chars = [c for c in ascii_layout if c not in allowed_chars and not c.isspace()]
        if problematic_chars:
            raise LayoutError(
                f"ascii_layout contiene caracteres no permitidos: {set(problematic_chars)}. "
                f"Use solo letras, números, espacios y saltos de línea."
            )
        
        rows = [r.strip() for r in ascii_layout.strip().split("\n") if r.strip()]
        if not rows:
            raise LayoutError("ascii_layout no puede estar vacío")
        
        col_len = len(rows[0])
        if not all(len(r) == col_len for r in rows):
            raise LayoutError("Todas las filas del ascii_layout deben tener igual longitud")
        
        grid = Grid(len(rows), col_len)
        
        # Parsear cada celda
        for row_idx, row in enumerate(rows):
            for col_idx, letter in enumerate(row):
                cell_id = f"{row_idx}_{col_idx}"
                grid.add_cell(cell_id, row_idx, col_idx, letter)
        
        return grid
    
    @staticmethod
    def validate_grid(grid: "Grid") -> bool:
        """
        Valida que un grid sea válido.
        
        Args:
            grid (Grid): Grid a validar
        
        Returns:
            bool: True si el grid es válido
        """
        if not isinstance(grid, Grid):
            return False
        if grid.rows <= 0 or grid.cols <= 0:
            return False
        if len(grid.cells) != grid.rows * grid.cols:
            return False
        return True
    
    @staticmethod
    def calculate_dimensions(grid: "Grid", container_size: Optional[dict] = None) -> dict:
        """
        Calcula dimensiones de celdas del grid.
        
        Args:
            grid (Grid): Grid a calcular
            container_size (dict, optional): Tamaño del contenedor
        
        Returns:
            dict: Dimensiones calculadas
        
        Raises:
            TypeError: Si grid no es Grid o container_size no es dict/None
            ValueError: Si container_size no tiene 'width' y 'height' o valores inválidos
        """
        if not isinstance(grid, Grid):
            raise TypeError(f"grid must be Grid, received: {type(grid).__name__}")
        if container_size is not None and not isinstance(container_size, dict):
            raise TypeError(f"container_size must be dict or None, received: {type(container_size).__name__}")
        
        if container_size is not None:
            if 'width' not in container_size or 'height' not in container_size:
                raise ValueError("container_size debe tener 'width' y 'height' si se proporciona")
            width = container_size.get('width')
            height = container_size.get('height')
            
            # ✅ CRIT-006: Validación estricta de tipos numéricos
            import math
            if not isinstance(width, (int, float)):
                raise TypeError(f"container_size['width'] debe ser int o float, recibido: {type(width).__name__}")
            if not isinstance(height, (int, float)):
                raise TypeError(f"container_size['height'] debe ser int o float, recibido: {type(height).__name__}")
            if math.isnan(width) or math.isinf(width) or width <= 0:
                raise ValueError(
                    f"container_size['width'] debe ser número positivo finito, recibido: {width!r}"
                )
            if math.isnan(height) or math.isinf(height) or height <= 0:
                raise ValueError(
                    f"container_size['height'] debe ser número positivo finito, recibido: {height!r}"
                )
        
        # Por ahora retorna estructura básica
        # En el futuro se implementará lógica de cálculo de dimensiones
        return {
            'rows': grid.rows,
            'cols': grid.cols,
            'cell_width': container_size.get('width', 400) / grid.cols if container_size else None,
            'cell_height': container_size.get('height', 300) / grid.rows if container_size else None
        }

