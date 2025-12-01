# Contribuir a BESTLIB

¡Gracias por tu interés en contribuir a BESTLIB! 🎉

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo puedo contribuir?](#cómo-puedo-contribuir)
- [Desarrollo Local](#desarrollo-local)
- [Estilo de Código](#estilo-de-código)
- [Testing](#testing)
- [Pull Requests](#pull-requests)

## Código de Conducta

Este proyecto se adhiere a un código de conducta. Al participar, se espera que mantengas este código.

## ¿Cómo puedo contribuir?

### 🐛 Reportar Bugs

Los bugs se reportan como [issues de GitHub](https://github.com/NahiaEscalante/bestlib/issues).

**Antes de crear un bug report**, verifica que no exista ya un issue similar.

**Para un buen bug report**, incluye:
- Descripción clara y concisa del problema
- Pasos para reproducir el comportamiento
- Comportamiento esperado vs actual
- Capturas de pantalla si aplica
- Versión de Python y BESTLIB
- Entorno (Jupyter, Colab, etc.)

### ✨ Sugerir Mejoras

Las sugerencias de mejoras también se reportan como issues.

Incluye:
- Descripción clara de la funcionalidad
- Por qué sería útil
- Ejemplos de uso si es posible

### 📝 Tu Primera Contribución de Código

¿No sabes por dónde empezar? Busca issues etiquetados con:
- `good first issue` - Issues simples para empezar
- `help wanted` - Issues que necesitan ayuda

## Desarrollo Local

### Setup

```bash
# Clonar el repositorio
git clone https://github.com/NahiaEscalante/bestlib.git
cd bestlib

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar en modo desarrollo
pip install -e ".[dev,full]"
```

### Estructura del Proyecto

```
bestlib/
├── bestlib/              # Código fuente
│   ├── charts/          # Tipos de gráficos
│   ├── core/            # Núcleo del sistema
│   ├── data/            # Procesamiento de datos
│   ├── reactive/        # Sistema reactivo
│   ├── render/          # Renderizado
│   ├── layouts/         # Layouts
│   ├── utils/           # Utilidades
│   ├── assets/          # JS/CSS
│   └── api/             # API pública
├── tests/               # Tests
├── examples/            # Ejemplos
└── docs/                # Documentación
```

## Estilo de Código

### Python

Usamos [Black](https://black.readthedocs.io/) para formateo:

```bash
black bestlib/ tests/
```

Y [Flake8](https://flake8.pycqa.org/) para linting:

```bash
flake8 bestlib/ tests/
```

### Convenciones

- Nombres de variables/funciones: `snake_case`
- Nombres de clases: `PascalCase`
- Constantes: `UPPER_CASE`
- Líneas: máximo 100 caracteres
- Docstrings: formato Google/NumPy

Ejemplo de docstring:

```python
def mi_funcion(param1, param2):
    """
    Breve descripción de la función.
    
    Args:
        param1 (tipo): Descripción del parámetro 1
        param2 (tipo): Descripción del parámetro 2
        
    Returns:
        tipo: Descripción del valor de retorno
        
    Raises:
        ErrorType: Cuándo se lanza este error
        
    Example:
        >>> mi_funcion(1, 2)
        3
    """
    return param1 + param2
```

## Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_charts.py

# Con cobertura
pytest --cov=bestlib --cov-report=html
```

### Escribir Tests

```python
# tests/test_ejemplo.py
import pytest
from bestlib import MatrixLayout

def test_matrix_layout_creation():
    """Test creación básica de MatrixLayout."""
    layout = MatrixLayout("A | B")
    assert layout is not None
    assert len(layout.cells) == 2

def test_matrix_layout_invalid():
    """Test que se lance error con layout inválido."""
    with pytest.raises(LayoutError):
        MatrixLayout("")
```

### Cobertura

Buscamos mantener >80% de cobertura de código.

## Pull Requests

### Proceso

1. **Fork** el repositorio
2. **Crea una rama** desde `main`:
   ```bash
   git checkout -b feature/mi-nueva-funcionalidad
   ```
3. **Haz tus cambios** siguiendo el estilo de código
4. **Añade tests** para tu código
5. **Ejecuta los tests**:
   ```bash
   pytest
   black bestlib/ tests/
   flake8 bestlib/ tests/
   ```
6. **Commit** con mensajes descriptivos:
   ```bash
   git commit -m "feat: agregar gráfico de burbujas"
   ```
7. **Push** a tu fork:
   ```bash
   git push origin feature/mi-nueva-funcionalidad
   ```
8. **Abre un Pull Request**

### Mensajes de Commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Formateo, punto y coma faltante, etc.
- `refactor:` Refactorización de código
- `test:` Añadir o modificar tests
- `chore:` Mantenimiento (dependencias, etc.)

Ejemplos:
```
feat: agregar gráfico polar interactivo
fix: corregir error en SelectionModel cuando data es None
docs: actualizar README con ejemplos de vistas enlazadas
test: agregar tests para ChartRegistry
```

### Checklist del PR

- [ ] Los tests pasan
- [ ] Código formateado con Black
- [ ] Sin errores de Flake8
- [ ] Tests añadidos/actualizados
- [ ] Documentación actualizada si aplica
- [ ] CHANGELOG.md actualizado
- [ ] Descripción clara del PR

## 📞 Preguntas

Si tienes preguntas, puedes:
- Abrir un issue con la etiqueta `question`
- Contactar a los mantenedores

## 🙏 Agradecimientos

¡Gracias por contribuir a BESTLIB! Cada contribución, por pequeña que sea, es valiosa.

---

**Happy Coding!** 🚀
