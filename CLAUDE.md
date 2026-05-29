# CLAUDE.md

Asistente de voz para vehículo (Jeep) sobre Raspberry Pi, con arquitectura
Edge-to-LLM: `KWS → STT → Gemini → VehicleController`.

👉 **Leé el [README.md](./README.md) para el panorama completo** (cómo funciona,
motores STT, instalación, uso). Para el detalle de arquitectura, ver
[ARCHITECTURE.txt](./ARCHITECTURE.txt).

## Para trabajar en este repo

- Gestor de paquetes: **`uv`**. Instalar deps con `uv sync`, ejecutar con `uv run python <archivo>`.
- Entrypoint principal: `r-pi/kws_monitor.py` (orquesta todo el pipeline).
- El control del vehículo (`VehicleController` en `gemini_engine.py`) está **simulado** — no hay CAN bus ni GPIO reales todavía.
- La NLU usa el **modo JSON estructurado** de Gemini, **no** function calling / Tool-Use nativo. No describir como "Tool-Use".
- El modelo `jeepy_kws_model_quantized.tflite` **no está versionado**; se genera con los scripts de `scripts/`.

## Reglas de documentación

- **No inventar features ni estado.** Verificar contra el código antes de afirmar algo en docs.
- No referenciar archivos que no existen.
- Si el código y la doc difieren, corregir la doc para que diga la verdad.
