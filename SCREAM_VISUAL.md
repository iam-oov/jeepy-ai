```
# Visual SCREAM Architecture - Jeepy AI

## Capas SCREAM - Vista General

                        🎬 SCREAM ARCHITECTURE 🎬

    ┌─────────────────────────────────────────────────────────┐
    │  🎨 SCREEN (Presentation Layer)                         │
    │  ┌─────────────────────────────────────────────────────┐│
    │  │ jeepy_ai/presentation/cli/cli_presentation.py       ││
    │  │ └─ CLIPresentation: Interfaz de usuario            ││
    │  │    • run(): Loop principal del programa             ││
    │  │    • print_welcome() / print_goodbye()              ││
    │  └─────────────────────────────────────────────────────┘│
    └─────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────┐
    │  📋 APPLICATION (Use Cases Layer)                       │
    │  ┌─────────────────────────────────────────────────────┐│
    │  │ jeepy_ai/application/usecases/                      ││
    │  │ • StartMonitoringUseCase: start()                   ││
    │  │ • StopMonitoringUseCase: stop()                     ││
    │  │ • GetSystemStatusUseCase: get_status()              ││
    │  └─────────────────────────────────────────────────────┘│
    │                                                          │
    │  🎮 CONTROLLER (Orchestration Layer)                    │
    │  ┌─────────────────────────────────────────────────────┐│
    │  │ jeepy_ai/controllers/monitor_controller.py          ││
    │  │ └─ MonitorController                                ││
    │  │    • start(): Inicializa servicios                  ││
    │  │    • stop(): Detiene servicios                      ││
    │  │    • get_status(): Retorna estado                   ││
    │  └─────────────────────────────────────────────────────┘│
    └─────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────┐
    │  ⚙️ SERVICE (Business Logic Layer - THREADS)            │
    │  ┌──────────────────┬──────────────────┬──────────────┐ │
    │  │ AudioCapture     │ KWSInference     │ CommandProc. │ │
    │  │ Service          │ Service          │ Service      │ │
    │  │ ┌──────────────┐ │ ┌──────────────┐│ ┌──────────┐  │ │
    │  │ │ Thread 1     │ │ │ Thread 2     ││ │Thread 3  │  │ │
    │  │ └──────────────┘ │ └──────────────┘│ └──────────┘  │ │
    │  │ • Captura audio │ │ • Procesa KWS │ │ • STT       │ │
    │  │ • Reconexión    │ │ • Grabación   │ │ • Gemini    │ │
    │  │ • VAD básico    │ │ • Encola cmds │ │ • Acción    │ │
    │  └──────────────────┴──────────────────┴──────────────┘ │
    │                                                          │
    │  Comunicación entre servicios:                          │
    │  Thread1 ─[audio_queue]─> Thread2 ─[proc_queue]─> T3   │
    │                                                          │
    └─────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────┐
    │  📦 ENTITY (Domain Models - Thread-Safe)                │
    │  ┌─────────────────────────────────────────────────────┐│
    │  │ jeepy_ai/entities/                                  ││
    │  │ • SystemState: Estado compartido (lock)             ││
    │  │ • AudioChunk: Fragmento de audio                    ││
    │  │ • CommandRecord: Comando grabado                    ││
    │  │ • ErrorRecoveryManager: Reintentos                  ││
    │  └─────────────────────────────────────────────────────┘│
    └─────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────┐
    │  💾 REPOSITORY (Data Access)                            │
    │  ┌────────────────┬──────────────────┬────────────────┐ │
    │  │ AudioRepository│CommandRepository │ConfigRepository│ │
    │  │ • save_wav()   │ • save_cmd()     │ • load_env()   │ │
    │  │ • load_wav()   │ • get_history()  │ • get_config() │ │
    │  │ • delete_audio()│ • save_result() │ • set_config() │ │
    │  └────────────────┴──────────────────┴────────────────┘ │
    └─────────────────────────────────────────────────────────┘
                              ↓
    ┌─────────────────────────────────────────────────────────┐
    │  🌍 EXTERNAL SYSTEMS                                    │
    │  • FileSystem (WAV, JSON, ENV)                          │
    │  • Audio Hardware (Micrófono, Speakers)                 │
    │  • APIs (Whisper, Gemini, GPIO)                         │
    │  • GPIO Control (LEDs, Relés)                           │
    └─────────────────────────────────────────────────────────┘


## Dependencias Entre Capas

Presentation Layer
    │
    ├─ usa ─> Application Layer (Use Cases)
    │
    └─ NUNCA usa ─┬─> Services
                 ├─> Repositories
                 └─> Entities (excepto a través de Controller)


Application Layer
    │
    ├─ usa ─> Controllers
    │
    └─ NUNCA usa ─┬─> Services (directamente)
                 ├─> Repositories (directamente)
                 └─> Entities (a través de Controller)


Controller Layer
    │
    ├─ usa ─> Services
    │         Repositories
    │         Entities
    │
    └─ NUNCA usa ─> Presentation
                    Application


Services Layer
    │
    ├─ usa ─> Entities
    │         Repositories
    │
    └─ NUNCA usa ─┬─> Controllers
                 ├─> Presentation
                 └─> Application


Repositories Layer
    │
    ├─ usa ─> Entities
    │
    └─ NUNCA usa ─┬─> Services
                 ├─> Controllers
                 ├─> Presentation
                 └─> Application


Entities Layer
    │
    ├─ NUNCA usa ─> Nada (módulos externos solo librería estándar)
    │
    └─ Principio: Pure Domain Objects


## Flujo de Ejecución

1. Usuario ejecuta: `python -m jeepy_ai.main`

2. main.py
   └─> CLIPresentation().__init__()
       └─> MonitorController().__init__()

3. CLIPresentation.run()
   └─> StartMonitoringUseCase.execute()
       └─> MonitorController.start()
           ├─> AudioCaptureService.start()      [Thread1 inicia]
           ├─> KWSInferenceService.start()      [Thread2 inicia]
           └─> CommandProcessorService.start()  [Thread3 inicia]

4. Loop Principal (Main Thread)
   ├─ Actualiza CPU/métricas (usando psutil)
   ├─ Muestra status en CLI
   ├─ Espera Ctrl+C
   └─ Si Ctrl+C: StopMonitoringUseCase.execute()

5. Threads Worker Concurrentes

   Thread1 (AudioCaptureService.run())
   ├─ while not stop:
   │  ├─ audio = microphone.read()
   │  ├─ chunk = AudioChunk(audio, timestamp, rms)
   │  └─ audio_queue.put(chunk) ──┐
   │                               │
   │                               ▼
   └─ [PRODUCE] audio_queue (maxsize=20, LIFO)

                                   │
                                   ▼
   Thread2 (KWSInferenceService.run())
   ├─ while not stop:
   │  ├─ chunk = audio_queue.get()
   │  ├─ si STATE_MONITORING:
   │  │  ├─ MFCC = librosa.feature.mfcc(chunk)
   │  │  ├─ predict = model.predict(MFCC)
   │  │  └─ if predict > threshold:
   │  │     └─ start_recording()
   │  │
   │  └─ si STATE_RECORDING:
   │     ├─ accumulate(chunk)
   │     └─ if silence_detected:
   │        └─ finish_recording()
   │           └─ processing_queue.put((file, dur)) ──┐
   │                                                   │
   └─ [CONSUME] audio_queue ◄──────────────────────   │
   [PRODUCE] processing_queue ─────────────────────────┤
                                                       │
                                                       ▼
   Thread3 (CommandProcessorService.run())
   ├─ while not stop:
   │  ├─ (file, dur) = processing_queue.get()
   │  ├─ transcription = whisper.transcribe(file)
   │  ├─ result = gemini.process(transcription)
   │  ├─ cmd_repo.save_transcription()
   │  └─ cmd_repo.save_gemini_result()
   │
   └─ [CONSUME] processing_queue ◄─────────────────

6. Graceful Shutdown (Ctrl+C)
   └─> stop_event.set()
       ├─ Thread1, Thread2, Thread3: detect stop_event
       ├─ Cierran streams/resources
       └─ .join(timeout=5s) espera finalización


## Estado del Sistema (Thread-Safe)

```

SystemState (Entity - shared entre threads)
├─ Atributos
│ ├─ fps: float [Actualizado por Thread2]
│ ├─ cpu_usage: float [Actualizado por Main]
│ ├─ last_prediction: float [Actualizado por Thread2]
│ ├─ is_speaking: bool [Actualizado por Thread2]
│ ├─ noise_level: float [Actualizado por Thread2]
│ ├─ current_state: str [Actualizado por Thread2/3]
│ ├─ last_error: str [Actualizado por cualquiera]
│ └─ lock: threading.Lock() [Protege acceso]
│
└─ Métodos Thread-Safe (CON lock)
├─ set_state(state: str)
├─ get_state() -> str
├─ set_error(error_msg: str)
├─ update_metrics(fps, cpu, noise, prediction)
└─ get_status_string() -> str

````

Ejemplo de acceso seguro:
```python
# Thread2
with system_state.lock:
    system_state.current_state = "recording"
    system_state.last_prediction = 0.95

# Main (acceso seguro automático)
status = system_state.get_status_string()
````

## Comunicación Entre Threads

```
┌────────────────────────┐
│  AudioCaptureService   │
│  (Productor)           │
└───────────┬────────────┘
            │ puts(AudioChunk)
            │ maxsize=20, LIFO
            │ (descarta más antiguos si lleno)
            ▼
       ┌─────────────┐
       │audio_queue  │◄─────┐
       └─────────────┘      │
            │               │
            │ gets()        │ receba & procesa
            ▼               │
┌──────────────────────────┐│
│ KWSInferenceService      ││
│ (Consumidor + Productor) ││
└──────────────┬───────────┘│
               │ puts(file, dur)
               │ maxsize=10, FIFO
               │
               ▼
        ┌─────────────┐
        │process_q    │
        └─────────────┘
             │
             │ gets()
             ▼
┌──────────────────────────┐
│ CommandProcessorService  │
│ (Consumidor)             │
└──────────────────────────┘
```

Características de Colas:

- audio_queue (LIFO): Descarta frames antiguos cuando está llena (OK para audio real-time)
- processing_queue (FIFO): Procesa en orden (importante para comandos)

## Integración de Dependencias Externas

Ejemplos de cómo inyectar STT y Gemini:

```python
# En MonitorController.__init__()
from src.stt_engine import STTManager
from src.gemini_engine import GeminiEngine, VehicleController

self.stt_manager = STTManager()          # Inyectar en Command
self.gemini_engine = GeminiEngine()      # Processor
self.vehicle_controller = VehicleController()

# En CommandProcessorService
def __init__(self, ..., stt_manager, gemini_engine):
    self.stt_manager = stt_manager
    self.gemini_engine = gemini_engine

def _transcribe_command(self):
    transcription = self.stt_manager.transcribe(audio_file)
    return transcription

def _process_with_gemini(self, transcription):
    result = self.gemini_engine.process_command(transcription)
    return result
```

## Resumen de Responsabilidades

| Capa         | Responsabilidad           | NO HACE                    |
| ------------ | ------------------------- | -------------------------- |
| Presentation | UI, mostrar info          | Lógica de negocio          |
| Application  | Orquestar use cases       | Detalles de implementación |
| Controller   | Coordinar servicios       | Lógica específica          |
| Services     | Implementar funcionalidad | Persistencia, UI           |
| Repositories | Acceso a datos            | Lógica de negocio          |
| Entities     | Objetos de dominio        | Acceso a datos, UI         |

```

```
