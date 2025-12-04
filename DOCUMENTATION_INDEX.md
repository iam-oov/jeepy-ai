# Jeepy AI - Documentación Completa

## 📑 Índice de Documentos

### 🏗️ Arquitectura

- **[SCREAM_ARCHITECTURE.md](SCREAM_ARCHITECTURE.md)** - Guía completa de la arquitectura SCREAM
- **[SCREAM_VISUAL.md](SCREAM_VISUAL.md)** - Diagramas visuales y flujos de datos
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Guía de migración desde estructura anterior
- **[README_SCREAM.md](README_SCREAM.md)** - README con quick start y configuración

### 📚 Proyecto Original

- **[PROJECT_WORKFLOWS.md](PROJECT_WORKFLOWS.md)** - Flujos de trabajo: KWS, STT, NLU
- **[PLATFORM_COMPATIBILITY.md](PLATFORM_COMPATIBILITY.md)** - Compatibilidad multiplataforma
- **[AUDIO_PROCESSING_ARCHITECTURE.md](AUDIO_PROCESSING_ARCHITECTURE.md)** - Arquitectura de procesamiento de audio
- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - Propuestas de mejora (algunas implementadas)

## 🗂️ Estructura del Código

```
jeepy_ai/
├── __init__.py                           # Paquete raíz
├── main.py                              # 🚀 Punto de entrada
│
├── presentation/                        # 🎨 SCREEN LAYER
│   ├── __init__.py
│   └── cli/
│       ├── __init__.py
│       └── cli_presentation.py          # Interfaz CLI
│
├── application/                         # 📋 APPLICATION LAYER
│   ├── __init__.py
│   └── usecases/
│       ├── __init__.py
│       ├── start_monitoring_usecase.py
│       ├── stop_monitoring_usecase.py
│       └── get_system_status_usecase.py
│
├── controllers/                         # 🎮 CONTROLLER LAYER
│   ├── __init__.py
│   └── monitor_controller.py            # Orquestación principal
│
├── services/                            # ⚙️ SERVICE LAYER (Threads)
│   ├── __init__.py
│   ├── audio_capture_service.py         # Thread 1: Captura de audio
│   ├── kws_inference_service.py         # Thread 2: Detección KWS
│   └── command_processor_service.py     # Thread 3: Procesamiento STT/NLU
│
├── repositories/                        # 💾 REPOSITORY LAYER
│   ├── __init__.py
│   ├── audio_repository.py              # Gestión de archivos WAV
│   ├── command_repository.py            # Historial de comandos
│   └── config_repository.py             # Configuración
│
└── entities/                            # 📦 ENTITY LAYER (Domain Models)
    ├── __init__.py
    ├── audio_chunk.py                   # Fragmento de audio
    ├── system_state.py                  # Estado del sistema (thread-safe)
    ├── error_recovery.py                # Gestión de errores
    └── command.py                       # Comando grabado
```

## 🚀 Quick Start

```bash
# 1. Instalar dependencias
uv install
# o: pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con API keys

# 3. Ejecutar
python -m jeepy_ai.main
# o: python jeepy_ai/main.py

# En desarrollo: Ver logs
tail -f jeepy_ai_monitor.log
```

## 📊 Capas SCREAM Explicadas

### 🎨 SCREEN (Presentation)

- **Dónde**: `presentation/cli/`
- **Qué**: Interfaz CLI para interacción del usuario
- **No sabe**: Lógica de negocio, APIs, persistencia

### 📋 APPLICATION (Use Cases)

- **Dónde**: `application/usecases/`
- **Qué**: Casos de uso: iniciar/detener monitoreo, obtener estado
- **No sabe**: Implementación específica, UI, persistencia

### 🎮 CONTROLLER (Orchestration)

- **Dónde**: `controllers/`
- **Qué**: Coordina servicios y flujos
- **No sabe**: Detalles específicos de cada servicio

### ⚙️ SERVICE (Business Logic)

- **Dónde**: `services/`
- **Qué**: Implementa funcionalidad (threads)
  - AudioCaptureService: Captura continua
  - KWSInferenceService: Detección de palabra clave
  - CommandProcessorService: STT/NLU
- **No sabe**: UI, persistencia, orquestación

### 💾 REPOSITORY (Data Access)

- **Dónde**: `repositories/`
- **Qué**: Abstrae acceso a datos
  - AudioRepository: Archivos WAV
  - CommandRepository: Historial JSON
  - ConfigRepository: Configuración
- **No sabe**: Lógica de negocio

### 📦 ENTITY (Domain Models)

- **Dónde**: `entities/`
- **Qué**: Objetos puros del dominio
  - SystemState: Estado compartido (thread-safe)
  - AudioChunk: Fragmento de audio
  - CommandRecord: Comando grabado
  - ErrorRecoveryManager: Gestión de errores
- **No sabe**: Nada (módulos externos solo stdlib)

## 🧵 Model de Threading

```
Main Thread (CLI)
├─ Loop principal
├─ Muestra estado
└─ Captura Ctrl+C

AudioCaptureService Thread
├─ Lee micrófono 24/7
├─ Produce: audio_queue (LIFO)
└─ Reconexión automática

KWSInferenceService Thread
├─ Procesa audio real-time
├─ Detecta palabra clave
├─ Consume: audio_queue
└─ Produce: processing_queue

CommandProcessorService Thread
├─ Transcribe (STT)
├─ Interpreta (Gemini)
├─ Consume: processing_queue
└─ Guarda resultados
```

## 📈 Flujo de Ejecución

1. **Inicio**: `python jeepy_ai/main.py`
2. **Setup**: CLIPresentation → MonitorController
3. **Threads**: 3 servicios inician en paralelo
4. **Loop**: Main actualiza UI cada 2 segundos
5. **Procesamiento**: Threads procesan audio concurrentemente
6. **Shutdown**: Ctrl+C → graceful stop

## 🔄 Cambios de Estado

```
MONITORING ──[KWS]──> RECORDING ──[Silencio]──> PROCESSING ──[STT]──> TRANSCRIBING
   ▲                                                                        │
   │                                                                        ▼
   │                                            PROCESSING_NLU ◄──[Gemini]─┤
   │                                                    │
   │                                                    ▼
   └────────────────────────────────────[Acción completada]───────────────┘
```

## 🛠️ Desarrollo

### Agregar Nueva Feature

**Ejemplo**: Notificaciones por email

1. **Entity** (opcional): Crear modelo si necesario

   ```python
   # entities/notification.py
   @dataclass
   class EmailNotification:
       to: str
       subject: str
       body: str
   ```

2. **Repository**: Crear acceso a datos

   ```python
   # repositories/email_repository.py
   class EmailRepository:
       def send_email(self, notification: EmailNotification):
           # Lógica de envío
           pass
   ```

3. **Service**: Implementar lógica

   ```python
   # services/notification_service.py
   class NotificationService:
       def __init__(self, email_repo: EmailRepository):
           self.email_repo = email_repo

       def notify_command_executed(self, command: str):
           # Lógica
           pass
   ```

4. **Controller**: Integrar en orquestación

   ```python
   # controllers/monitor_controller.py
   self.notification_service = NotificationService(email_repo)
   ```

5. **Use Case** (opcional): Crear caso de uso
   ```python
   # application/usecases/send_notification_usecase.py
   class SendNotificationUseCase:
       def execute(self, notification):
           self.service.send_email(notification)
   ```

**Cambios en otras capas**: ✅ CERO

### Testing

```bash
# Unit tests
pytest tests/unit/test_entities.py
pytest tests/unit/test_repositories.py

# Integration tests
pytest tests/integration/test_monitor_controller.py

# Coverage
pytest --cov=jeepy_ai tests/
```

## 📝 Convenciones de Código

### Naming

- Classes: PascalCase (`MonitorController`, `AudioChunk`)
- Methods: snake_case (`start_monitoring()`, `get_state()`)
- Constants: UPPER_SNAKE_CASE (`STATE_MONITORING`, `MAX_RETRIES`)
- Private: Prefijo `_` (`_finish_recording()`)

### Imports

```python
# Orden: stdlib, third-party, local
import threading
import queue

import numpy as np
import pyaudio

from jeepy_ai.entities import SystemState
from jeepy_ai.repositories import AudioRepository
```

### Docstrings

```python
def start(self) -> bool:
    """
    Inicia el monitor.

    Returns:
        True si se inició correctamente
    """
    pass
```

## 🐛 Troubleshooting

### Importación circular

- Verificar que no haya imports cruzados entre módulos
- Usar inyección de dependencias

### Thread no se detiene

- Verificar que `stop_event.set()` sea llamado
- Comprobar que `.join(timeout=X)` sea invocado

### Micrófono no captura

- Verificar `DEVICE_INDEX` en .env
- Ejecutar: `python -m sounddevice` para listar dispositivos

## 📚 Referencias

- [SCREAM Architecture Pattern](SCREAM_ARCHITECTURE.md)
- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection)

## 🎯 Roadmap

### ✅ Completado (v0.1)

- [x] Estructura SCREAM
- [x] Entities (modelos puros)
- [x] Repositories (acceso a datos)
- [x] Services (lógica de negocio - threads)
- [x] Controllers (orquestación)
- [x] Application (casos de uso)
- [x] Presentation (CLI)
- [x] Documentación completa

### ⏳ Próximo (v0.2)

- [ ] Completar implementación de servicios
- [ ] Inyectar STT Manager
- [ ] Inyectar Gemini Engine
- [ ] Test suite completo
- [ ] CI/CD pipeline

### 🔮 Futuro (v1.0)

- [ ] Web UI (Flask/FastAPI)
- [ ] REST API
- [ ] Mobile App (Kivy)
- [ ] Database (SQLite/PostgreSQL)
- [ ] Clustering/Load Balancing

## 📞 Soporte

Para preguntas o problemas:

1. Revisar documentación (especialmente SCREAM_VISUAL.md)
2. Revisar docstrings en código
3. Abrir issue en repositorio

## 👥 Contribuyentes

- Team Jeepy AI

## 📜 License

[Tu licencia]

---

**¡Bienvenido a Jeepy AI - Voice Control for Your Jeep! 🎤🚙**

Última actualización: December 3, 2025
