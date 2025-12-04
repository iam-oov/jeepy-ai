# Guía de Migración: SCREAM Architecture

## Cambio de Estructura

El proyecto ha sido reorganizado de una estructura monolítica a arquitectura **SCREAM**:

### Estructura Anterior

```
src/
├── state.py               # Entity + State
├── utils.py              # Helpers genéricos
├── audio_capture.py      # Service
├── kws_inference.py      # Service
├── command_processor.py  # Service
└── main.py               # Entry point
```

### Nueva Estructura (SCREAM)

```
jeepy_ai/
├── entities/             # 📦 Domain models
├── repositories/         # 💾 Data access
├── services/             # ⚙️ Business logic
├── controllers/          # 🎮 Orchestration
├── application/          # 📋 Use cases
├── presentation/         # 🎨 UI
└── main.py              # Entry point
```

## Mapeo de Archivos

| Anterior               | Nuevo                                   | Capa SCREAM  | Descripción             |
| ---------------------- | --------------------------------------- | ------------ | ----------------------- |
| `state.py` (partial)   | `entities/system_state.py`              | Entity       | Modelos de estado       |
| `state.py` (partial)   | `entities/error_recovery.py`            | Entity       | Recuperación de errores |
| `utils.py` (partial)   | `entities/audio_chunk.py`               | Entity       | Fragmento de audio      |
| `utils.py` (partial)   | `entities/command.py`                   | Entity       | Comando grabado         |
| `audio_capture.py`     | `services/audio_capture_service.py`     | Service      | Captura de audio        |
| `kws_inference.py`     | `services/kws_inference_service.py`     | Service      | Inferencia KWS          |
| `command_processor.py` | `services/command_processor_service.py` | Service      | Procesamiento STT/NLU   |
| -                      | `repositories/audio_repository.py`      | Repository   | Gestión de archivos WAV |
| -                      | `repositories/command_repository.py`    | Repository   | Historial de comandos   |
| -                      | `repositories/config_repository.py`     | Repository   | Configuración           |
| -                      | `controllers/monitor_controller.py`     | Controller   | Orquestación            |
| -                      | `application/usecases/*.py`             | Application  | Casos de uso            |
| -                      | `presentation/cli/cli_presentation.py`  | Presentation | Interfaz CLI            |
| `main.py`              | `jeepy_ai/main.py`                      | Main         | Punto de entrada        |

## Importaciones Actualizadas

### Antes

```python
from src.state import SystemState, AudioChunk
from src.utils import save_wav_file
from src.audio_capture import AudioCaptureThread
from src.kws_inference import InferenceThread
from src.command_processor import CommandProcessorThread
```

### Después

```python
from jeepy_ai.entities import SystemState, AudioChunk
from jeepy_ai.repositories import AudioRepository
from jeepy_ai.services import AudioCaptureService, KWSInferenceService, CommandProcessorService
from jeepy_ai.controllers import MonitorController
from jeepy_ai.application.usecases import StartMonitoringUseCase
```

## Ejecución

### Antes

```bash
python -m src.main
```

### Después

```bash
python -m jeepy_ai.main
```

O directamente:

```bash
python jeepy_ai/main.py
```

## Cambios en Nombres de Clases

| Anterior                 | Nuevo                     | Razón                             |
| ------------------------ | ------------------------- | --------------------------------- |
| `AudioCaptureThread`     | `AudioCaptureService`     | Es un servicio, no solo un thread |
| `InferenceThread`        | `KWSInferenceService`     | Más descriptivo                   |
| `CommandProcessorThread` | `CommandProcessorService` | Consistencia con nomenclatura     |
| N/A                      | `MonitorController`       | Nueva capa de orquestación        |
| N/A                      | `AudioRepository`         | Abstrae acceso a archivos WAV     |

## Beneficios de la Migración

### ✅ Organización

- Código organizado en 6 capas claras
- Fácil entender dónde va cada componente nuevo

### ✅ Testabilidad

- Cada capa puede ser testeada aisladamente
- Fácil crear mocks de dependencias

### ✅ Escalabilidad

- Agregar UI web no afecta lógica de negocio
- Cambiar persistencia es trivial

### ✅ Mantenibilidad

- Nuevo dev entiende estructura en 1 hora
- Cambios son localizados

### ✅ Profesionalismo

- Arquitectura reconocida en la industria
- Facilita colaboración en equipo

## Archivos Legados

Los archivos antiguos están preservados en `_legacy/`:

```
_legacy/
├── __init__.py
├── audio_capture.py
├── command_processor.py
├── kws_inference.py
├── main.py
├── state.py
└── utils.py
```

Se pueden consultar para entender la lógica original, pero **NO SE DEBEN USAR** en la nueva arquitectura.

## Próximos Pasos

### Implementación Pendiente

1. ✅ Estructura SCREAM creada
2. ⏳ Completar servicios con lógica de `_legacy/`
3. ⏳ Inyectar dependencias STT y Gemini
4. ⏳ Crear test suite
5. ⏳ Actualizar CI/CD

### Para Desarrolladores

Si necesitas:

- **Agregar nueva feature**: Crea use case en `application/`
- **Cambiar persistencia**: Modifica solo `repositories/`
- **Agregar nueva UI**: Crea presentación en `presentation/`
- **Agregar lógica nueva**: Crea servicio en `services/`
- **Agregar modelo nuevo**: Crea entity en `entities/`

## Soporte

Para dudas sobre la nueva arquitectura, ver:

- `SCREAM_ARCHITECTURE.md` - Guía completa
- Código comentado en cada módulo
- Docstrings en clases y métodos

## Conclusión

Esta reorganización transforma Jeepy AI de un monolito difícil de mantener a una arquitectura profesional, escalable y testeable. El código es ahora más modular, reutilizable y fácil de entender.

**Welcome to the SCREAM Architecture! 🎬**
