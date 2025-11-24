# 🧪 Guía de Pruebas para BESTLIB en Google Colab

## 📋 Resumen

Esta guía te ayudará a probar todas las funcionalidades de **interactividad, selección y linked views** de BESTLIB en Google Colab (branch `restore`).

## 🎯 Funcionalidades a Probar

### ✅ Funcionalidades Implementadas

1. **Scatter Plot Interactivo** - Brush selection funcionando
2. **Bar Chart Interactivo** - Click en barras para seleccionar
3. **Linked Views** - Múltiples vistas sincronizadas automáticamente
4. **ReactiveMatrixLayout** - Sistema reactivo con SelectionModel
5. **Callbacks Python** - Eventos JavaScript → Python
6. **Variables de Selección** - Guardar datos en variables Python
7. **Historial de Selecciones** - Tracking de todas las selecciones
8. **Callbacks Múltiples** - Varios handlers para el mismo evento

## 🚀 Cómo Usar

### Opción 1: Usar el archivo Python en Colab

1. **Subir el archivo a Colab:**
   - Abre Google Colab: https://colab.research.google.com/
   - Ve a `File` → `Upload notebook`
   - Sube el archivo `TEST_COLAB_COMPLETO.py`
   - Colab lo convertirá automáticamente a un notebook

2. **Ejecutar las celdas:**
   - Ejecuta las celdas en orden (de arriba a abajo)
   - Sigue las instrucciones en cada sección

### Opción 2: Copiar y pegar celdas

1. Abre un nuevo notebook en Colab
2. Copia las celdas del archivo `TEST_COLAB_COMPLETO.py`
3. Pégalas como celdas de código o markdown según corresponda

## 📊 Estructura del Test

### Paso 1: Instalación
```python
!pip install git+https://github.com/NahiaEscalante/bestlib.git@restore
```

### Paso 2: Preparar Datos
- Crea un dataset sintético tipo Iris con 150 muestras
- 4 variables numéricas + 1 categórica (species)

### Paso 3: Test 1 - Scatter Plot Interactivo
- **Qué probar:** Brush selection básica
- **Cómo probarlo:** Arrastra el mouse sobre el gráfico
- **Resultado esperado:** Ver datos seleccionados en la consola

### Paso 4: Test 2 - Linked Views
- **Qué probar:** Sincronización automática entre vistas
- **Componentes:**
  - Scatter plot (vista principal)
  - Bar chart (enlazado)
  - Histogram (enlazado)
- **Cómo probarlo:** Selecciona en el scatter plot
- **Resultado esperado:** Bar chart e histogram se actualizan automáticamente

### Paso 5: Test 3 - Bar Chart Interactivo
- **Qué probar:** Bar chart como vista principal
- **Cómo probarlo:** Click en una barra
- **Resultado esperado:** Datos guardados en variable Python

### Paso 6: Test 4 - Dashboard Completo
- **Qué probar:** Sistema completo con 5 visualizaciones
- **Componentes:**
  - Scatter plot (principal)
  - Bar chart (enlazado)
  - Histogram (enlazado)
  - Pie chart (enlazado)
  - Correlation heatmap (solo lectura)
- **Cómo probarlo:** Selecciona en el scatter plot
- **Resultado esperado:** 4 vistas se actualizan simultáneamente

### Paso 7: Test 5 - Sistema de Comunicación
- **Qué probar:** Estado del sistema JavaScript ↔ Python
- **Resultado esperado:** 
  - `comm_registered: True`
  - Instancias activas visibles
  - Handlers registrados

### Paso 8: Test 6 - Historial de Selecciones
- **Qué probar:** Tracking de selecciones
- **Resultado esperado:** Ver lista de todas las selecciones anteriores

### Paso 9: Test 7 - Callbacks Múltiples
- **Qué probar:** Múltiples callbacks para el mismo evento
- **Resultado esperado:** Ver 3 mensajes por cada selección

### Paso 10: Resumen y Verificación
- Resumen automático de todos los tests
- Checklist de funcionalidades

## 🔍 Verificaciones Clave

### ✅ Scatter Plot Interactivo

**Comportamiento esperado:**
1. Aparece un gráfico de dispersión con puntos de colores
2. Al arrastrar el mouse sobre puntos, aparece un rectángulo de selección
3. Al soltar, se muestran los datos seleccionados en la consola
4. Los datos están en la variable `selected_items`

**Si no funciona:**
- Verifica que `interactive=True` esté configurado
- Activa debug: `MatrixLayout.set_debug(True)`
- Revisa la consola de JavaScript (F12 en el navegador)

### ✅ Linked Views

**Comportamiento esperado:**
1. Al seleccionar en el scatter plot (superior):
   - El bar chart (inferior izquierdo) se actualiza mostrando solo las categorías seleccionadas
   - El histogram (inferior derecho) se actualiza mostrando solo los valores seleccionados
2. Las actualizaciones son **automáticas** y **sincronizadas**
3. No es necesario re-ejecutar ninguna celda

**Si no funciona:**
- Verifica que `linked_to='S'` esté configurado en los gráficos enlazados
- Asegúrate de que el scatter plot tiene `interactive=True`
- Verifica que los datos tienen las columnas correctas
- Activa debug: `MatrixLayout.set_debug(True)`

### ✅ Bar Chart Interactivo (Vista Principal)

**Comportamiento esperado:**
1. Al hacer click en una barra:
   - Los datos de esa categoría se guardan en `bar_selected_data`
   - El SelectionModel se actualiza
2. Los datos están disponibles inmediatamente como DataFrame

**Si no funciona:**
- Verifica que `interactive=True` esté en el bar chart
- Verifica que `selection_var='bar_selected_data'` esté configurado
- Asegúrate de que no hay `linked_to` (vistas principales no deben estar enlazadas)

### ✅ Callbacks

**Comportamiento esperado:**
1. Cada selección ejecuta los callbacks registrados
2. Los callbacks reciben un `payload` con:
   - `items`: Lista de diccionarios con los datos seleccionados
   - `count`: Número de elementos seleccionados
   - `type`: Tipo de gráfico ('scatter', 'bar', etc.)

**Si no funciona:**
- Verifica que el comm esté registrado: `MatrixLayout.get_status()`
- Asegúrate de que el callback está registrado ANTES de mostrar el gráfico
- Activa debug para ver los eventos: `MatrixLayout.set_debug(True)`

## 🐛 Solución de Problemas

### Problema: "Los gráficos no se muestran"

**Soluciones:**
1. Verifica que estás en Google Colab (no Jupyter local)
2. Ejecuta `MatrixLayout.register_comm(force=True)`
3. Reinicia el runtime y vuelve a ejecutar

### Problema: "Las selecciones no funcionan"

**Soluciones:**
1. Activa debug: `MatrixLayout.set_debug(True)`
2. Verifica que `interactive=True` esté configurado
3. Revisa los mensajes en la consola
4. Verifica el estado del comm: `MatrixLayout.get_status()`

### Problema: "Linked views no se actualizan"

**Soluciones:**
1. Verifica que `linked_to` apunte a la letra correcta
2. Asegúrate de que la vista principal tenga `interactive=True`
3. Revisa que los datos tengan las columnas correctas
4. Activa debug para ver los eventos
5. Verifica que no haya errores en la consola de JavaScript (F12)

### Problema: "Error al importar BESTLIB"

**Soluciones:**
1. Reinstala con force:
   ```python
   !pip install --force-reinstall git+https://github.com/NahiaEscalante/bestlib.git@restore
   ```
2. Reinicia el runtime de Colab
3. Verifica que estés usando el branch correcto (`restore`)

### Problema: "Callbacks no se ejecutan"

**Soluciones:**
1. Verifica que el callback está registrado ANTES de mostrar el gráfico
2. Asegúrate de que el comm esté registrado
3. Activa debug para ver si los eventos llegan
4. Verifica que el callback tenga la firma correcta: `def callback(payload):`

## 📊 Datos de Prueba

El test usa un dataset sintético similar a Iris:
- **150 muestras**
- **4 variables numéricas:** sepal_length, sepal_width, petal_length, petal_width
- **1 variable categórica:** species (setosa, versicolor, virginica)

Este dataset es ideal para probar:
- Scatter plots (2 variables numéricas)
- Bar charts (distribución de especies)
- Histograms (distribución de variables numéricas)
- Correlación entre variables

## 🎯 Checklist de Funcionalidades

Usa este checklist para verificar que todo funciona:

- [ ] **Instalación exitosa** - BESTLIB se importa sin errores
- [ ] **Scatter plot interactivo** - Brush selection funciona
- [ ] **Selección capturada en Python** - Variable `selected_items` tiene datos
- [ ] **Linked views básico** - Scatter → Bar + Histogram se actualiza
- [ ] **Bar chart interactivo** - Click en barra funciona
- [ ] **Variables de selección** - Datos guardados en variable Python
- [ ] **Dashboard completo** - 5 vistas, 4 sincronizadas
- [ ] **Sistema de comunicación** - Comm registrado correctamente
- [ ] **Historial de selecciones** - SelectionModel guarda historial
- [ ] **Callbacks múltiples** - 3 callbacks se ejecutan correctamente
- [ ] **Debug mode** - Mensajes detallados visibles

## 📚 Recursos Adicionales

### Documentación
- **README Principal:** `docs/README.md`
- **Ejemplos:** Carpeta `examples/`
- **API Reference:** Ver código fuente en `BESTLIB/`

### Links Útiles
- **Repositorio:** https://github.com/NahiaEscalante/bestlib
- **Issues:** https://github.com/NahiaEscalante/bestlib/issues
- **Google Colab:** https://colab.research.google.com/

### Comandos Útiles

```python
# Activar modo debug
MatrixLayout.set_debug(True)

# Ver estado del sistema
status = MatrixLayout.get_status()
print(status)

# Registrar comm manualmente
MatrixLayout.register_comm(force=True)

# Ver datos seleccionados
selection_model.get_items()
selection_model.get_count()
selection_model.get_history()

# Limpiar selección
selection_model.clear()
```

## 💡 Tips

1. **Ejecuta las celdas en orden** - Los tests están diseñados para ejecutarse secuencialmente
2. **Lee las instrucciones** - Cada test tiene instrucciones específicas
3. **Usa debug mode** - Activa `MatrixLayout.set_debug(True)` para ver eventos
4. **Verifica los datos** - Usa las celdas de verificación después de cada test
5. **Experimenta** - Prueba diferentes selecciones y combinaciones

## 🎉 ¡Éxito!

Si todos los tests pasan, BESTLIB está funcionando correctamente en Google Colab con:
- ✅ Interactividad completa (brush, clicks)
- ✅ Selección bidireccional (JavaScript ↔ Python)
- ✅ Linked views sincronizadas automáticamente
- ✅ Sistema reactivo con SelectionModel
- ✅ Callbacks y eventos funcionando

---

**¿Encontraste un bug?** Por favor reporta en: https://github.com/NahiaEscalante/bestlib/issues

**¿Tienes preguntas?** Revisa la documentación o abre un issue.
