# 📝 Changelog - BESTLIB

Todos los cambios importantes del proyecto están documentados en este archivo.

---

## [0.1.1] - 2025-11-09

### 🐛 Correcciones Críticas

#### Errores de Indentación en `reactive.py`
- **Problema:** La función `add_confusion_matrix()` estaba definida fuera de la clase `ReactiveMatrixLayout` (líneas 1442-1502)
- **Problema:** Las propiedades `@property` (`selection_widget`, `items`, `selected_data`, `count`) estaban mal indentadas después de la función standalone `_sanitize_for_json()` (líneas 1576-1628)
- **Solución:** Movida `add_confusion_matrix()` dentro de `ReactiveMatrixLayout` como método de instancia
- **Solución:** Movidas todas las propiedades `@property` dentro de `ReactiveMatrixLayout`
- **Impacto:** Ahora `layout.add_confusion_matrix()` y `layout.selected_data` funcionan correctamente
- **Archivos modificados:** `/BESTLIB/reactive.py`

### 📦 Dependencias

#### Actualización de `requirements.txt`
- **Agregado:** `pandas>=1.3.0` (requerido para DataFrames)
- **Agregado:** `numpy>=1.20.0` (requerido para histogramas, violines, etc.)
- **Documentado:** `scikit-learn>=1.0.0` como dependencia opcional (solo para `add_confusion_matrix()`)
- **Archivos modificados:** `/requirements.txt`

### 📊 Dataset de Pruebas

#### Creación de `iris.csv`
- **Agregado:** Dataset Iris completo (150 filas, 5 columnas)
- **Columnas:** `sepal_length`, `sepal_width`, `petal_length`, `petal_width`, `species`
- **Especies:** setosa (50), versicolor (50), virginica (50)
- **Ubicación:** `/examples/iris.csv`
- **Propósito:** Facilitar testing y ejemplos de uso

### 🧪 Tests y Documentación

#### Notebook de Tests Completo
- **Agregado:** `/examples/test_completo_iris.ipynb`
- **Contenido:** Tests de todos los tipos de gráficos con dataset Iris
- **Gráficos probados:**
  1. Scatter Plot (con brush selection)
  2. Bar Chart (interactivo)
  3. Histogram (distribución bimodal)
  4. Boxplot (por categoría)
  5. Correlation Heatmap (matriz 4x4)
  6. Line Chart (múltiples series)
  7. Pie Chart (3 sectores)
  8. Violin Plot (densidades)
  9. RadViz (proyección multidimensional)
  10. LinkedViews (vistas enlazadas)
  11. ReactiveMatrixLayout (sistema reactivo)
  12. Layout Completo (matriz 2x2)

#### Documentación de Análisis
- **Agregado:** `/ANALISIS_ERRORES_Y_SOLUCION.md`
- **Contenido:** Análisis completo de errores, causas, efectos y soluciones
- **Incluye:** Plan de corrección progresivo, checklist de verificación, plan de testing

---

## [0.1.0] - 2025-11-08

### ✨ Características Iniciales

#### Arquitectura Base
- Clase `MatrixLayout` para layouts ASCII
- Sistema de comunicación bidireccional (Jupyter Comm)
- Soporte para pandas DataFrames y listas de diccionarios
- Integración con D3.js v7

#### Tipos de Gráficos Implementados
1. **Scatter Plot** - Gráfico de dispersión con brush selection
2. **Bar Chart** - Gráfico de barras simple
3. **Grouped Bar Chart** - Gráfico de barras agrupadas
4. **Histogram** - Histograma con bins configurables
5. **Boxplot** - Diagrama de caja y bigotes
6. **Heatmap** - Mapa de calor genérico
7. **Correlation Heatmap** - Matriz de correlación
8. **Line Chart** - Gráfico de líneas (simple y múltiples series)
9. **Pie Chart** - Gráfico circular
10. **Violin Plot** - Gráfico de violín (densidad)
11. **RadViz** - Visualización radial multidimensional

#### Sistema de Vistas Enlazadas
- Clase `LinkedViews` para sincronizar múltiples gráficos
- Actualización automática al seleccionar datos
- Soporte para scatter plots y bar charts enlazados

#### Sistema Reactivo
- Clase `ReactiveMatrixLayout` con soporte para reactividad
- Clase `SelectionModel` para gestionar selecciones
- Actualización automática de gráficos enlazados vía JavaScript
- Soporte para múltiples scatter plots con bar charts independientes

#### Métodos Helper
- `map_scatter()` - Crear scatter plot desde DataFrame
- `map_barchart()` - Crear bar chart desde DataFrame
- `map_histogram()` - Crear histograma desde DataFrame
- `map_boxplot()` - Crear boxplot desde DataFrame
- `map_heatmap()` - Crear heatmap desde DataFrame
- `map_correlation_heatmap()` - Calcular y visualizar correlaciones
- `map_line()` - Crear line chart desde DataFrame
- `map_pie()` - Crear pie chart desde DataFrame
- `map_violin()` - Crear violin plot desde DataFrame
- `map_radviz()` - Crear RadViz desde DataFrame
- `map_grouped_barchart()` - Crear grouped bar chart desde DataFrame

#### Interactividad
- Brush selection en scatter plots
- Click en puntos y barras
- Callbacks personalizables con `.on(event, callback)`
- Comunicación bidireccional Python ↔ JavaScript

---

## 🔮 Próximas Versiones

### [0.2.0] - Planificado
- [ ] Soporte para más tipos de gráficos (treemap, sankey, network)
- [ ] Exportación de gráficos a PNG/SVG
- [ ] Temas personalizables (dark mode, custom colors)
- [ ] Animaciones y transiciones configurables
- [ ] Tooltips personalizables
- [ ] Zoom y pan en gráficos

### [0.3.0] - Planificado
- [ ] Integración con Plotly para gráficos 3D
- [ ] Soporte para streaming de datos en tiempo real
- [ ] Dashboard builder interactivo
- [ ] Exportación a HTML standalone

---

## 📚 Guía de Migración

### De 0.1.0 a 0.1.1

No hay cambios breaking. Todas las funcionalidades existentes siguen funcionando.

**Nuevas funcionalidades disponibles:**
```python
# Ahora puedes usar add_confusion_matrix correctamente
from BESTLIB import ReactiveMatrixLayout

layout = ReactiveMatrixLayout("SH")
layout.set_data(df)
layout.add_scatter('S', x_col='x', y_col='y', category_col='class', interactive=True)
layout.add_confusion_matrix('H', y_true_col='true_label', y_pred_col='pred_label')
layout.display()

# Acceso a datos seleccionados
print(layout.selected_data)  # Ahora funciona correctamente
print(layout.count)          # Número de elementos seleccionados
```

**Instalación de nuevas dependencias:**
```bash
pip install pandas>=1.3.0 numpy>=1.20.0

# Opcional (solo para confusion matrix)
pip install scikit-learn>=1.0.0
```

---

## 🤝 Contribuciones

Este proyecto es mantenido por:
- Nahia Escalante
- Alejandro
- Max

Para reportar bugs o sugerir mejoras, por favor crea un issue en el repositorio.

---

## 📄 Licencia

Este proyecto está bajo la licencia especificada en el archivo LICENSE del repositorio.
