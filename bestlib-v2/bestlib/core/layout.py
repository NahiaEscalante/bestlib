"""
Layout Engine - Parsing y gestión de layouts ASCII
"""
from .exceptions import LayoutError


class Grid:
    """Representación de un grid de layout"""
    
    def __init__(self, rows, cols):
        """
        Inicializa un grid.
        
        Args:
            rows (int): Número de filas
            cols (int): Número de columnas
        """
        self.rows = rows
        self.cols = cols
        self.cells = {}  # {cell_id: {'row': int, 'col': int, 'letter': str}}
    
    def add_cell(self, cell_id, row, col, letter):
        """Agrega una celda al grid"""
        self.cells[cell_id] = {
            'row': row,
            'col': col,
            'letter': letter
        }
    
    def get_cell(self, cell_id):
        """Obtiene información de una celda"""
        return self.cells.get(cell_id)


class LayoutEngine:
    """
    Motor de parsing y gestión de layouts ASCII.
    Convierte layouts ASCII en estructura de grid.
    """
    
    @staticmethod
    def parse_ascii_layout(ascii_layout):
        """
        Parsea un layout ASCII en estructura de grid.
        
        Args:
            ascii_layout (str): Layout ASCII (ej: "AB\nCD")
        
        Returns:
            Grid: Estructura de grid parseada
        
        Raises:
            LayoutError: Si el layout es inválido
        """
        if not ascii_layout:
            raise LayoutError("ascii_layout no puede estar vacío")
        
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
    def validate_grid(grid):
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
    def calculate_dimensions(grid, container_size=None):
        """
        Calcula dimensiones de celdas del grid.
        
        Args:
            grid (Grid): Grid a calcular
            container_size (dict): Tamaño del contenedor (opcional)
        
        Returns:
            dict: Dimensiones calculadas
        """
        # Por ahora retorna estructura básica
        # En el futuro se implementará lógica de cálculo de dimensiones
        return {
            'rows': grid.rows,
            'cols': grid.cols,
            'cell_width': container_size.get('width', 400) / grid.cols if container_size else None,
            'cell_height': container_size.get('height', 300) / grid.rows if container_size else None
        }

