# 🚀 Usar BESTLIB en Google Colab

Google Colab es la forma **MÁS FÁCIL** de usar BESTLIB con visualizaciones D3.js.

## ✅ ¿Por qué Google Colab?

| Característica | Google Colab | VS Code Notebook |
|---------------|--------------|------------------|
| Soporte D3.js | ✅ Excelente | ⚠️ Limitado |
| Carga de CDN | ✅ Sin problemas | ❌ Bloqueado |
| Renderizado | ✅ Navegador completo | ⚠️ Básico |
| Interactividad | ✅ Total | ⚠️ Parcial |
| **Recomendación** | **👍 USA ESTO** | Solo Python puro |

## 🎯 Inicio Rápido (2 minutos)

### Opción 1: Abrir directamente en Colab

Haz click aquí:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NahiaEscalante/bestlib/blob/pruebas/examples/demo_colab.ipynb)

### Opción 2: Manual

1. Ve a [Google Colab](https://colab.research.google.com/)
2. **Archivo → Abrir notebook → GitHub**
3. Pega: `https://github.com/NahiaEscalante/bestlib`
4. Selecciona: `pruebas` (rama)
5. Abre: `examples/demo_colab.ipynb`

## 📦 Instalación en Colab

En la primera celda del notebook:

```python
# Clonar repositorio
!git clone https://github.com/NahiaEscalante/bestlib.git
%cd bestlib
!git checkout pruebas

# Instalar
!pip install -e .

# Importar
from BESTLIB.matrix import MatrixLayout
```

## 🎨 Ejemplo Básico

```python
# Configurar visualización
MatrixLayout.map({
    'C': {
        "type": "circle",
        "cx": 50,
        "cy": 50,
        "r": 40,
        "fill": "#e74c3c"
    }
})

# Crear y mostrar
layout = MatrixLayout("C")
layout  # Se renderiza automáticamente en Colab!
```

## 🔥 Ventajas en Colab

✅ **D3.js funciona perfectamente** - Sin problemas de carga  
✅ **Renderizado completo** - Todas las animaciones y transiciones  
✅ **Interactividad total** - Click, hover, zoom, brush  
✅ **Gratis** - No necesitas instalar nada localmente  
✅ **Compartir fácil** - Solo comparte el link  

## 📚 Ejemplos Disponibles

| Notebook | Descripción | Link |
|----------|-------------|------|
| `demo_colab.ipynb` | Demo completo con todos los gráficos | [Abrir](https://colab.research.google.com/github/NahiaEscalante/bestlib/blob/pruebas/examples/demo_colab.ipynb) |
| `demo_matriz.ipynb` | Solo layouts y grids | [Abrir](https://colab.research.google.com/github/NahiaEscalante/bestlib/blob/pruebas/examples/demo_matriz.ipynb) |

## ⚠️ Notas para VS Code

Si aún quieres usar VS Code (no recomendado para D3.js):

1. D3 debe estar descargado localmente (`BESTLIB/d3.min.js`)
2. Puede haber problemas de renderizado
3. Mejor para proyectos sin visualizaciones interactivas

**Recomendación:** Usa Colab para desarrollo con visualizaciones, VS Code para el resto.

## 🤝 Contribuir

1. Haz fork del repositorio
2. Crea tu rama: `git checkout -b feature/mi-feature`
3. Commit: `git commit -am 'Agregar feature'`
4. Push: `git push origin feature/mi-feature`
5. Crea un Pull Request

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/NahiaEscalante/bestlib/issues)
- **Documentación**: [docs/](../docs/)
- **Ejemplos**: [examples/](.)

---

**✨ BESTLIB** - Visualizaciones D3.js en Python, optimizado para Google Colab
