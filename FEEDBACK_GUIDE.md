# 🔄 Guía de Comunicación Bidireccional en BESTLIB

## 📖 Resumen

BESTLIB ahora implementa **comunicación bidireccional completa** entre JavaScript y Python:

- **Python → JavaScript**: Envío de datos, configuraciones y especificaciones de gráficos
- **JavaScript → Python**: Captura de eventos de interacción del usuario (clicks, brush, zoom)

## 🎯 Casos de Uso

### 1. Selección de datos con Brush
El usuario arrastra sobre un gráfico para seleccionar elementos, y Python recibe los datos seleccionados para análisis o filtrado.

### 2. Click en elementos
El usuario hace click en un punto o barra específica, y Python puede mostrar detalles, actualizar otros gráficos, o guardar la selección.

### 3. Dashboard interactivo
Múltiples visualizaciones conectadas donde la interacción en una afecta a otras mediante lógica Python.

## 🛠️ Arquitectura Técnica

### Componentes

1. **matrix.py** (`MatrixLayout`)
   - Clase principal con sistema de callbacks
   - Métodos: `.on(event, callback)` y `.on_global(event, callback)`
   - Registro de instancias con `weakref`
   - Jupyter Comm target para recibir mensajes de JS

2. **matrix.js**
   - Funciones: `getComm()`, `sendEvent()`
   - Renderizado de gráficos D3.js interactivos
   - Captura de eventos del navegador (brush, click, zoom)

3. **Jupyter Comm**
   - Canal de comunicación bidireccional
   - Target: `"bestlib_matrix"`
   - Mensajes con estructura: `{type, div_id, payload}`

### Flujo de Datos

```
Usuario interactúa → JS captura evento → sendEvent() → Jupyter Comm 
    ↓
Python recibe → Busca callback → Ejecuta función → Procesa datos
```

## 📚 API de Uso

### Registrar Callbacks

#### Por Instancia
```python
layout = MatrixLayout("AAA\nBBB")

def mi_callback(payload):
    print(f"Datos recibidos: {payload}")
    # Procesar datos...

layout.on('select', mi_callback)
```

#### Global (todas las instancias)
```python
def handler_global(payload):
    print(f"Evento global: {payload['type']}")

MatrixLayout.on_global('select', handler_global)
```

### Tipos de Eventos

| Evento | Descripción | Payload |
|--------|-------------|---------|
| `select` | Selección con brush | `{type, indices, items}` |
| `point_click` | Click en punto scatter | `{type, index, point}` |

## 📊 Ejemplos de Gráficos

### Bar Chart Interactivo

```python
MatrixLayout.map({
    "B": {
        "type": "bar",
        "data": [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20}
        ],
        "color": "#4a90e2",
        "interactive": True  # Habilita brush
    }
})

layout = MatrixLayout("BBB\nBBB")

layout.on('select', lambda p: print(f"Seleccionado: {p['items']}"))
layout  # Renderizar
```

**Interacciones:**
- Hover: tooltip con categoría y valor
- Brush: arrastra para seleccionar barras
- Evento: envía índices y datos de barras seleccionadas

### Scatter Plot Interactivo

```python
MatrixLayout.map({
    "S": {
        "type": "scatter",
        "data": [
            {"x": 10, "y": 20, "label": "Punto 1"},
            {"x": 30, "y": 40, "label": "Punto 2"}
        ],
        "pointRadius": 5,
        "interactive": True,
        "zoom": True  # Habilita zoom con scroll
    }
})

layout = MatrixLayout("SSS\nSSS")

layout.on('point_click', lambda p: print(f"Click: {p['point']['label']}"))
layout.on('select', lambda p: print(f"{len(p['items'])} puntos seleccionados"))
layout
```

**Interacciones:**
- Click: selecciona punto individual → evento `point_click`
- Brush: selecciona múltiples puntos → evento `select`
- Scroll: zoom in/out
- Hover: tooltip con label y coordenadas

## 🎨 Dashboard Completo

```python
# Callback global para todos los eventos
eventos = []

def procesar_evento(payload):
    eventos.append(payload)
    print(f"Evento #{len(eventos)}: {payload['type']}")

MatrixLayout.on_global('select', procesar_evento)

# Configurar múltiples gráficos
MatrixLayout.map({
    "H": "<h2>Dashboard</h2>",
    "B": {"type": "bar", "data": datos_bar, "interactive": True},
    "S": {"type": "scatter", "data": datos_scatter, "interactive": True},
    "I": "<div>Panel de información</div>"
})

dashboard = MatrixLayout("""
HHHH
BBSS
BBSS
IIIS
""")

dashboard
```

## 🔧 Personalización

### Opciones de Bar Chart

```python
{
    "type": "bar",
    "data": [...],
    "color": "#4a90e2",           # Color de barras
    "hoverColor": "#357abd",      # Color al pasar mouse
    "interactive": True,          # Habilita brush
    "axes": True                  # Muestra ejes
}
```

### Opciones de Scatter Plot

```python
{
    "type": "scatter",
    "data": [...],
    "pointRadius": 5,             # Tamaño de puntos
    "color": "#e24a4a",           # Color por defecto
    "interactive": True,          # Habilita brush y clicks
    "zoom": True,                 # Habilita zoom con scroll
    "axes": True                  # Muestra ejes
}
```

### Estructura de Datos

**Bar Chart:**
```python
[
    {"category": "Nombre", "value": 100},
    {"category": "Otro", "value": 200}
]
```

**Scatter Plot:**
```python
[
    {
        "x": 10.5,
        "y": 20.3,
        "label": "Punto A",
        "color": "#ff0000"  # Opcional, color individual
    }
]
```

## 🚀 Casos de Uso Avanzados

### 1. Filtrado Dinámico

```python
datos_completos = [...]  # Dataset grande

def filtrar_por_seleccion(payload):
    indices = payload['indices']
    datos_filtrados = [datos_completos[i] for i in indices]
    
    # Actualizar otro gráfico con datos filtrados
    print(f"Mostrando {len(datos_filtrados)} elementos")
    # Aquí podrías regenerar otro MatrixLayout

layout.on('select', filtrar_por_seleccion)
```

### 2. Análisis en Tiempo Real

```python
def analizar_seleccion(payload):
    items = payload['items']
    
    if items:
        valores = [item['value'] for item in items]
        print(f"Media: {sum(valores)/len(valores):.2f}")
        print(f"Max: {max(valores)}")
        print(f"Min: {min(valores)}")

layout.on('select', analizar_seleccion)
```

### 3. Coordinación entre Gráficos

```python
seleccion_global = []

def sincronizar_graficos(payload):
    global seleccion_global
    seleccion_global = payload['items']
    print(f"Selección sincronizada: {len(seleccion_global)} items")
    # Todos los gráficos pueden acceder a seleccion_global

MatrixLayout.on_global('select', sincronizar_graficos)
```

## 🐛 Debugging

### Verificar que Comm está activo

```python
# En una celda después de renderizar
layout = MatrixLayout("AAA")
print(f"Div ID: {layout.div_id}")
print(f"Handlers: {layout._handlers}")

# Después de interactuar, verificar en consola del navegador
# Debe aparecer: [BESTLIB] Evento enviado: select {indices: [...], items: [...]}
```

### Probar Callbacks

```python
def test_callback(payload):
    print("✅ Callback ejecutado")
    print(f"Payload: {payload}")

layout.on('select', test_callback)

# Interactúa con el gráfico
# Deberías ver el mensaje en la celda
```

## 📋 Checklist para Implementación

- [ ] Importar `MatrixLayout` correctamente
- [ ] Configurar datos con estructura adecuada (`category/value` o `x/y/label`)
- [ ] Establecer `"interactive": True` en la especificación del gráfico
- [ ] Registrar callbacks con `.on()` o `.on_global()`
- [ ] Renderizar el layout
- [ ] Interactuar con el gráfico (brush, click, zoom)
- [ ] Verificar que los callbacks se ejecutan en Python

## 💡 Tips

1. **Usa callbacks globales** para comportamiento común entre múltiples gráficos
2. **Usa callbacks por instancia** para lógica específica de cada visualización
3. **Estructura tus datos correctamente** antes de pasarlos a MatrixLayout
4. **Prueba en Jupyter clásico** primero (mejor soporte de JavaScript que VS Code)
5. **Revisa la consola del navegador** para mensajes de debug de BESTLIB

## 🎓 Para tu Presentación

Puntos clave a demostrar:

1. **Configuración Simple**: Solo necesitas `.map()` y `.on()`
2. **Bidireccionalidad**: Python envía datos, JS envía eventos
3. **Escalabilidad**: Funciona con múltiples gráficos simultáneos
4. **Interactividad Real**: Brush, zoom, clicks capturados en tiempo real
5. **Arquitectura Limpia**: Separación clara entre visualización (JS) y lógica (Python)

---

**¿Preguntas?** Revisa `examples/demo.ipynb` para ver todos los ejemplos funcionando. 🚀
