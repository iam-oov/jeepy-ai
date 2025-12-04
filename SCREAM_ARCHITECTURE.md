```markdown
# Arquitectura SCREAM - Jeepy AI

## Descripción General

**SCREAM** es una arquitectura limpia que organiza el código en capas bien definidas:

- **S**creen: Interfaz de usuario
- **C**ontroller: Orquestación de flujos
- **R**epository: Acceso a datos
- **E**ntity: Modelos de dominio puro
- **A**pplication: Casos de uso
- **M**odel/Service: Lógica de negocio

## Estructura del Proyecto
```

jeepy_ai/
├── **init**.py # Paquete raíz
├── main.py # Punto de entrada
│
├── presentation/ # 🎨 SCREEN LAYER
│ ├── **init**.py
│ └── cli/
│ ├── **init**.py
│ └── cli_presentation.py # Interfaz CLI (usuario ↔ aplicación)
│
├── controllers/ # 🎮 CONTROLLER LAYER
│ ├── **init**.py
│ └── monitor_controller.py # Orquestación de servicios
│
├── application/ # 📋 APPLICATION LAYER (Casos de Uso)
│ ├── **init**.py
│ └── usecases/
│ ├── **init**.py
│ ├── start_monitoring_usecase.py
│ ├── stop_monitoring_usecase.py
│ └── get_system_status_usecase.py
│
├── services/ # ⚙️ SERVICE LAYER (Lógica de Negocio)
│ ├── **init**.py
│ ├── audio_capture_service.py # Thread: Captura de audio
│ ├── kws_inference_service.py # Thread: Detección KWS
│ └── command_processor_service.py # Thread: Procesamiento STT/NLU
│
├── repositories/ # 💾 REPOSITORY LAYER (Acceso a Datos)
│ ├── **init**.py
│ ├── audio_repository.py # Gestión de archivos de audio
│ ├── command_repository.py # Gestión de historial de comandos
│ └── config_repository.py # Acceso a configuración
│
└── entities/ # 📦 ENTITY LAYER (Modelos Puros)
├── **init**.py
├── audio_chunk.py # Modelo: FragmentoAudio
├── system_state.py # Modelo: EstadoDelSistema
├── error_recovery.py # Modelo: RecuperaciónDeErrores
└── command.py # Modelo: ComandoGrabado

```

## Flujo de Datos (SCREAM)

```

┌─────────────────────────────────────────────────────────────────┐
│ USER INTERACTION │
└─────────────────────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────────┐
│ SCREEN (Presentation Layer) │
│ CLIPresentation: │
│ • run() → Loop principal │
│ • Muestra estado del sistema │
│ • Captura eventos (Ctrl+C) │
└─────────────────────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────────┐
│ APPLICATION (Use Cases Layer) │
│ StartMonitoringUseCase → execute() │
│ StopMonitoringUseCase → execute() │
│ GetSystemStatusUseCase → execute() │
└─────────────────────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────────┐
│ CONTROLLER (Orchestration Layer) │
│ MonitorController: │
│ • start() → Inicia servicios │
│ • stop() → Detiene servicios │
│ • get_status() → Estado del sistema │
└─────────────────────────────────────────────────────────────────┘
↓
┌─────────────────────┬─────────────────────┐
↓ ↓ ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ SERVICE 1 │ │ SERVICE 2 │ │ SERVICE 3 │
│ AudioCapture │ │ KWSInference │ │ CommandProc. │
│ (Thread) │ │ (Thread) │ │ (Thread) │
└──────────────┘ └──────────────┘ └──────────────┘
│ Produce │ Procesa │ Procesa
└─→ audio_queue │ Transcribe │ + Gemini NLU
(25ms chunks)│ + Encola │
└─→ processing_q │
└─→ Acción

                    ↓↓↓ DATOS ↓↓↓

            ┌─────────────────────────────┐
            │ ENTITY (Domain Models)      │
            │ • AudioChunk                │
            │ • SystemState               │
            │ • CommandRecord             │
            │ • ErrorRecoveryManager      │
            └─────────────────────────────┘
                       ↑↑↑ DATOS ↑↑↑

┌─────────────────────────────────────────────────────────────────┐
│ REPOSITORY (Data Access Layer) │
│ AudioRepository → Gestiona archivos WAV │
│ CommandRepository → Historial de comandos (JSON) │
│ ConfigRepository → Configuración (env + JSON) │
└─────────────────────────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────────┐
│ EXTERNAL SYSTEMS │
│ • FileSystem (WAV, JSON) │
│ • APIs (Whisper, Gemini) │
│ • Hardware (Micrófono, GPIO) │
└─────────────────────────────────────────────────────────────────┘

````

## Principios SCREAM en Jeepy AI

### 1. **Screen (Presentación)**
- **Responsabilidad**: Interfaz con el usuario
- **Componentes**: `CLIPresentation`
- **No sabe**: Lógica de negocio, detalles técnicos
- **Beneficio**: Fácil cambiar UI (Web, Android) sin tocar lógica

### 2. **Controller (Orquestación)**
- **Responsabilidad**: Coordinar servicios y flujos
- **Componentes**: `MonitorController`
- **No sabe**: Detalles de implementación de cada servicio
- **Beneficio**: Punto central de orquestación

### 3. **Repository (Acceso a Datos)**
- **Responsabilidad**: Abstraer acceso a datos externos
- **Componentes**: `AudioRepository`, `CommandRepository`, `ConfigRepository`
- **No sabe**: Cómo se usa la información, lógica de negocio
- **Beneficio**: Cambiar persistencia sin afectar servicios

### 4. **Entity (Modelos Puros)**
- **Responsabilidad**: Objetos de dominio sin dependencias
- **Componentes**: `AudioChunk`, `SystemState`, `CommandRecord`, `ErrorRecoveryManager`
- **No sabe**: Nada de capas superiores
- **Beneficio**: Reutilizable, testeable, independiente

### 5. **Application (Casos de Uso)**
- **Responsabilidad**: Orquestar use cases del usuario
- **Componentes**: `StartMonitoringUseCase`, `StopMonitoringUseCase`, `GetSystemStatusUseCase`
- **No sabe**: Cómo se usa (CLI, Web, API)
- **Beneficio**: Lógica de negocio independiente de UI

### 6. **Model/Service (Lógica de Negocio)**
- **Responsabilidad**: Implementar reglas de negocio
- **Componentes**: `AudioCaptureService`, `KWSInferenceService`, `CommandProcessorService`
- **No sabe**: Cómo se presenta la información
- **Beneficio**: Máximo testeable, reutilizable en múltiples contextos

## Ventajas de SCREAM en Jeepy AI

### ✅ Separación de Responsabilidades
- Cada capa tiene una única responsabilidad clara
- Cambios en una capa no afectan otras

### ✅ Testabilidad
- Cada componente puede ser testeado aisladamente
- Fácil crear mocks de dependencias

### ✅ Mantenibilidad
- Código organizado y fácil de entender
- Nuevos desarrolladores entienden rápidamente

### ✅ Escalabilidad
- Fácil agregar nuevas características
- Bajo acoplamiento entre componentes

### ✅ Reutilizabilidad
- Services pueden ser usados en múltiples contextos
- Entities son independientes de la implementación

### ✅ Independencia de Frameworks
- Cambiar librería de audio no afecta estructura
- Agregar nueva UI (Web, Android) es trivial

## Inyección de Dependencias

SCREAM promueve inyección de dependencias:

```python
# ❌ Acoplado (MAL)
class MonitorController:
    def __init__(self):
        self.audio_repo = AudioRepository()  # Hardcoded
        self.stt_engine = STTManager()       # Hardcoded

# ✅ Inyectado (BIEN)
class MonitorController:
    def __init__(self, audio_repo: AudioRepository, stt_engine: STTManager):
        self.audio_repo = audio_repo        # Inyectado
        self.stt_engine = stt_engine        # Inyectado
````

Beneficios:

- Fácil reemplazar implementaciones
- Testeable con mocks
- Flexible para diferentes configuraciones

## Threading en SCREAM

Services implementan threads de forma limpia:

```
┌─ AudioCaptureService (Thread)
│   └─ Produce: audio_queue
│
├─ KWSInferenceService (Thread)
│   ├─ Consume: audio_queue
│   ├─ Produce: processing_queue
│   └─ Usa: Entity, Repository
│
└─ CommandProcessorService (Thread)
    ├─ Consume: processing_queue
    ├─ Usa: Repository (Command, Audio)
    └─ Integra: STTManager, GeminiEngine
```

Cada thread:

- ✅ Responsabilidad clara
- ✅ Acceso thread-safe a Entity (SystemState)
- ✅ Comunicación por colas (thread-safe)
- ✅ Independiente del resto

## Extensión de SCREAM

### Agregar Nueva Capa de Presentación (Web)

```python
# jeepy_ai/presentation/web/web_presentation.py
from flask import Flask
from jeepy_ai.application.usecases import StartMonitoringUseCase

class WebPresentation:
    def __init__(self):
        self.app = Flask(__name__)
        self.controller = MonitorController()
        self.start_usecase = StartMonitoringUseCase(self.controller)

    @self.app.route('/monitor/start', methods=['POST'])
    def start_monitoring():
        success = self.start_usecase.execute()
        return {"success": success}
```

**Cambios necesarios**: 0 en lógica de negocio ✅

### Agregar Nuevo Repository

```python
# jeepy_ai/repositories/metrics_repository.py
class MetricsRepository:
    def save_metric(self, metric_name: str, value: float):
        # Guardar métrica en InfluxDB o Prometheus
        pass
```

**Cambios necesarios**: Solo agregar repository ✅

### Agregar Nuevo Service

```python
# jeepy_ai/services/metrics_service.py
class MetricsService(threading.Thread):
    def run(self):
        # Recolectar y guardar métricas cada X segundos
        pass
```

**Cambios necesarios**: Registrar en MonitorController ✅

## Comparación: Antes vs Después

### ❌ Antes (Monolito 1321 líneas)

```
kws_monitor.py (1321 líneas)
├── AudioCapture (100 líneas)
├── Inference (400 líneas)
├── Command Processor (300 líneas)
├── Utils (200 líneas)
├── main() (50 líneas)
└── TODO: Mezcla de todo
```

Problemas:

- Difícil entender flujo
- Imposible testear componentes
- Cambios afectan todo
- Nuevo dev necesita 1 semana para entender

### ✅ Después (SCREAM arquitectura)

```
jeepy_ai/
├── entities/          # Modelos puros
├── repositories/      # Acceso a datos
├── services/          # Lógica de negocio (threads)
├── controllers/       # Orquestación
├── application/       # Casos de uso
├── presentation/      # UI
└── main.py           # Entrada
```

Beneficios:

- Flujo crystal clear
- Cada componente testeado aisladamente
- Cambios localizados
- Nuevo dev entiende en 1 hora

## Testing en SCREAM

```python
# tests/unit/test_system_state.py
def test_system_state_thread_safe():
    state = SystemState()
    # Entity no tiene dependencias externas
    assert state.get_state() == "monitoring"

# tests/unit/test_audio_repository.py
def test_save_wav_file(tmp_path):
    repo = AudioRepository(base_path=str(tmp_path))
    repo.save_wav(np.array([0.1, 0.2, 0.3]))
    # Repository es testeable aisladamente

# tests/integration/test_monitor_controller.py
@patch('jeepy_ai.services.AudioCaptureService')
def test_monitor_controller_start(mock_audio_service):
    controller = MonitorController()
    controller.start()
    assert controller.is_running == True
    # Fácil crear mocks
```

## Conclusión

SCREAM proporciona a Jeepy AI:

1. **Claridad**: Cada capa tiene responsabilidad clara
2. **Mantenibilidad**: Código organizado y fácil de modificar
3. **Escalabilidad**: Agregar nuevas features es sencillo
4. **Testabilidad**: Componentes independientemente testeables
5. **Reusabilidad**: Servicios usables en múltiples contextos
6. **Profesionalismo**: Arquitectura robusta y probada

La migración de monolito a SCREAM es un paso hacia un codebase profesional, mantenible y escalable.

```

```
