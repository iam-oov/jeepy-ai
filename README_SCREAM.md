# Jeepy AI - SCREAM Architecture

Sistema de reconocimiento de voz para control vehicular, basado en arquitectura **SCREAM** (Screen, Controller, Repository, Entity, Application, Service/Model).

## 🏗️ Arquitectura

```
jeepy_ai/
├── presentation/cli/        # 🎨 Interfaz de usuario (CLI)
├── controllers/             # 🎮 Orquestación de servicios
├── application/usecases/    # 📋 Casos de uso (business logic)
├── services/                # ⚙️ Servicios (audio, KWS, procesamiento)
├── repositories/            # 💾 Acceso a datos
└── entities/                # 📦 Modelos de dominio
```

## 🚀 Quick Start

### Instalación

```bash
# Configurar entorno Python
python -m venv venv
source venv/bin/activate

# Instalar dependencias
uv install
# o
pip install -r requirements.txt
```

### Configuración

```bash
# Copiar template de configuración
cp .env.example .env

# Editar .env con tus credenciales
GEMINI_API_KEY=tu_api_key_aquí
OPENAI_API_KEY=tu_api_key_aquí
```

### Ejecución

```bash
# Ejecutar monitor
python -m jeepy_ai.main

# O directamente
python jeepy_ai/main.py
```

## 📚 Estructura de Carpetas

### `entities/` - Modelos de Dominio

Objetos puros sin dependencias externas:

- `system_state.py` - Estado del sistema (thread-safe)
- `audio_chunk.py` - Fragmento de audio
- `error_recovery.py` - Gestión de reintentos
- `command.py` - Registro de comando grabado

### `repositories/` - Acceso a Datos

Abstracción para persistencia:

- `audio_repository.py` - Gestión de archivos WAV
- `command_repository.py` - Historial de comandos (JSON)
- `config_repository.py` - Configuración (env + JSON)

### `services/` - Lógica de Negocio

Threads que implementan funcionalidad:

- `audio_capture_service.py` - Captura continua de audio
- `kws_inference_service.py` - Detección de palabra clave
- `command_processor_service.py` - Procesamiento STT/NLU

### `controllers/` - Orquestación

Coordinación de servicios:

- `monitor_controller.py` - Inicializa y coordina servicios

### `application/` - Casos de Uso

Lógica de la aplicación:

- `usecases/start_monitoring_usecase.py` - Iniciar monitoreo
- `usecases/stop_monitoring_usecase.py` - Detener monitoreo
- `usecases/get_system_status_usecase.py` - Obtener estado

### `presentation/` - Interfaz de Usuario

Interacción con usuario:

- `cli/cli_presentation.py` - Interfaz de línea de comandos

## 🔄 Flujo de Datos

```
┌──────────────────────┐
│  User Input (CLI)    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Application Layer (Use Cases)       │ StartMonitoringUseCase
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Controller Layer (Orchestration)    │ MonitorController.start()
└──────────┬───────────────────────────┘
           │
           ├─────────────────────────────────────────┐
           │                                         │
           ▼                                         ▼
    ┌────────────────┐              ┌──────────────────────┐
    │ AudioCapture   │              │ KWSInference         │
    │ Service        │              │ Service              │
    │ (Thread)       │              │ (Thread)             │
    └────────┬───────┘              └──────────┬───────────┘
             │ Produce                         │ Consume
             └────► audio_queue ────────────────┘
                        │ 25ms chunks
                        │
                        ├─ Detect KWS?
                        │   YES ─────────┐
                        │                │
                        │                ▼
                        │         ┌──────────────────────┐
                        │         │ CommandProcessor     │
                        │         │ Service (Thread)     │
                        │         │ • STT Transcribe     │
                        │         │ • Gemini NLU         │
                        │         │ • Execute Action     │
                        │         └──────────┬───────────┘
                        │                    │
                        │                    ▼
                        │          ┌──────────────────────┐
                        │          │ Repositories:        │
                        │          │ • Save Transcription │
                        │          │ • Save Result JSON   │
                        │          │ • Load Config        │
                        │          └──────────────────────┘
                        │
           ┌────────────┴─────────────┐
           │                          │
    Repository Access          External APIs
    • Archivos WAV            • Whisper (STT)
    • JSON results            • Gemini (NLU)
    • Config files            • GPIO Control
```

## 🧵 Threading Model

```
Main Thread (CLI Loop)
├─ Reads input
├─ Calls MonitorController
└─ Updates UI

AudioCaptureService (Producer Thread)
├─ Captura audio 24/7
├─ Produce: audio_queue (20 chunks LIFO)
└─ Reconnect automático si falla micrófono

KWSInferenceService (Consumer Thread)
├─ Procesa audio en tiempo real
├─ Detección de palabra clave
├─ Consume: audio_queue
├─ Produce: processing_queue
└─ No bloquea captura de audio

CommandProcessorService (Worker Thread)
├─ Transcripción (STT)
├─ Interpretación (Gemini NLU)
├─ Ejecución de acciones
├─ Consume: processing_queue
├─ Guarda: Transcripciones + Resultados
└─ Libre de tiempo real
```

## 📊 Cambios de Estados

```
MONITORING ──[KWS Detected]──> RECORDING ──[Silence/Timeout]──> PROCESSING
   ▲                                                                  │
   │                                                                  ▼
   └──────────────────────────────────────────────────────── MONITORING
                          STT ──> TRANSCRIBING
                                      │
                                      ▼
                              PROCESSING_NLU ──[Gemini]
                                      │
                                      ▼
                                    ACTION
```

## 🔧 Configuración

Variables de entorno (`.env`):

```bash
# API Keys
GEMINI_API_KEY=sk-...
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Audio
DEVICE_INDEX=0                   # Índice de dispositivo de audio
SAMPLE_RATE=16000               # Hz

# KWS Model
KWS_MODEL_PATH=./models/jeepy_model.tflite
KWS_THRESHOLD=0.7

# STT
STT_ENGINE=whisper_api          # whisper_api, whisper_local, google_cloud, vosk
STT_SAVE_TRANSCRIPTIONS=true
STT_AUTO_DELETE_AUDIO=true

# Output
TRANSCRIPTIONS_DIR=./transcriptions/
INTERPRETATIONS_DIR=./interpretations/
CAPTURED_COMMANDS_DIR=./captured_commands/
```

## 📝 Ejemplo de Uso

```python
from jeepy_ai.controllers import MonitorController
from jeepy_ai.repositories import ConfigRepository
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Crear configuración
config = ConfigRepository()
config.load_from_env()

# Crear controller
monitor = MonitorController(config=config)

# Iniciar monitoreo
monitor.start()

# ... sistema captando audio ...

# Detener
monitor.stop()

# Obtener estado
status = monitor.get_status()
print(f"Running: {status['is_running']}")
print(f"State: {status['state']}")
```

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Coverage
pytest --cov=jeepy_ai tests/
```

## 📦 Dependencias Principales

```
pyaudio==0.2.14              # Captura de audio
numpy>=1.21.0                # Computación numérica
librosa>=0.11.0              # Procesamiento de audio
tensorflow-lite              # Inferencia KWS (Linux/RPi solamente)
google-genai==1.53.0         # Gemini API
openai==2.8.1                # Whisper API
psutil                        # Monitoreo de sistema
```

## 📖 Documentación

- [`SCREAM_ARCHITECTURE.md`](SCREAM_ARCHITECTURE.md) - Arquitectura detallada
- [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md) - Guía de migración desde estructura anterior
- [`PROJECT_WORKFLOWS.md`](PROJECT_WORKFLOWS.md) - Flujos de trabajo (KWS, STT, NLU)
- [`PLATFORM_COMPATIBILITY.md`](PLATFORM_COMPATIBILITY.md) - Compatibilidad por plataforma

## 🚫 Archivos Legados

Archivos de la arquitectura anterior están en `_legacy/`:

- Para consultar lógica original
- **NO IMPORTAR** en nuevo código
- Se eliminarán después de implementación completa

## 🤝 Contribuir

1. Entender la [Arquitectura SCREAM](SCREAM_ARCHITECTURE.md)
2. Seguir convenciones de nombres
3. Escribir tests para nuevas features
4. Mantener separación de capas

## 📞 Soporte

Para preguntas sobre la arquitectura, referirse a:

- Docstrings en código
- `SCREAM_ARCHITECTURE.md`
- Issues en el repositorio

## 📜 License

[Tu licencia aquí]

---

**Jeepy AI - Voice Control for Your Jeep 🎤🚙**
