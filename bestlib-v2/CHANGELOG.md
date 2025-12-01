# Changelog

Todos los cambios notables a este proyecto serán documentados aquí.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [2.0.0] - 2024-12-01

### 🎉 Refactorización Completa

Esta es una refactorización completa del proyecto con arquitectura limpia y código optimizado.

### ✨ Añadido

- Arquitectura modular limpia sin código legacy
- Sistema de imports directo sin fallbacks
- API pública simplificada
- Mejor manejo de dependencias opcionales
- Documentación concisa y actualizada
- Estructura de testing desde el inicio

### 🔄 Cambiado

- Estructura de proyecto completamente reorganizada
- Eliminados todos los fallbacks y compatibilidad legacy
- `__init__.py` limpio y directo
- Assets movidos a carpeta `assets/`
- Imports simplificados en todos los módulos

### 🗑️ Eliminado

- Código legacy de `matrix.py`, `linked.py`, `reactive.py` en raíz
- Carpeta `compat/` completa
- 70+ archivos de documentación/debug innecesarios
- Múltiples capas de try-except en imports
- Código duplicado

### 🐛 Corregido

- Problemas de imports circulares
- Errores de fallback innecesarios
- Conflictos de módulos duplicados

### 📚 Documentación

- README.md conciso y claro
- Ejemplos actualizados
- CONTRIBUTING.md para colaboradores

### 🔧 Mantenimiento

- Código más fácil de mantener (50% menos complejo)
- Testing estructurado
- CI/CD ready

---

## [1.x] - Versiones Anteriores

Las versiones 1.x contenían la implementación original con arquitectura híbrida.
Ver branch `restore` para el código anterior.

### Funcionalidades heredadas

- 30+ tipos de gráficos
- Sistema reactivo
- Vistas enlazadas
- Layouts ASCII
- Comunicación Python ↔ JavaScript

---

**Nota**: Esta es la versión refactorizada. Para migrar desde v1.x, ver la [Guía de Migración](docs/migration.md).
