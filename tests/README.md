# Tests de BESTLIB

Suite de tests unitarios y de compatibilidad para BESTLIB.

---

## Ejecutar Tests

### Ejecutar todos los tests

```bash
pytest
```

### Ejecutar tests específicos

```bash
# Solo tests de imports
pytest tests/test_imports.py

# Solo tests de MatrixLayout
pytest tests/test_matrixlayout.py

# Solo tests de charts
pytest tests/test_charts.py

# Solo tests de compatibilidad legacy
pytest tests/test_legacy_compatibility.py
```

### Ejecutar con más detalle

```bash
# Verbose mode
pytest -v

# Mostrar print statements
pytest -s

# Detener en primer fallo
pytest -x

# Mostrar coverage
pytest --cov=BESTLIB --cov-report=html
```

---

## Estructura de Tests

### test_imports.py
- Tests de importación de API pública
- Verificación de que todos los componentes se importan correctamente
- Tests de imports legacy con warnings

### test_matrixlayout.py
- Tests de creación de MatrixLayout
- Tests de mapeo de gráficos (map_scatter, map_barchart, etc.)
- Tests del sistema de eventos
- Tests de ReactiveMatrixLayout

### test_charts.py
- Tests de ChartRegistry
- Tests de gráficos individuales (ScatterChart, BarChart, etc.)
- Tests de preparación y validación de datos

### test_legacy_compatibility.py
- Tests de compatibilidad hacia atrás
- Verificación de que código legacy funciona con warnings
- Tests de equivalencia entre API legacy y moderna

---

## Fixtures Disponibles

Definidos en `conftest.py`:

- `sample_dataframe` - DataFrame simple para tests
- `iris_dataframe` - DataFrame Iris (si existe el archivo)
- `sample_dicts` - Lista de diccionarios para tests

---

## Requisitos

### Obligatorios

```bash
pip install pytest
```

### Opcionales (para coverage)

```bash
pip install pytest-cov
```

### Para tests completos

```bash
pip install pandas numpy
```

---

## Markers

### Markers disponibles:

- `@pytest.mark.slow` - Tests lentos
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.jupyter` - Tests que requieren Jupyter
- `@pytest.mark.pandas` - Tests que requieren pandas

### Uso:

```python
@pytest.mark.pandas
def test_with_dataframe(sample_dataframe):
    # Este test solo se ejecuta si pandas está instalado
    pass
```

---

## Añadir Nuevos Tests

### 1. Crear archivo test_*.py en tests/

```python
"""
Descripción del módulo de tests
"""
import pytest


class TestMyFeature:
    """Tests para mi funcionalidad"""
    
    def test_something(self):
        """Test: Descripción del test"""
        from BESTLIB import SomeComponent
        
        result = SomeComponent.do_something()
        assert result == expected_value
```

### 2. Ejecutar

```bash
pytest tests/test_mynewfile.py -v
```

---

## Estado Actual

### ✅ Tests Implementados:

- ✅ Imports de API pública
- ✅ Imports legacy con warnings
- ✅ ChartRegistry
- ✅ Gráficos básicos (scatter, bar, histogram)
- ✅ MatrixLayout creación y configuración
- ✅ ReactiveMatrixLayout básico
- ✅ Compatibilidad legacy

### ⏳ Tests Pendientes (Futuro):

- ⏳ Renderizado completo (requiere Jupyter)
- ⏳ Comunicación JS ↔ Python (requiere Jupyter)
- ⏳ Sistema reactivo completo
- ⏳ Vistas enlazadas end-to-end
- ⏳ Todos los 30+ tipos de gráficos

---

## CI/CD (Futuro)

Configuración recomendada para GitHub Actions:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install pytest pytest-cov
        pip install -e .
    - name: Run tests
      run: pytest --cov=BESTLIB --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

**Última actualización:** Diciembre 2024  
**Mantenido por:** Equipo BESTLIB

