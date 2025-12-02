# Protocolo JS ↔ Python

Este documento describe el contrato actual entre `matrix.js` (bundle generado con esbuild) y el backend Python (`CommManager` + `MatrixLayout`).

## Mensajes enviados desde JS

Cada interacción invoca `sendEvent(divId, type, payload)` que abre un Comm de Jupyter con los siguientes campos:

```json
{
  "type": "select",
  "div_id": "matrix-<uuid>",
  "payload": {
    "items": [...],
    "__view_letter__": "A",
    "__graph_type__": "scatter",
    "__is_primary_view__": true
  }
}
```

- `type`: nombre del evento (`select`, `click`, `brush`, etc.).
- `div_id`: identifica la instancia de `MatrixLayout`.
- `payload`: datos específicos del evento. Para `select` debe incluir `items` (lista) y, cuando aplica, las claves auxiliares (`__view_letter__`, `__linked_to__`, etc.).

## Flujo en Python

1. `CommManager` registra cada `div_id` con `register_instance`.
2. Al recibir un mensaje, `_handle_message` normaliza `payload` y:
   - Emite el evento vía `EventManager` si la instancia tiene `_event_manager`.
   - Fallback a `_handlers` (legacy) si existe.
3. Los datos seleccionados se envían al `SelectionModel` asociado y, si corresponde, al `_selection_store` de `ReactiveMatrixLayout`.

## Reglas de versionado

- `items` siempre debe ser lista (aunque esté vacía).
- Para vistas enlazadas, `__view_letter__` y `__linked_to__` deben acompañar el payload.
- Los cambios en el esquema del payload requieren actualizar esta especificación y añadir pruebas en `tests/test_comm_manager.py`.

