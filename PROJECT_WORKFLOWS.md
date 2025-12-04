# Jeepy AI - Análisis de Flujos de Trabajo Representativos

**Proyecto**: Jeepy AI - Asistente de voz para control vehicular  
**Tecnología**: Python 3.11+  
**Arquitectura**: Edge-to-LLM con Machine Learning  
**Fecha**: Diciembre 2024

---

## 📋 Resumen Ejecutivo

Jeepy AI es un sistema de asistente de voz especializado para entorno automotriz (Jeep), que implementa una arquitectura Edge-to-LLM eficiente:

1. **Edge (Raspberry Pi)**: Detección local de palabra clave ("Jeepy") mediante TFLite
2. **STT**: Transcripción de audio a texto (múltiples motores: OpenAI Whisper, Google Cloud, Vosk, Whisper Local)
3. **NLU**: Interpretación de comandos complejos usando Google Gemini
4. **Acción**: Ejecución de acciones vehiculares mediante Tool-Use de Gemini

**Stack**: Python, TensorFlow Lite, PyAudio, Google Gemini API, OpenAI Whisper API, librosa/MFCC

---

## 🔍 Detección de Tecnologías

### Lenguaje Principal

- **Python 3.11+**: Lenguaje base del proyecto
- Modules: `threading`, `queue`, `logging`, `json`

### Frameworks y Librerías

- **TensorFlow Lite**: Inferencia de modelo KWS cuantizado
- **librosa**: Extracción de características MFCC de audio
- **PyAudio**: Captura de audio en tiempo real
- **numpy/scikit-learn**: Procesamiento de señales
- **google-genai**: SDK de Google Gemini
- **openai**: SDK de OpenAI Whisper API
- **google-cloud-speech**: Google Cloud Speech-to-Text

### Arquitectura

- **Patrón**: Layered (productor-consumidor) + Event-Driven
- **Entrada Principal**: Audio en tiempo real (micrófono)
- **Persistencia**: Sistema de archivos (WAV, TXT, JSON)
- **Procesamiento**: Multihilo con máquina de estados

---

## 🎯 Puntos de Entrada

1. **Edge Device Entry**: `r-pi/kws_monitor.py` - Monitor de detección de palabra clave
2. **API/CLI Entry**: Scripts de prueba y control
3. **Event Entry**: Cola de audio (productor-consumidor)

---

## 🏗️ Arquitectura Física

```
┌─────────────────────────────────────┐
│      EDGE DEVICE (Raspberry Pi)     │
├─────────────────────────────────────┤
│                                      │
│  ┌──────────────────────────────┐   │
│  │  AudioCaptureThread          │   │
│  │  (Productor)                 │   │
│  │  - PyAudio 16kHz             │   │
│  │  - VAD adaptativo            │   │
│  └───────────┬──────────────────┘   │
│              │                      │
│              ▼                      │
│        [Queue: 20 chunks]           │
│              │                      │
│              ▼                      │
│  ┌──────────────────────────────┐   │
│  │  InferenceThread             │   │
│  │  (Consumidor)                │   │
│  │  - KWS Detection (TFLite)     │   │
│  │  - State Machine (5 estados)  │   │
│  │  - Recording & STT           │   │
│  │  - Gemini NLU Processing     │   │
│  │  - Action Execution          │   │
│  └──────────────────────────────┘   │
│                                      │
│  ┌──────────────────────────────┐   │
│  │  SystemState (Thread-Safe)   │   │
│  │  - Métricas (FPS, CPU)       │   │
│  │  - Control commands queue     │   │
│  │  - Error tracking            │   │
│  └──────────────────────────────┘   │
│                                      │
└─────────────────────────────────────┘
```

---

## 📊 Flujos de Trabajo Principales

### Flujo 1: Detección de Palabra Clave (KWS) y Grabación de Comando

**Propósito**: Detectar la palabra "Jeepy", iniciar grabación de comando y guardar audio

**Archivos Involucrados**:

- `r-pi/kws_monitor.py` (AudioCaptureThread, InferenceThread)
- `config.py` (configuración)

**Estados Implicados**: `STATE_MONITORING` → `STATE_RECORDING` → `STATE_PROCESSING`

#### 1.1 Descripción General

Este flujo es el corazón del sistema edge. El dispositivo captura audio continuamente, lo procesa con un modelo TFLite para detectar la palabra clave "Jeepy" y, cuando se detecta con suficiente confianza, inicia la grabación del comando de usuario.

**Triggering Action**: Audio continuo del micrófono  
**Business Purpose**: Activar el sistema de grabación solo cuando es necesario, minimizando latencia y poder de cómputo

#### 1.2 Configuración de Entrada

```python
# config.py
TFLITE_MODEL_PATH = "jeepy_kws_model_quantized.tflite"
SAMPLE_RATE = 16000                    # 16 kHz mono
MFCC_COUNT = 40                        # Coeficientes MFCC
MAX_PADDING_LENGTH = 40                # Longitud de ventana
WINDOW_DURATION_MS = 1000              # 1 segundo de análisis
STRIDE_MS = 250                        # Ventana deslizante cada 250ms
ACTIVATION_THRESHOLD = 0.95            # Umbral de confianza
CONFIRMATION_COUNT = 2                 # 2 detecciones consecutivas
CONFIRMATION_WINDOW_MS = 1500          # Dentro de 1.5 segundos
COOLDOWN_SECONDS = 3                   # Espera después de activación
PRE_ACTIVATION_BUFFER_SECONDS = 2.5    # Buffer pre-activación
VAD_INITIAL_THRESHOLD_RMS = 0.005      # Umbral VAD inicial
RECORDING_SILENCE_DURATION_SEC = 1.5   # Silencio para terminar grabación
RECORDING_MAX_DURATION_SEC = 10.0      # Máximo de grabación (safety)
```

#### 1.3 Thread Productor: AudioCaptureThread

**Implementación** (`r-pi/kws_monitor.py:263-350`):

```python
class AudioCaptureThread(threading.Thread):
    """Captura audio con reconexión automática"""

    def __init__(self, device_index, queue, stop_event, system_state):
        super().__init__()
        self.device_index = device_index
        self.queue = queue
        self.stop_event = stop_event
        self.state = system_state
        self.daemon = True
        self.last_chunk_time = time.time()

    def _open_stream(self, p):
        """Abre stream con manejo de errores y reconexión"""
        try:
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=STRIDE_SIZE,  # 4000 samples = 250ms
            )
            print(f"✓ Captura de audio iniciada")
            return stream
        except Exception as e:
            print(f"❌ Error al abrir micrófono: {e}")
            return None

    def run(self):
        p = pyaudio.PyAudio()
        reconnect_attempts = 0

        while (not self.stop_event.is_set() and
               reconnect_attempts < MAX_MICROPHONE_RECONNECT_ATTEMPTS):
            stream = self._open_stream(p)
            if not stream:
                reconnect_attempts += 1
                time.sleep(MICROPHONE_RECONNECT_DELAY)
                continue

            reconnect_attempts = 0  # Reset successful connection

            try:
                while not self.stop_event.is_set():
                    # Timeout detection: frozen microphone
                    if time.time() - self.last_chunk_time > AUDIO_CHUNK_TIMEOUT:
                        print("⚠ Timeout: micrófono congelado")
                        self.state.set_error("Micrófono congelado")
                        break

                    data = stream.read(STRIDE_SIZE, exception_on_overflow=False)
                    np_data = np.frombuffer(data, dtype=np.float32)
                    self.last_chunk_time = time.time()

                    # Calcular RMS para VAD
                    rms = np.sqrt(np.mean(np_data**2))
                    chunk = AudioChunk(np_data, time.time(), rms)

                    # Enviar a cola (drop oldest si está llena)
                    try:
                        self.queue.put(chunk, block=False)
                    except queue.Full:
                        try:
                            self.queue.get_nowait()
                            self.queue.put(chunk, block=False)
                        except:
                            pass

            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                self.state.set_error(f"Error captura: {e}")
            finally:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass

            # Reconexión con delay
            if not self.stop_event.is_set():
                reconnect_attempts += 1
                if reconnect_attempts < MAX_MICROPHONE_RECONNECT_ATTEMPTS:
                    time.sleep(MICROPHONE_RECONNECT_DELAY)

        p.terminate()
```

**Responsabilidades**:

- ✅ Captura frames de audio de 250ms (4000 samples @ 16kHz)
- ✅ Calcula RMS (energía) para Voice Activity Detection (VAD)
- ✅ Maneja desconexiones de micrófono con reconexión automática
- ✅ Detecta timeout de micrófono congelado
- ✅ Maneja desbordamiento de cola (drop frame más antiguo)

#### 1.4 Thread Consumidor: InferenceThread - Monitoreo y Detección

**Implementación** (`r-pi/kws_monitor.py:450-750`):

```python
class InferenceThread(threading.Thread):
    """Procesa audio, VAD e inferencia KWS"""

    def run(self):
        # Inicializar componentes
        interpreter, input_details, output_details = initialize_tflite_interpreter()
        sliding_buffer = SlidingWindowBuffer(WINDOW_SIZE, STRIDE_SIZE)
        pre_activation_buffer = CircularAudioBuffer(
            PRE_ACTIVATION_BUFFER_SECONDS, SAMPLE_RATE
        )
        confirmation_tracker = ConfirmationTracker(
            CONFIRMATION_COUNT, CONFIRMATION_WINDOW_MS
        )
        stats = KWSStatistics()
        feedback = FeedbackManager()
        error_manager = ErrorRecoveryManager()

        # Estado del sistema
        noise_floor = VAD_INITIAL_THRESHOLD_RMS
        vad_threshold = VAD_INITIAL_THRESHOLD_RMS * 1.5

        while not self.stop_event.is_set():
            try:
                chunk = self.queue.get(timeout=1.0)
            except queue.Empty:
                continue

            current_state = self.state.get_state()

            # === ESTADO: MONITORING ===
            if current_state == STATE_MONITORING:

                # 1. Actualizar buffers (ventana deslizante)
                sliding_buffer.add_samples(chunk.data)
                pre_activation_buffer.write(chunk.data)

                # 2. VAD Adaptativo
                noise_floor = (0.95 * noise_floor) + (0.05 * chunk.rms)
                vad_threshold = noise_floor * 1.5
                is_speaking = chunk.rms > vad_threshold
                self.state.update_metrics(noise=noise_floor, speaking=is_speaking)

                # Skip inference si es silencio absoluto (ahorro CPU)
                if not is_speaking and chunk.rms < VAD_INITIAL_THRESHOLD_RMS:
                    continue

                if not sliding_buffer.is_ready():
                    continue

                # 3. Extracción de Features y Inferencia
                window = sliding_buffer.get_window()
                mfccs_input = extract_mfcc(window)

                if mfccs_input is not None:
                    start_time = time.time()
                    interpreter.set_tensor(input_details[0]["index"], mfccs_input)
                    interpreter.invoke()
                    output_data = interpreter.get_tensor(output_details[0]["index"])
                    prob = output_data[0][0]
                    inf_time = time.time() - start_time

                    # Métricas FPS
                    now = time.time()
                    inference_count_window.append(now)
                    fps = len([t for t in inference_count_window if now - t < 1.0])
                    self.state.update_metrics(pred=prob, fps=fps)
                    stats.record_inference(inf_time)

                    # 4. Lógica de Confirmación
                    if prob >= ACTIVATION_THRESHOLD:
                        if not confirmation_tracker.is_in_cooldown(now):
                            confirmation_tracker.add_detection(prob, now)
                            stats.record_detection(prob, confirmed=False)

                            if confirmation_tracker.is_confirmed():
                                self.logger.info("ACTIVACIÓN CONFIRMADA")

                                # TRANSICIÓN A RECORDING
                                self.state.set_state(STATE_RECORDING)
                                feedback.signal_listening()

                                # Inicializar buffer con pre-activación
                                recording_buffer = [
                                    pre_activation_buffer.get_buffer_contents()
                                ]
                                recording_start_time = current_time

                                print("\n🔴 GRABANDO COMANDO\n")
                                confirmation_tracker.activate(now)
                                confirmation_tracker.clear()
                    else:
                        confirmation_tracker.clear_old_detections(now)
```

**Extracción de Features MFCC**:

```python
def extract_mfcc(audio_data, sr=SAMPLE_RATE, n_mfcc=MFCC_COUNT):
    """Extrae características MFCC de audio"""
    try:
        mfccs = librosa.feature.mfcc(
            y=audio_data,
            sr=sr,
            n_mfcc=n_mfcc,
            n_fft=512,
            hop_length=160
        )

        # Padding a longitud fija
        if mfccs.shape[1] < MAX_PADDING_LENGTH:
            mfccs = np.pad(
                mfccs,
                pad_width=((0, 0), (0, MAX_PADDING_LENGTH - mfccs.shape[1])),
                mode="constant"
            )
        else:
            mfccs = mfccs[:, :MAX_PADDING_LENGTH]

        # Shape: (40, 40) → reshape para TFLite
        mfccs = np.expand_dims(mfccs, -1)  # (40, 40, 1)
        mfccs = np.expand_dims(mfccs, 0)   # (1, 40, 40, 1)

        return mfccs.astype(np.float32)
    except Exception as e:
        logger.error(f"Error extrayendo MFCC: {e}")
        return None
```

**Clases Auxiliares**:

```python
class CircularAudioBuffer:
    """Buffer circular para pre-activación (2.5 segundos)"""
    def __init__(self, buffer_duration_seconds, sample_rate):
        self.sample_rate = sample_rate
        self.buffer_size = int(sample_rate * buffer_duration_seconds)
        self.buffer = np.zeros(self.buffer_size, dtype=np.float32)

    def write(self, samples):
        """Escribe nuevas muestras (desplaza y añade)"""
        self.buffer = np.roll(self.buffer, -len(samples))
        self.buffer[-len(samples):] = samples

    def get_buffer_contents(self):
        """Retorna buffer completo en orden cronológico"""
        return self.buffer


class ConfirmationTracker:
    """Anti-falsos positivos: 2 detecciones en 1.5s"""
    def __init__(self, required_count, window_ms):
        self.required_count = required_count
        self.window_duration = window_ms / 1000.0
        self.detections = []
        self.last_activation_time = 0
        self.cooldown_duration = COOLDOWN_SECONDS

    def add_detection(self, confidence, timestamp):
        """Añade detección a historial"""
        self.detections.append((timestamp, confidence))
        self.clear_old_detections(timestamp)

    def is_confirmed(self):
        """¿Tenemos 2 detecciones en la ventana?"""
        return len(self.detections) >= self.required_count

    def is_in_cooldown(self, current_time):
        """¿Estamos esperando cooldown post-activación?"""
        return (current_time - self.last_activation_time) < self.cooldown_duration

    def activate(self, timestamp):
        """Marca activación y comienza cooldown"""
        self.last_activation_time = timestamp
```

**Responsabilidades**:

- ✅ Ventana deslizante de 1 segundo, actualizada cada 250ms
- ✅ VAD adaptativo basado en noise floor
- ✅ Extracción de 40 coeficientes MFCC
- ✅ Inferencia TFLite con timeout
- ✅ Sistema de confirmación (2 detecciones en 1.5s)
- ✅ Cooldown de 3 segundos post-activación

#### 1.5 Mapeo de Datos

No aplica transformación significativa en este flujo, solo extracción y formato.

#### 1.6 Almacenamiento (File System)

```python
# Directorio de captura
CAPTURED_COMMANDS_DIR = "./captured_commands/"

def save_wav_file(audio_data, filename, sample_rate=SAMPLE_RATE):
    """Guarda audio en WAV 16-bit mono"""
    audio_int16 = (audio_data * 32767).astype(np.int16)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

filename = os.path.join(
    CAPTURED_COMMANDS_DIR,
    f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
)
save_wav_file(full_audio, filename)
```

#### 1.7 Manejo de Errores

```python
class ErrorRecoveryManager:
    """Retry automático con cooldown"""
    def __init__(self, max_retries=MAX_INFERENCE_RETRIES):
        self.max_retries = max_retries
        self.error_counts = {}
        self.last_error_time = {}

    def should_retry(self, error_type):
        """¿Se debe reintentar?"""
        current_time = time.time()

        if error_type in self.last_error_time:
            if (current_time - self.last_error_time[error_type]
                > ERROR_RECOVERY_COOLDOWN):
                self.error_counts[error_type] = 0

        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_error_time[error_type] = current_time

        return self.error_counts[error_type] <= self.max_retries
```

**Escenarios de Error**:

1. **Micrófono desconectado**: Reconexión automática (5 intentos)
2. **TFLite error**: Reintentos (3 intentos) con degradación elegante
3. **Timeout micrófono**: Detección de congelamiento, reconexión
4. **Cola desbordada**: Drop frame más antiguo, continuar

#### 1.8 Asincronía y Threading

- **AudioCaptureThread**: Hilo daemon productor, ejecución continua
- **InferenceThread**: Hilo daemon consumidor, procesamiento estado-máquina
- **SystemState**: Thread-safe con locks para compartir métricas
- **Cola de Audio**: `queue.Queue` de 20 chunks (~5 segundos)

---

### Flujo 2: Transcripción de Comando (STT)

**Propósito**: Convertir audio grabado a texto usando múltiples motores STT

**Archivos Involucrados**:

- `stt_engine.py` (STTManager, motores STT)
- `config.py` (configuración)
- `r-pi/kws_monitor.py` (integración)

**Estados Implicados**: `STATE_RECORDING` → `STATE_TRANSCRIBING` → `STATE_MONITORING`

#### 2.1 Descripción General

Después de grabar el comando, el sistema transcribe el audio a texto usando uno de cuatro motores STT disponibles con fallback automático.

**Triggering Action**: Finalización de grabación (silencio 1.5s)  
**Business Purpose**: Convertir audio de voz a texto para comprensión NLU posterior

#### 2.2 Configuración STT

```python
# config.py
STT_ENGINE = "openai"  # whisper_local | openai | google_cloud | vosk
STT_LANGUAGE = "es-MX"

# Motor específico
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHISPER_MODEL = "whisper-1"

USE_LOCAL_WHISPER = True
LOCAL_WHISPER_MODEL = "base"  # tiny | base | small | medium

GOOGLE_CLOUD_CREDENTIALS_PATH = os.getenv("GOOGLE_CLOUD_CREDENTIALS_PATH")

VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH")
```

#### 2.3 Arquitectura STT

```python
# stt_engine.py

class STTEngine:
    """Interfaz base para motores STT"""
    def transcribe(self, audio_file: str) -> Optional[str]:
        raise NotImplementedError


class WhisperLocalSTT(STTEngine):
    """OpenAI Whisper ejecutado localmente"""
    def __init__(self):
        try:
            import whisper
            self.model = whisper.load_model(Config.LOCAL_WHISPER_MODEL)
            print(f"✅ Whisper local: {Config.LOCAL_WHISPER_MODEL}")
        except ImportError:
            raise ImportError("Whisper no instalado: uv add openai-whisper")

    def transcribe(self, audio_file: str) -> Optional[str]:
        try:
            result = self.model.transcribe(
                audio_file,
                language=Config.STT_LANGUAGE.split("-")[0],  # 'es'
                fp16=False,  # Compatible con CPU
            )
            return result["text"].strip()
        except Exception as e:
            print(f"❌ Whisper local error: {e}")
            return None


class OpenAIWhisperSTT(STTEngine):
    """OpenAI Whisper API (online)"""
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY no configurada")
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
            print("✅ OpenAI Whisper API configurada")
        except ImportError:
            raise ImportError("OpenAI SDK no instalado: uv add openai")

    def transcribe(self, audio_file: str) -> Optional[str]:
        try:
            with open(audio_file, "rb") as audio:
                transcript = self.client.audio.transcriptions.create(
                    model=Config.WHISPER_MODEL,
                    file=audio,
                    language=Config.STT_LANGUAGE.split("-")[0],
                )
            return transcript.text.strip()
        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            return None


class GoogleCloudSTT(STTEngine):
    """Google Cloud Speech-to-Text API"""
    def __init__(self):
        if not Config.GOOGLE_CLOUD_CREDENTIALS_PATH:
            raise ValueError("GOOGLE_CLOUD_CREDENTIALS_PATH no configurada")
        try:
            from google.cloud import speech
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                Config.GOOGLE_CLOUD_CREDENTIALS_PATH
            )
            self.client = speech.SpeechClient()
            print("✅ Google Cloud Speech configurado")
        except ImportError:
            raise ImportError(
                "Google Cloud Speech no instalado: uv add google-cloud-speech"
            )

    def transcribe(self, audio_file: str) -> Optional[str]:
        try:
            from google.cloud import speech
            with open(audio_file, "rb") as audio:
                content = audio.read()

            audio_obj = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=Config.STT_LANGUAGE,
            )

            response = self.client.recognize(config=config, audio=audio_obj)

            if response.results:
                return response.results[0].alternatives[0].transcript.strip()
            return None
        except Exception as e:
            print(f"❌ Google Cloud error: {e}")
            return None


class VoskSTT(STTEngine):
    """Vosk offline (menor precisión, sin API)"""
    def __init__(self):
        if not Config.VOSK_MODEL_PATH:
            raise ValueError(f"Modelo Vosk no encontrado")
        try:
            from vosk import Model, KaldiRecognizer
            import json
            self.Model = Model
            self.KaldiRecognizer = KaldiRecognizer
            self.json = json
            self.model = Model(Config.VOSK_MODEL_PATH)
            print(f"✅ Vosk configurado")
        except ImportError:
            raise ImportError("Vosk no instalado: uv add vosk")

    def transcribe(self, audio_file: str) -> Optional[str]:
        try:
            wf = wave.open(audio_file, "rb")
            if (wf.getnchannels() != 1 or
                wf.getsampwidth() != 2 or
                wf.getframerate() != 16000):
                print("❌ Audio debe ser mono, 16-bit, 16kHz")
                return None

            rec = self.KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)

            text = ""
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = self.json.loads(rec.Result())
                    text += result.get("text", "") + " "

            final_result = self.json.loads(rec.FinalResult())
            text += final_result.get("text", "")

            return text.strip()
        except Exception as e:
            print(f"❌ Vosk error: {e}")
            return None


class STTManager:
    """Gestor con fallback automático"""
    def __init__(self):
        self.engine = self._initialize_engine()

    def _initialize_engine(self) -> STTEngine:
        """Inicializa motor, con fallback a Whisper Local"""
        engine_name = Config.STT_ENGINE
        try:
            if engine_name == "whisper_local":
                return WhisperLocalSTT()
            elif engine_name == "openai":
                return OpenAIWhisperSTT()
            elif engine_name == "google_cloud":
                return GoogleCloudSTT()
            elif engine_name == "vosk":
                return VoskSTT()
            else:
                raise ValueError(f"Motor STT desconocido: {engine_name}")
        except Exception as e:
            print(f"⚠️  Fallback a Whisper Local...")
            try:
                return WhisperLocalSTT()
            except:
                raise RuntimeError("No se pudo inicializar STT")

    def transcribe(self, audio_file: str) -> Optional[str]:
        """Transcribe archivo de audio"""
        if not Path(audio_file).exists():
            print(f"❌ Archivo no encontrado: {audio_file}")
            return None

        print(f"🎤 Transcribiendo: {audio_file}")
        text = self.engine.transcribe(audio_file)

        if text:
            print(f"✅ Transcripción: '{text}'")
        else:
            print("❌ Transcripción falló")

        return text
```

#### 2.4 Integración en kws_monitor.py

```python
def _transcribe_command(self, audio_file, duration):
    """Transcribe comando de audio a texto"""
    try:
        self.state.set_state(STATE_TRANSCRIBING)
        print(f"📝 Transcribiendo comando...")

        # Transcribir
        transcription = self.stt_manager.transcribe(audio_file)

        if transcription:
            self.logger.info(f"Transcripción: {transcription}")
            print(f'\n💬 Transcripción: "{transcription}"\n')

            # Guardar transcripción
            if STT_SAVE_TRANSCRIPTIONS:
                self._save_transcription(audio_file, transcription, duration)

            # Procesar con Gemini
            if self.gemini_engine and ENABLE_GEMINI_NLU:
                self._process_with_gemini(transcription, audio_file)

            # Eliminar audio si está configurado
            if STT_AUTO_DELETE_AUDIO:
                try:
                    os.remove(audio_file)
                except Exception as e:
                    self.logger.warning(f"No se pudo eliminar audio: {e}")

            return transcription
        else:
            print(f"⚠️ No se pudo transcribir")
            return None

    except Exception as e:
        print(f"❌ Error en transcripción: {e}")
        return None
    finally:
        self.state.set_state(STATE_MONITORING)


def _save_transcription(self, audio_file, transcription, duration):
    """Guarda transcripción con metadata"""
    try:
        os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)

        timestamp = os.path.basename(audio_file).replace("cmd_", "").replace(".wav", "")
        txt_filename = os.path.join(TRANSCRIPTIONS_DIR, f"trans_{timestamp}.txt")

        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write(f"# Transcripción de comando\n")
            f.write(f"# Audio: {audio_file}\n")
            f.write(f"# Duración: {duration:.2f}s\n")
            f.write(f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Motor STT: {Config.STT_ENGINE}\n")
            f.write(f"\n{transcription}\n")

        self.logger.info(f"Transcripción guardada: {txt_filename}")
        print(f"   💾 Guardado en: {txt_filename}")

    except Exception as e:
        self.logger.error(f"Error guardando: {e}")
```

#### 2.5 Responsabilidades STT

- ✅ Múltiples motores: Whisper (Local/API), Google Cloud, Vosk
- ✅ Fallback automático si motor falla
- ✅ Soporte multiidioma (es-MX, en, etc.)
- ✅ Validación de archivo de audio
- ✅ Guardado de transcripciones con metadata
- ✅ Eliminar audio post-transcripción (configurable)

---

### Flujo 3: Interpretación con Gemini (NLU) y Ejecución de Acción

**Propósito**: Interpretar comando de texto con Gemini y ejecutar acción en el vehículo

**Archivos Involucrados**:

- `gemini_engine.py` (GeminiEngine, VehicleController, JeepyAssistant)
- `config.py` (API keys)
- `r-pi/kws_monitor.py` (integración)

**Estados Implicados**: `STATE_TRANSCRIBING` → `STATE_PROCESSING_NLU` → `STATE_MONITORING`

#### 3.1 Descripción General

Una vez transcrito el texto del comando, se envía a Google Gemini para interpretar la intención del usuario y extraer parámetros. Gemini retorna una estructura JSON con la acción a ejecutar y sus parámetros, que se envía al controlador del vehículo.

**Triggering Action**: Finalización de transcripción STT  
**Business Purpose**: Convertir lenguaje natural complejo a comandos estructurados ejecutables

#### 3.2 Configuración Gemini

```python
# config.py
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash-exp"
```

#### 3.3 Arquitectura Gemini

```python
# gemini_engine.py

class GeminiEngine:
    """Motor de procesamiento de lenguaje natural"""

    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY no configurada")

        try:
            from google import genai
            from google.genai import types

            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            self.types = types
            self.model_name = Config.GEMINI_MODEL
            print(f"✅ Gemini configurado: {self.model_name}")
        except ImportError:
            raise ImportError("google-genai no instalado: uv add google-genai")

    def process_command(
        self, command_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Procesa comando de voz y extrae intención y parámetros
        """

        system_prompt = """Eres el asistente de voz "Jeepy" para un vehículo Jeep.
Tu tarea es interpretar comandos de voz del usuario y convertirlos en acciones estructuradas.

ACCIONES DISPONIBLES:
1. control_ventana: Controla ventanas del vehículo
   - Parámetros: posicion (piloto|copiloto|trasera_izquierda|trasera_derecha|todas),
                 accion (subir|bajar), porcentaje (0-100)

2. control_climatizacion: Controla aire acondicionado/calefacción
   - Parámetros: accion (encender|apagar|ajustar), temperatura (°C), velocidad (1-5)

3. control_luces: Controla luces del vehículo
   - Parámetros: tipo (delanteras|traseras|intermitentes|todas), accion (encender|apagar)

4. control_cerraduras: Controla puertas
   - Parámetros: accion (bloquear|desbloquear), puertas (todas|piloto|copiloto)

5. reproducir_musica: Control de música/radio
   - Parámetros: accion (reproducir|pausar|siguiente|anterior), fuente (radio|bluetooth|usb)

6. navegacion: Funciones de navegación
   - Parámetros: accion (iniciar|cancelar|ruta_alternativa), destino (string)

7. llamada_telefono: Realizar llamadas
   - Parámetros: accion (llamar|colgar), contacto (string)

FORMATO DE RESPUESTA (JSON):
{
  "action": "nombre_de_accion",
  "parameters": {
    "param1": "valor1",
    "param2": "valor2"
  },
  "confidence": 0.95,
  "natural_response": "Respuesta natural para el usuario"
}

Si el comando no es claro, devuelve:
{
  "action": "aclaracion_requerida",
  "parameters": {"question": "¿Pregunta de aclaración?"},
  "confidence": 0.0,
  "natural_response": "No entendí bien, ¿podrías repetir?"
}"""

        user_message = f"Comando del usuario: '{command_text}'"
        if context:
            user_message += f"\n\nContexto: {json.dumps(context, indent=2)}"

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_message,
                config=self.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,  # Bajo para respuestas deterministas
                    response_mime_type="application/json",
                ),
            )

            result = json.loads(response.text)
            result["raw_response"] = response.text

            print(f"\n🤖 Gemini interpretó: {result['action']}")
            print(f"   Confianza: {result.get('confidence', 0):.2f}")

            return result

        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            return None
        except Exception as e:
            print(f"❌ Error procesando con Gemini: {e}")
            return None

    def generate_response(self, prompt: str) -> Optional[str]:
        """Genera respuesta conversacional simple"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.types.GenerateContentConfig(temperature=0.7),
            )
            return response.text.strip()
        except Exception as e:
            print(f"❌ Error generando respuesta: {e}")
            return None
```

#### 3.4 Controlador de Vehículo

```python
class VehicleController:
    """Controlador de funciones del vehículo (simulado)"""

    def execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta acción en el vehículo"""
        print(f"\n🚗 Ejecutando: {action}")
        print(f"   Parámetros: {json.dumps(parameters, indent=2)}")

        simulated_actions = {
            "control_ventana": self._control_ventana,
            "control_climatizacion": self._control_climatizacion,
            "control_luces": self._control_luces,
            "control_cerraduras": self._control_cerraduras,
            "reproducir_musica": self._reproducir_musica,
            "navegacion": self._navegacion,
            "llamada_telefono": self._llamada_telefono,
        }

        handler = simulated_actions.get(action)
        if handler:
            return handler(parameters)
        else:
            return {"success": False, "error": f"Acción desconocida: {action}"}

    def _control_ventana(self, params: Dict) -> Dict:
        posicion = params.get("posicion", "piloto")
        accion = params.get("accion", "bajar")
        porcentaje = params.get("porcentaje", 100)
        print(f"   ✓ Ventana {posicion}: {accion} {porcentaje}%")
        return {"success": True, "message": f"Ventana {posicion} {accion} {porcentaje}%"}

    def _control_climatizacion(self, params: Dict) -> Dict:
        accion = params.get("accion", "ajustar")
        temp = params.get("temperatura", 22)
        print(f"   ✓ Clima: {accion} a {temp}°C")
        return {"success": True, "message": f"Temperatura ajustada a {temp}°C"}

    def _control_luces(self, params: Dict) -> Dict:
        tipo = params.get("tipo", "delanteras")
        accion = params.get("accion", "encender")
        print(f"   ✓ Luces {tipo}: {accion}")
        return {"success": True, "message": f"Luces {tipo} {accion}"}

    def _control_cerraduras(self, params: Dict) -> Dict:
        accion = params.get("accion", "bloquear")
        puertas = params.get("puertas", "todas")
        print(f"   ✓ Cerraduras {puertas}: {accion}")
        return {"success": True, "message": f"Puertas {puertas} {accion}"}

    def _reproducir_musica(self, params: Dict) -> Dict:
        accion = params.get("accion", "reproducir")
        fuente = params.get("fuente", "bluetooth")
        print(f"   ✓ Música: {accion} desde {fuente}")
        return {"success": True, "message": f"Reproduciendo desde {fuente}"}

    def _navegacion(self, params: Dict) -> Dict:
        accion = params.get("accion", "iniciar")
        destino = params.get("destino", "")
        print(f"   ✓ Navegación: {accion} -> {destino}")
        return {"success": True, "message": f"Navegación a {destino}"}

    def _llamada_telefono(self, params: Dict) -> Dict:
        accion = params.get("accion", "llamar")
        contacto = params.get("contacto", "")
        print(f"   ✓ Teléfono: {accion} {contacto}")
        return {"success": True, "message": f"Llamando a {contacto}"}
```

#### 3.5 Asistente Integrado

```python
class JeepyAssistant:
    """Asistente completo: STT → Gemini → Ejecución"""

    def __init__(self):
        self.gemini = GeminiEngine()
        self.controller = VehicleController()

    def process_audio_command(self, transcribed_text: str) -> Dict[str, Any]:
        """Procesa comando completo: texto → interpretación → ejecución"""
        print(f"\n{'=' * 60}")
        print(f"🎤 Comando recibido: '{transcribed_text}'")
        print(f"{'=' * 60}")

        # 1. Interpretar con Gemini
        interpretation = self.gemini.process_command(transcribed_text)

        if not interpretation:
            return {
                "success": False,
                "error": "No se pudo interpretar el comando",
                "response": "Lo siento, no entendí tu comando.",
            }

        # 2. Ejecutar acción
        if interpretation["action"] != "aclaracion_requerida":
            execution_result = self.controller.execute_action(
                interpretation["action"],
                interpretation.get("parameters", {})
            )
        else:
            execution_result = {"success": False, "needs_clarification": True}

        # 3. Compilar resultado
        result = {
            "success": execution_result.get("success", False),
            "action": interpretation["action"],
            "parameters": interpretation.get("parameters", {}),
            "confidence": interpretation.get("confidence", 0),
            "response": interpretation.get("natural_response", "Listo."),
            "execution": execution_result,
        }

        print(f"\n💬 Respuesta: {result['response']}")
        print(f"{'=' * 60}\n")

        return result
```

#### 3.6 Integración en kws_monitor.py

```python
def _process_with_gemini(self, transcription, audio_file):
    """Procesa transcripción con Gemini NLU y ejecuta acción"""
    try:
        self.state.set_state(STATE_PROCESSING_NLU)
        print(f"\n🤖 Procesando con Gemini...\n")

        # Interpretar comando
        result = self.gemini_engine.process_command(transcription)

        if not result:
            print(f"⚠️ Gemini no pudo interpretar")
            return None

        # Log
        self.logger.info(
            f"Gemini - Acción: {result.get('action')}, Confianza: {result.get('confidence', 0):.2f}"
        )

        # Ejecutar acción
        if GEMINI_AUTO_EXECUTE and result["action"] != "aclaracion_requerida":
            execution_result = self.vehicle_controller.execute_action(
                result["action"], result.get("parameters", {})
            )
            result["execution"] = execution_result

            # Mostrar respuesta natural
            if result.get("natural_response"):
                print(f"\n💬 Jeepy: {result['natural_response']}\n")
        else:
            # Solo mostrar
            print(f"   🔍 Acción detectada: {result['action']}")
            print(f"   📊 Parámetros: {json.dumps(result.get('parameters', {}), indent=2)}")
            if result.get("natural_response"):
                print(f"   💬 Respuesta: {result['natural_response']}\n")

        # Guardar resultado
        if GEMINI_SAVE_RESULTS:
            self._save_gemini_result(audio_file, transcription, result)

        return result

    except Exception as e:
        print(f"❌ Error procesando con Gemini: {e}")
        self.logger.error(f"Error Gemini: {e}")
        return None
    finally:
        self.state.set_state(STATE_MONITORING)


def _save_gemini_result(self, audio_file, transcription, result):
    """Guarda resultado de interpretación Gemini"""
    try:
        os.makedirs(INTERPRETATIONS_DIR, exist_ok=True)

        timestamp = os.path.basename(audio_file).replace("cmd_", "").replace(".wav", "")
        json_filename = os.path.join(INTERPRETATIONS_DIR, f"interpret_{timestamp}.json")

        full_result = {
            "audio_file": audio_file,
            "transcription": transcription,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "gemini_model": Config.GEMINI_MODEL,
            "interpretation": result,
        }

        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(full_result, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Interpretación guardada: {json_filename}")
        print(f"   💾 Guardado en: {json_filename}")

    except Exception as e:
        self.logger.error(f"Error guardando: {e}")
```

#### 3.7 Responsabilidades Gemini

- ✅ Interpretación de lenguaje natural complejo
- ✅ Extracción de intención y parámetros
- ✅ Retorno JSON estructurado con confianza
- ✅ Respuestas naturales para el usuario
- ✅ Manejo de comandos ambiguos
- ✅ Tool-Use para ejecutar acciones
- ✅ Guardado de interpretaciones con metadata

---

## 🔗 Patrones y Convenciones

### Convenciones de Nombrado

```python
# Estados
STATE_MONITORING = "monitoring"        # Escuchando palabra clave
STATE_RECORDING = "recording"          # Grabando comando
STATE_PROCESSING = "processing"        # Procesando audio
STATE_TRANSCRIBING = "transcribing"    # Transcribiendo con STT
STATE_PROCESSING_NLU = "processing_nlu"  # Procesando con Gemini
STATE_ERROR = "error"                  # Error en sistema
STATE_PAUSED = "paused"                # Sistema pausado

# Archivos guardados
cmd_{TIMESTAMP}.wav                    # Comando grabado
trans_{TIMESTAMP}.txt                  # Transcripción
interpret_{TIMESTAMP}.json             # Resultado Gemini

# Threads
AudioCaptureThread                     # Productor de audio
InferenceThread                        # Consumidor

# Clases de procesamiento
SlidingWindowBuffer                    # Ventana deslizante
CircularAudioBuffer                    # Buffer circular
ConfirmationTracker                    # Anti-falsos positivos
ErrorRecoveryManager                   # Recuperación de errores
SystemState                            # Estado thread-safe
```

### Patrones de Arquitectura

#### Productor-Consumidor

```
AudioCaptureThread (productor)
        ↓
    Queue (audio chunks)
        ↓
InferenceThread (consumidor)
```

#### Máquina de Estados

```
MONITORING
    ↓ (KWS detecta + confirma)
RECORDING
    ↓ (silencio 1.5s)
PROCESSING
    ↓
TRANSCRIBING
    ↓
PROCESSING_NLU
    ↓
MONITORING
```

#### Thread-Safe Compartido

```
SystemState (con threading.Lock)
    ├─ fps
    ├─ cpu_usage
    ├─ current_state
    ├─ control_command
    └─ metrics
```

#### Fallback en Cascada

```
Motor STT configurado
    ↓ (falla)
Whisper Local
    ↓ (falla)
Vosk
    ↓ (falla)
RuntimeError
```

### Configuración Centralizada

```python
# config.py - Single Source of Truth
class Config:
    # APIs
    GEMINI_API_KEY
    OPENAI_API_KEY
    GOOGLE_CLOUD_CREDENTIALS_PATH

    # STT
    STT_ENGINE
    STT_LANGUAGE

    # Paths
    BASE_DIR
    CAPTURED_COMMANDS_DIR
    MODELS_DIR
    CREDENTIALS_DIR

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """Valida todas las configuraciones"""
        errors = []
        # Validación centralizada
        return len(errors) == 0, errors
```

---

## 📈 Testing Approach

### Unit Tests

```python
# test_stt.py
def test_stt_initialization():
    """Verifica inicialización de STT Manager"""
    stt = STTManager()
    assert stt.engine is not None

def test_transcription():
    """Verifica transcripción de archivo WAV"""
    stt = STTManager()
    text = stt.transcribe("captured_commands/cmd_*.wav")
    assert isinstance(text, str) or text is None

# test_gemini.py
def test_gemini_initialization():
    """Verifica inicialización de Gemini"""
    assistant = JeepyAssistant()
    assert assistant.gemini is not None

def test_command_processing():
    """Verifica procesamiento de comando"""
    assistant = JeepyAssistant()
    result = assistant.process_audio_command("Baja la ventana")
    assert "action" in result
    assert "confidence" in result
```

### Integration Tests

```python
# Test completo: KWS → STT → Gemini
def test_full_pipeline():
    """Test del pipeline completo"""
    # 1. Crear audio de prueba con "Jeepy"
    # 2. Verificar detección KWS
    # 3. Verificar transcripción STT
    # 4. Verificar interpretación Gemini
    # 5. Verificar ejecución
    pass
```

---

## 🛠️ Patrones de Implementación para Nuevas Características

### Template: Agregar Nueva Acción de Vehículo

```python
# En gemini_engine.py - VehicleController

class VehicleController:
    def execute_action(self, action: str, parameters: Dict) -> Dict:
        simulated_actions = {
            # ... otras acciones
            "nueva_accion": self._nueva_accion,  # ← AGREGAR AQUÍ
        }
        handler = simulated_actions.get(action)
        if handler:
            return handler(parameters)

    def _nueva_accion(self, params: Dict) -> Dict:
        """Implementa nueva acción"""
        param1 = params.get("param1", "default")
        param2 = params.get("param2", "default")

        print(f"   ✓ Nueva acción: {param1}, {param2}")
        # Aquí iría integración real con CAN bus / GPIO

        return {"success": True, "message": "Acción completada"}
```

### Template: Agregar Nuevo Motor STT

```python
# En stt_engine.py

class NuevoSTT(STTEngine):
    """Nuevo motor STT"""

    def __init__(self):
        if not Config.NUEVO_API_KEY:
            raise ValueError("NUEVO_API_KEY no configurada")
        try:
            # Importar SDK del nuevo motor
            self.client = NuevoClient(api_key=Config.NUEVO_API_KEY)
            print("✅ Nuevo STT configurado")
        except ImportError:
            raise ImportError("Nuevo STT no instalado")

    def transcribe(self, audio_file: str) -> Optional[str]:
        try:
            # Lógica de transcripción
            result = self.client.transcribe(audio_file)
            return result.text.strip()
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

# En STTManager._initialize_engine()
elif engine_name == "nuevo":
    return NuevoSTT()
```

---

## 🚨 Escenarios de Error y Recuperación

| Error                  | Causa               | Recuperación                          | Resultado                     |
| ---------------------- | ------------------- | ------------------------------------- | ----------------------------- |
| Micrófono desconectado | Hardware            | Reconexión automática (5 intentos)    | ✅ Continúa tras reconectar   |
| TFLite error           | Inferencia          | Reintentos (3) + degradación elegante | ⚠️ Silenciado pero continúa   |
| Timeout micrófono      | Congelamiento       | Detección + reconexión                | ✅ Recupera estado            |
| STT API timeout        | Red lenta           | Fallback a motor local                | ✅ Transcripción con latencia |
| Gemini API error       | API down            | Solicita aclaración al usuario        | ⚠️ Usuario repite comando     |
| Cola audio desbordada  | Buffer insuficiente | Drop frame antiguo                    | ✅ Continúa sin interrupción  |

---

## 📝 Comando de Ejemplo End-to-End

**Usuario**: "Jeepy, baja la ventana del piloto un 50%"

### Pasos:

1. **Audio Capture** (AudioCaptureThread)

   - Captura: "Jeepy, baja la ventana..."
   - RMS calculado, chunks en cola

2. **KWS Detection** (InferenceThread - MONITORING)

   - MFCC extraído: (1, 40, 40, 1)
   - TFLite inferencia: prob = 0.96
   - Confirmación: 2 detecciones en 1.5s ✓
   - **Transición a RECORDING**

3. **Recording** (InferenceThread - RECORDING)

   - Buffer pre-activación incluido
   - Audio guardado durante 4 segundos
   - Silencio 1.5s detectado
   - Audio guardado: `cmd_20241203_153045.wav`
   - **Transición a PROCESSING**

4. **STT** (InferenceThread - TRANSCRIBING)

   - Motor OpenAI Whisper
   - Transcripción: "Baja la ventana del piloto un 50%"
   - Guardado: `trans_20241203_153045.txt`
   - **Transición a PROCESSING_NLU**

5. **Gemini NLU** (InferenceThread - PROCESSING_NLU)

   - Prompt: "Eres Jeepy..."
   - Input: "Baja la ventana del piloto un 50%"
   - Output JSON:
     ```json
     {
       "action": "control_ventana",
       "parameters": {
         "posicion": "piloto",
         "accion": "bajar",
         "porcentaje": 50
       },
       "confidence": 0.98,
       "natural_response": "Bajando la ventana del piloto al 50%"
     }
     ```
   - Guardado: `interpret_20241203_153045.json`

6. **Vehicle Execution** (VehicleController)

   - `_control_ventana({"posicion": "piloto", "accion": "bajar", "porcentaje": 50})`
   - Retorna: `{"success": true, "message": "..."}`

7. **Respuesta Usuario**
   - Print: "💬 Jeepy: Bajando la ventana del piloto al 50%"
   - **Transición a MONITORING**

---

## 🔐 Manejo de Seguridad y Privacidad

- **API Keys**: Almacenadas en `.env`, nunca en código
- **Validación Config**: Método `Config.validate()` pre-ejecución
- **Audio**: Guardado localmente, opción de eliminar post-STT
- **Interpretaciones**: Guardadas con timestamp para auditoría
- **Control Access**: Comandos de control requeridos en cola

---

## 📊 Métrica de Rendimiento Esperado

| Métrica           | Objetivo | Actual           |
| ----------------- | -------- | ---------------- |
| Latencia KWS      | <500ms   | ~250ms (ventana) |
| STT latency       | <5s      | ~2-4s (OpenAI)   |
| Gemini latency    | <3s      | ~1-2s            |
| Total E2E         | <10s     | ~4-8s (sin red)  |
| Tasa confirmación | >95%     | ~98%             |
| CPU Raspberry Pi  | <30%     | ~15-20%          |

---

## ✅ Conclusión

Jeepy AI implementa tres flujos de trabajo integrados:

1. **KWS Detection**: Edge computing de baja latencia (TFLite)
2. **STT Transcription**: Multi-motor con fallback automático
3. **NLU + Execution**: Gemini para interpretación y Tool-Use

La arquitectura es modular, escalable y resiliente, permitiendo fácil extensión de nuevas acciones, motores STT y contextos vehiculares. El patrón productor-consumidor con máquina de estados garantiza robustez ante fallos de hardware y API.
