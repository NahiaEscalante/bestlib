# BESTLIB Refactor Plan

## Objetivo general
Reconstruir BESTLIB en capas modulares y probadas: dependencia declarada, núcleo Python unificado, capa reactiva segura, bundle JS moderno y documentación lista para releases.

## Progreso por fases

- [x] **F1. Auditoría inicial**  
  - Inventario de módulos y dependencias reales.  
  - Resultado: estructura confirmada (`BESTLIB/` + assets), vacíos detectados en `pyproject/setup`.

- [ ] **F2. Dependencias y entorno**  
  - Declarar paquetes requeridos (ipywidgets, traitlets, pandas, numpy, scipy, jupyter).  
  - Crear `requirements-dev.txt` + scripts `make lint/test/build`.

- [ ] **F3. Núcleo Python**  
  - Aislar `_map` por instancia, validar layouts ↔ mappings.  
  - Unificar registries y cubrir charts con pytest.  
  - Refactor `data` helpers y limpieza de imports defensivos.

- [ ] **F4. Layouts y Reactividad**  
  - Consolidar `BESTLIB/layouts` vs `BESTLIB/matrix.py`.  
  - Reescribir capa reactiva sin variables globales ni threads ad-hoc.  
  - Resolver `LinkedViews` legacy (fusionar o documentar deprecación).

- [ ] **F5. Charts y specs**  
  - Completar charts pendientes (violin, ribbon, etc.) o retirarlos.  
  - Estandarizar specs (`encoding`, `options`, `interactive`).  
  - Actualizar notebooks y ejemplos a la API modular.

- [ ] **F6. Render / JS**  
  - Modularizar `matrix.js`, usar bundler (Vite/Rollup) con `d3.min.js` local.  
  - Documentar protocolo JS ↔ Python y cubrir con tests de snapshot/eventos.

- [ ] **F7. QA & Releases**  
  - Configurar CI (pytest, ruff/black, mypy opcional).  
  - Pipeline de empaquetado (wheel + publish).  
  - Actualizar documentación, changelog y guías de contribución/release.

## TODOs detallados
1. ✅ Auditar estructura y dependencias actuales.
2. ⏳ Definir dependencias en pyproject/setup y entorno reproducible.
3. ⏳ Aislar estado de MatrixLayout y validar mapeos.
4. ⏳ Unificar registries y cubrir charts con tests.
5. ⏳ Refactor data utils y limpieza de imports.
6. ⏳ Consolidar MatrixLayout legacy vs modular.
7. ⏳ Reescribir capa reactiva sin variables globales.
8. ⏳ Fusionar LinkedViews legacy o documentar deprecación.
9. ⏳ Completar charts pendientes y validar specs.
10. ⏳ Reestructurar matrix.js en bundle modular.
11. ⏳ Documentar protocolo JS↔Python y añadir tests.
12. ⏳ Configurar CI, lint, tests y empaquetado.
13. ⏳ Actualizar docs, notebooks y guías de release.

_Actualizar este archivo al cierre de cada tarea._

