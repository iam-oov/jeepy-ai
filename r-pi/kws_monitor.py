import pyaudio
import numpy as np
import librosa
import time
import tensorflow as tf  # Usaremos tf.lite.Interpreter en lugar de tflite-runtime para simplicidad en el desarrollo
import logging
import json
from datetime import datetime
import os
import sys
import threading
import queue
import psutil

# Agregar directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports de módulos de integración
try:
    from config import Config
    from stt_engine import STTManager

    STT_ENABLED = True
    print("✅ Módulos STT cargados")
except ImportError as e:
    STT_ENABLED = False
    print(f"⚠️ STT no disponible: {e}")

try:
    from gemini_engine import GeminiEngine, VehicleController

    GEMINI_ENABLED = True
    print("✅ Módulos Gemini cargados")
except ImportError as e:
    GEMINI_ENABLED = False
    print(f"⚠️ Gemini no disponible: {e}")

if STT_ENABLED and GEMINI_ENABLED:
    print("🎉 Pipeline completo: KWS → STT → Gemini → Acción")
elif STT_ENABLED:
    print("ℹ️  Pipeline parcial: KWS → STT")
else:
    print("ℹ️  Modo básico: KWS únicamente")

# --- CONFIGURACIÓN DEL MODELO Y AUDIO ---
TFLITE_MODEL_PATH = "jeepy_kws_model_quantized.tflite"
SAMPLE_RATE = 16000  # Debe coincidir con el entrenamiento (16 kHz)
MFCC_COUNT = 40  # Debe coincidir con el entrenamiento (40 coeficientes)
MAX_PADDING_LENGTH = 40  # Debe coincidir con el entrenamiento (~40 para 1 segundo)
FORMAT = (
    pyaudio.paFloat32
)  # Usamos Float32 para evitar conversiones complejas si el modelo TFLite lo requiere
CHANNELS = 1

# --- CONFIGURACIÓN DE ACTIVACIÓN ---
ACTIVATION_THRESHOLD = (
    0.95  # Umbral de confianza (ajustar aquí, usar >0.95 por la precisión baja)
)

# --- CONFIGURACIÓN DE VENTANA DESLIZANTE ---
WINDOW_DURATION_MS = 1000  # Duración de cada ventana de análisis (1 segundo, mantener compatibilidad con modelo)
STRIDE_MS = 250  # Desplazamiento entre ventanas (250-500ms)
WINDOW_SIZE = int(SAMPLE_RATE * WINDOW_DURATION_MS / 1000)  # 16000 samples
STRIDE_SIZE = int(SAMPLE_RATE * STRIDE_MS / 1000)  # 4000 samples

# --- CONFIGURACIÓN ANTI-FALSOS POSITIVOS ---
CONFIRMATION_COUNT = 2  # Número de detecciones consecutivas requeridas (2-3)
CONFIRMATION_WINDOW_MS = 1500  # Ventana de tiempo máxima para confirmaciones (1.5s)
COOLDOWN_SECONDS = 3  # Tiempo de espera después de activación válida

# --- CONFIGURACIÓN BUFFER PRE-ACTIVACIÓN ---
PRE_ACTIVATION_BUFFER_SECONDS = 2.5  # Mantener 2-3 segundos antes de activación
PRE_BUFFER_SIZE = int(SAMPLE_RATE * PRE_ACTIVATION_BUFFER_SECONDS)

# --- CONFIGURACIÓN DE LOGGING ---
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "kws_monitor.log"
LOG_STATS_INTERVAL_SECONDS = 60  # Intervalo para registrar estadísticas
ENABLE_DEBUG_AUDIO_DUMP = False  # Guardar audio cuando se detecta palabra clave (debug)
DEBUG_AUDIO_PATH = "./debug_audio/"

# --- CONFIGURACIÓN VAD Y THREADING ---
VAD_INITIAL_THRESHOLD_RMS = 0.005  # Umbral inicial de energía para detectar voz
QUEUE_SIZE = 20  # Tamaño de la cola de audio (aprox 5 segundos)
CPU_MONITOR_INTERVAL = 2.0  # Segundos entre lecturas de CPU

# --- CONFIGURACIÓN DE GRABACIÓN DE COMANDOS ---
RECORDING_SILENCE_THRESHOLD_MULTIPLIER = (
    2.0  # Multiplicador del noise_floor para detectar silencio
)
RECORDING_SILENCE_DURATION_SEC = (
    1.5  # Segundos de silencio continuo para terminar grabación
)
RECORDING_MAX_DURATION_SEC = 10.0  # Duración máxima de grabación (safety timeout)
RECORDING_MIN_DURATION_SEC = (
    0.5  # Duración mínima antes de permitir finalización por silencio
)
CAPTURED_COMMANDS_DIR = "./captured_commands/"

# --- CONFIGURACIÓN FASE 4: ROBUSTEZ ---
MAX_INFERENCE_RETRIES = 3  # Número de reintentos ante errores de inferencia
MICROPHONE_RECONNECT_DELAY = 2.0  # Segundos antes de reintentar conexión al micrófono
MAX_MICROPHONE_RECONNECT_ATTEMPTS = 5  # Intentos de reconexión antes de abortar
ERROR_RECOVERY_COOLDOWN = 1.0  # Cooldown después de errores para evitar spam
AUDIO_CHUNK_TIMEOUT = 2.0  # Timeout para detectar micrófono congelado

# --- CONFIGURACIÓN FASE 5: UX AVANZADO ---
ENABLE_CONTROL_COMMANDS = True  # Habilitar comandos de control ("Jeepy, detente")
CONTROL_COMMANDS = {
    "detente": "stop",
    "para": "stop",
    "pausa": "pause",
    "continua": "resume",
    "continúa": "resume",
    "recalibrar": "recalibrate",
    "calibrar": "recalibrate",
    "estado": "status",
    "estadísticas": "stats",
}
ENABLE_INTERACTIVE_MODE = True  # Permitir entrada de texto manual (desarrollo)
LED_PATTERN_MONITORING = "slow_pulse"  # Patrón LED en modo monitoring
LED_PATTERN_RECORDING = "solid"  # Patrón LED durante grabación
LED_PATTERN_ERROR = "fast_blink"  # Patrón LED en error

# --- CONFIGURACIÓN DE INTEGRACIÓN STT ---
ENABLE_STT_PROCESSING = True  # Habilitar transcripción automática de comandos
STT_AUTO_DELETE_AUDIO = True  # Eliminar WAV después de transcribir
STT_SAVE_TRANSCRIPTIONS = True  # Guardar transcripciones en archivo
TRANSCRIPTIONS_DIR = "./transcriptions/"  # Directorio para transcripciones

# --- CONFIGURACIÓN DE INTEGRACIÓN GEMINI ---
ENABLE_GEMINI_NLU = True  # Habilitar interpretación de comandos con Gemini
GEMINI_AUTO_EXECUTE = True  # Ejecutar automáticamente acciones interpretadas
GEMINI_SAVE_RESULTS = True  # Guardar resultados de interpretación
INTERPRETATIONS_DIR = "./interpretations/"  # Directorio para resultados Gemini

# --- ESTADOS DEL SISTEMA ---
STATE_MONITORING = "monitoring"
STATE_RECORDING = "recording"
STATE_PROCESSING = "processing"
STATE_TRANSCRIBING = "transcribing"  # Estado para STT
STATE_PROCESSING_NLU = "processing_nlu"  # Estado para Gemini NLU
STATE_ERROR = "error"
STATE_PAUSED = "paused"


# --- CLASES DE MEJORA ---


class ErrorRecoveryManager:
    """Gestiona reintentos y recuperación ante errores"""

    def __init__(self, max_retries=MAX_INFERENCE_RETRIES):
        self.max_retries = max_retries
        self.error_counts = {}
        self.last_error_time = {}

    def should_retry(self, error_type):
        """Determina si se debe reintentar ante un error"""
        current_time = time.time()

        # Resetear contador si pasó el cooldown
        if error_type in self.last_error_time:
            if (
                current_time - self.last_error_time[error_type]
                > ERROR_RECOVERY_COOLDOWN
            ):
                self.error_counts[error_type] = 0

        # Incrementar contador
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_error_time[error_type] = current_time

        return self.error_counts[error_type] <= self.max_retries

    def reset(self, error_type):
        """Resetea contador de errores exitosamente recuperados"""
        self.error_counts[error_type] = 0

    def get_error_count(self, error_type):
        """Obtiene contador de errores"""
        return self.error_counts.get(error_type, 0)


class AudioChunk:
    """Objeto para transportar datos de audio entre hilos"""

    def __init__(self, data, timestamp, rms):
        self.data = data
        self.timestamp = timestamp
        self.rms = rms


class SystemState:
    """Estado compartido thread-safe para monitoreo"""

    def __init__(self):
        self.fps = 0.0
        self.cpu_usage = 0.0
        self.last_prediction = 0.0
        self.is_speaking = False
        self.noise_level = 0.0
        self.current_state = STATE_MONITORING  # Estado del sistema
        self.paused = False
        self.control_command = None  # Para comunicación de comandos de control
        self.last_error = None
        self.lock = threading.Lock()

    def update_metrics(self, fps=None, cpu=None, pred=None, speaking=None, noise=None):
        with self.lock:
            if fps is not None:
                self.fps = fps
            if cpu is not None:
                self.cpu_usage = cpu
            if pred is not None:
                self.last_prediction = pred
            if speaking is not None:
                self.is_speaking = speaking
            if noise is not None:
                self.noise_level = noise

    def set_state(self, state):
        with self.lock:
            self.current_state = state

    def get_state(self):
        with self.lock:
            return self.current_state

    def set_paused(self, paused):
        with self.lock:
            self.paused = paused

    def is_paused(self):
        with self.lock:
            return self.paused

    def send_control_command(self, command):
        """Envía comando de control al sistema"""
        with self.lock:
            self.control_command = command

    def get_control_command(self):
        """Obtiene y limpia comando de control pendiente"""
        with self.lock:
            cmd = self.control_command
            self.control_command = None
            return cmd

    def set_error(self, error_msg):
        with self.lock:
            self.last_error = error_msg
            self.current_state = STATE_ERROR

    def get_status_string(self):
        with self.lock:
            vad_state = "🗣️" if self.is_speaking else ".."
            state_icons = {
                STATE_MONITORING: "👀",
                STATE_RECORDING: "🔴",
                STATE_PROCESSING: "⚙️",
                STATE_TRANSCRIBING: "📝",
                STATE_PROCESSING_NLU: "🤖",
                STATE_ERROR: "❌",
                STATE_PAUSED: "⏸️",
            }
            state_icon = state_icons.get(self.current_state, "❓")
            pause_marker = " [PAUSADO]" if self.paused else ""
            return f"{state_icon} CPU: {self.cpu_usage:4.1f}% | FPS: {self.fps:4.1f} | VAD: {vad_state} | Conf: {self.last_prediction:.4f} | Noise: {self.noise_level:.4f}{pause_marker}"


class AudioCaptureThread(threading.Thread):
    """Hilo productor: Captura audio con reconexión automática"""

    def __init__(self, device_index, queue, stop_event, system_state):
        super().__init__()
        self.device_index = device_index
        self.queue = queue
        self.stop_event = stop_event
        self.state = system_state
        self.daemon = True
        self.last_chunk_time = time.time()

    def _open_stream(self, p):
        """Abre stream de audio con manejo de errores"""
        try:
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=STRIDE_SIZE,
            )
            print(f"✓ Captura de audio iniciada (dispositivo {self.device_index})")
            return stream
        except Exception as e:
            print(f"❌ Error al abrir micrófono: {e}")
            return None

    def run(self):
        p = pyaudio.PyAudio()
        reconnect_attempts = 0

        while (
            not self.stop_event.is_set()
            and reconnect_attempts < MAX_MICROPHONE_RECONNECT_ATTEMPTS
        ):
            stream = self._open_stream(p)
            if not stream:
                reconnect_attempts += 1
                print(
                    f"Reintentando en {MICROPHONE_RECONNECT_DELAY}s... ({reconnect_attempts}/{MAX_MICROPHONE_RECONNECT_ATTEMPTS})"
                )
                time.sleep(MICROPHONE_RECONNECT_DELAY)
                continue

            reconnect_attempts = 0  # Resetear si conexión exitosa

            try:
                while not self.stop_event.is_set():
                    # Verificar timeout de micrófono congelado
                    if time.time() - self.last_chunk_time > AUDIO_CHUNK_TIMEOUT:
                        print("⚠ Timeout: micrófono congelado, reconectando...")
                        self.state.set_error("Micrófono congelado")
                        break

                    try:
                        data = stream.read(STRIDE_SIZE, exception_on_overflow=False)
                        np_data = np.frombuffer(data, dtype=np.float32)
                        self.last_chunk_time = time.time()

                        rms = np.sqrt(np.mean(np_data**2))
                        chunk = AudioChunk(np_data, time.time(), rms)

                        try:
                            self.queue.put(chunk, block=False)
                        except queue.Full:
                            # Drop oldest frame
                            try:
                                self.queue.get_nowait()
                                self.queue.put(chunk, block=False)
                            except:
                                pass

                    except IOError as e:
                        print(f"⚠ Error I/O: {e}, reconectando...")
                        self.state.set_error(f"Error I/O: {e}")
                        break

            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                self.state.set_error(f"Error captura: {e}")
            finally:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass

            if not self.stop_event.is_set():
                reconnect_attempts += 1
                if reconnect_attempts < MAX_MICROPHONE_RECONNECT_ATTEMPTS:
                    print(
                        f"Reconectando en {MICROPHONE_RECONNECT_DELAY}s... ({reconnect_attempts}/{MAX_MICROPHONE_RECONNECT_ATTEMPTS})"
                    )
                    time.sleep(MICROPHONE_RECONNECT_DELAY)

        p.terminate()
        if reconnect_attempts >= MAX_MICROPHONE_RECONNECT_ATTEMPTS:
            print("❌ Máximo de reconexiones alcanzado")
            self.state.set_error("Máximo de reconexiones")
        else:
            print("✓ Captura detenida")


class FeedbackManager:
    """Gestiona feedback de usuario (sonidos y GPIO)"""

    def __init__(self):
        self.has_gpio = False
        try:
            import RPi.GPIO as GPIO

            self.GPIO = GPIO
            self.has_gpio = True
            self.LED_PIN = 17
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.LED_PIN, GPIO.OUT)
            GPIO.output(self.LED_PIN, GPIO.LOW)
        except ImportError:
            pass  # Modo simulación en PC

    def _play_sound(self, message):
        """Reproduce un beep o mensaje (simulado en PC)"""
        print(f"\n🔔 {message}")
        # En Raspberry Pi con archivos de sonido reales:
        # subprocess.Popen(['aplay', '-q', f'assets/sounds/{sound_file}.wav'])

    def signal_listening(self):
        """Señal de inicio de grabación"""
        if self.has_gpio:
            self.GPIO.output(self.LED_PIN, self.GPIO.HIGH)
        self._play_sound("INICIO DE GRABACIÓN")

    def signal_processing(self):
        """Señal de fin de grabación"""
        if self.has_gpio:
            self.GPIO.output(self.LED_PIN, self.GPIO.LOW)
        self._play_sound("FIN DE GRABACIÓN")

    def signal_error(self):
        """Señal de error del sistema"""
        self._play_sound("ERROR DEL SISTEMA")
        # Parpadeo rápido en GPIO si está disponible
        if self.has_gpio:
            for _ in range(3):
                self.GPIO.output(self.LED_PIN, self.GPIO.HIGH)
                time.sleep(0.1)
                self.GPIO.output(self.LED_PIN, self.GPIO.LOW)
                time.sleep(0.1)

    def cleanup(self):
        """Limpieza de recursos GPIO"""
        if self.has_gpio:
            self.GPIO.cleanup()


def save_wav_file(audio_data, filename, sample_rate=SAMPLE_RATE):
    """Guarda audio en formato WAV"""
    import wave

    # Convertir float32 a int16
    audio_int16 = (audio_data * 32767).astype(np.int16)

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 2 bytes = 16 bits
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


class InferenceThread(threading.Thread):
    """Hilo consumidor: Procesa audio, VAD e inferencia"""

    def __init__(self, queue, stop_event, system_state, logger):
        super().__init__()
        self.queue = queue
        self.stop_event = stop_event
        self.state = system_state
        self.logger = logger
        self.daemon = True

    def run(self):
        # Inicializar componentes en este hilo
        interpreter, input_details, output_details = initialize_tflite_interpreter()
        if not interpreter:
            self.state.set_state(STATE_ERROR)
            return

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

        # Inicializar STT Manager
        if STT_ENABLED and ENABLE_STT_PROCESSING:
            try:
                self.stt_manager = STTManager()
                self.logger.info(f"STT Manager inicializado: {Config.STT_ENGINE}")
                print(f"🎤 STT habilitado: {Config.STT_ENGINE}")
            except Exception as e:
                self.logger.error(f"Error inicializando STT: {e}")
                print(f"⚠️ STT no disponible: {e}")
                self.stt_manager = None
        else:
            self.stt_manager = None
            if not STT_ENABLED:
                print("ℹ️ STT deshabilitado (módulos no disponibles)")

        # Inicializar Gemini Engine y Vehicle Controller
        if GEMINI_ENABLED and ENABLE_GEMINI_NLU:
            try:
                self.gemini_engine = GeminiEngine()
                self.vehicle_controller = VehicleController()
                self.logger.info(f"Gemini NLU inicializado: {Config.GEMINI_MODEL}")
                print(f"🤖 Gemini habilitado: {Config.GEMINI_MODEL}")
            except Exception as e:
                self.logger.error(f"Error inicializando Gemini: {e}")
                print(f"⚠️ Gemini no disponible: {e}")
                self.gemini_engine = None
                self.vehicle_controller = None
        else:
            self.gemini_engine = None
            self.vehicle_controller = None
            if not GEMINI_ENABLED:
                print("ℹ️ Gemini deshabilitado (módulos no disponibles)")

        # Variables para VAD y métricas
        noise_floor = VAD_INITIAL_THRESHOLD_RMS
        vad_threshold = VAD_INITIAL_THRESHOLD_RMS * 1.5
        inference_count_window = []

        # Variables para grabación
        recording_buffer = []
        recording_start_time = 0
        silence_start_time = None
        silence_chunks_count = 0

        # Crear directorio de comandos capturados
        os.makedirs(CAPTURED_COMMANDS_DIR, exist_ok=True)

        # Crear directorio de transcripciones si STT está habilitado
        if STT_ENABLED and STT_SAVE_TRANSCRIPTIONS:
            os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)

        while not self.stop_event.is_set():
            # Verificar comandos de control
            control_cmd = self.state.get_control_command()
            if control_cmd:
                self._handle_control_command(
                    control_cmd, stats, confirmation_tracker, feedback
                )
                continue

            # Verificar si está pausado
            if self.state.is_paused():
                time.sleep(0.1)
                continue

            try:
                chunk = self.queue.get(timeout=1.0)
            except queue.Empty:
                continue

            current_time = time.time()
            current_state = self.state.get_state()

            # === ESTADO: MONITORING ===
            if current_state == STATE_MONITORING:
                # 1. Actualizar buffers
                sliding_buffer.add_samples(chunk.data)
                pre_activation_buffer.write(chunk.data)

                # 2. Lógica VAD y Ruido Adaptativo
                noise_floor = (0.95 * noise_floor) + (0.05 * chunk.rms)
                vad_threshold = noise_floor * 1.5

                is_speaking = chunk.rms > vad_threshold
                self.state.update_metrics(noise=noise_floor, speaking=is_speaking)

                # Si es silencio absoluto, saltar inferencia (ahorro CPU)
                if not is_speaking and chunk.rms < VAD_INITIAL_THRESHOLD_RMS:
                    self.state.update_metrics(pred=0.0)
                    continue

                if not sliding_buffer.is_ready():
                    continue

                # 3. Inferencia
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
                    inference_count_window = [
                        t for t in inference_count_window if now - t < 1.0
                    ]
                    fps = len(inference_count_window)

                    self.state.update_metrics(pred=prob, fps=fps)
                    stats.record_inference(inf_time)

                    # 4. Lógica de Activación
                    if prob >= ACTIVATION_THRESHOLD:
                        if not confirmation_tracker.is_in_cooldown(now):
                            confirmation_tracker.add_detection(prob, now)
                            stats.record_detection(prob, confirmed=False)

                            if confirmation_tracker.is_confirmed():
                                self.logger.info(
                                    "ACTIVACIÓN CONFIRMADA",
                                    extra={"confidence": float(prob)},
                                )

                                # TRANSICIÓN A RECORDING
                                self.state.set_state(STATE_RECORDING)
                                feedback.signal_listening()

                                # Inicializar buffer de grabación con pre-activación
                                recording_buffer = [
                                    pre_activation_buffer.get_buffer_contents()
                                ]
                                recording_start_time = current_time
                                silence_start_time = None
                                silence_chunks_count = 0

                                print("\n🔴 GRABANDO COMANDO (habla ahora)...\n")

                                confirmation_tracker.activate(now)
                                confirmation_tracker.clear()
                    else:
                        confirmation_tracker.clear_old_detections(now)

            # === ESTADO: RECORDING ===
            elif current_state == STATE_RECORDING:
                # Añadir chunk al buffer de grabación
                recording_buffer.append(chunk.data)

                # Actualizar noise floor incluso durante grabación
                noise_floor = (0.95 * noise_floor) + (0.05 * chunk.rms)

                # Calcular umbral de silencio (más alto que el umbral de voz normal)
                silence_threshold = noise_floor * RECORDING_SILENCE_THRESHOLD_MULTIPLIER

                recording_duration = current_time - recording_start_time

                # Detectar silencio
                if chunk.rms < silence_threshold:
                    if silence_start_time is None:
                        silence_start_time = current_time
                        silence_chunks_count = 1
                    else:
                        silence_chunks_count += 1

                    silence_duration = current_time - silence_start_time

                    # Verificar si se cumple el criterio de finalización
                    if (
                        silence_duration >= RECORDING_SILENCE_DURATION_SEC
                        and recording_duration >= RECORDING_MIN_DURATION_SEC
                    ):
                        # FIN DE GRABACIÓN POR SILENCIO
                        self._finish_recording(recording_buffer, feedback, current_time)

                        # TRANSICIÓN A MONITORING
                        self.state.set_state(STATE_MONITORING)
                        recording_buffer = []

                else:
                    # Hay voz, resetear contador de silencio
                    silence_start_time = None
                    silence_chunks_count = 0

                # Safety timeout: grabación máxima
                if recording_duration >= RECORDING_MAX_DURATION_SEC:
                    self.logger.warning(
                        f"Grabación alcanzó timeout máximo ({RECORDING_MAX_DURATION_SEC}s)"
                    )
                    self._finish_recording(recording_buffer, feedback, current_time)
                    self.state.set_state(STATE_MONITORING)
                    recording_buffer = []

        # Cleanup
        feedback.cleanup()

    def _handle_control_command(self, command, stats, confirmation_tracker, feedback):
        """Procesa comandos de control del sistema"""
        self.logger.info(f"Comando de control recibido: {command}")

        if command == "stop":
            print("\n🛑 Sistema detenido por comando de usuario")
            self.stop_event.set()

        elif command == "pause":
            self.state.set_paused(True)
            self.state.set_state(STATE_PAUSED)
            print("\n⏸️  Sistema pausado")

        elif command == "resume":
            self.state.set_paused(False)
            self.state.set_state(STATE_MONITORING)
            print("\n▶️  Sistema reanudado")

        elif command == "recalibrate":
            print("\n🔧 Recalibrando umbrales...")
            confirmation_tracker.clear()
            # El noise floor se recalibrará automáticamente
            print("✅ Recalibración completada")

        elif command == "status":
            self._print_detailed_status(stats)

        elif command == "stats":
            stats.print_summary(self.logger)

    def _print_detailed_status(self, stats):
        """Imprime estado detallado del sistema"""
        print("\n" + "=" * 60)
        print("📊 ESTADO DETALLADO DEL SISTEMA")
        print("=" * 60)
        print(f"Estado actual: {self.state.get_state()}")
        print(f"Pausado: {self.state.is_paused()}")
        print(f"FPS: {self.state.fps:.1f}")
        print(f"CPU: {self.state.cpu:.1f}%")
        print(f"Nivel de ruido: {self.state.noise_level:.4f}")
        print(f"Hablando: {self.state.is_speaking}")
        print(f"\nEstadísticas KWS:")
        print(f"  Total inferencias: {stats.total_inferences}")
        print(f"  Detecciones: {stats.detections}")
        print(f"  Activaciones confirmadas: {stats.confirmed_activations}")
        print(f"  Falsos positivos: {stats.false_positives}")
        if stats.detections > 0:
            print(
                f"  Tasa de confirmación: {100 * stats.confirmed_activations / stats.detections:.1f}%"
            )
        print("=" * 60 + "\n")

    def _finish_recording(self, recording_buffer, feedback, timestamp):
        """Procesa y guarda el comando grabado"""
        self.state.set_state(STATE_PROCESSING)
        feedback.signal_processing()

        # Concatenar todo el audio
        full_audio = np.concatenate(recording_buffer)

        # Guardar archivo
        filename = os.path.join(
            CAPTURED_COMMANDS_DIR, f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        )
        save_wav_file(full_audio, filename)

        duration = len(full_audio) / SAMPLE_RATE
        self.logger.info(f"Comando guardado: {filename} ({duration:.2f}s)")
        print(f"\n✅ Comando guardado: {filename} ({duration:.2f}s)")

        # Procesar con STT si está habilitado
        if STT_ENABLED and ENABLE_STT_PROCESSING and hasattr(self, "stt_manager"):
            self._transcribe_command(filename, duration)

        # Pequeña pausa para evitar re-activación
        time.sleep(0.5)

    def _transcribe_command(self, audio_file, duration):
        """Transcribe comando de audio a texto y lo procesa con Gemini"""
        try:
            self.state.set_state(STATE_TRANSCRIBING)
            print(f"📝 Transcribiendo comando...")

            # Transcribir usando STTManager
            transcription = self.stt_manager.transcribe(audio_file)

            if transcription:
                self.logger.info(f"Transcripción: {transcription}")
                print(f'\n💬 Transcripción: "{transcription}"\n')

                # Guardar transcripción si está habilitado
                if STT_SAVE_TRANSCRIPTIONS:
                    self._save_transcription(audio_file, transcription, duration)

                # Procesar con Gemini si está habilitado
                if self.gemini_engine and ENABLE_GEMINI_NLU:
                    self._process_with_gemini(transcription, audio_file)

                # Eliminar audio si está configurado
                if STT_AUTO_DELETE_AUDIO:
                    try:
                        os.remove(audio_file)
                        self.logger.info(f"Audio eliminado: {audio_file}")
                    except Exception as e:
                        self.logger.warning(f"No se pudo eliminar audio: {e}")

                return transcription
            else:
                print(f"⚠️ No se pudo transcribir el comando")
                self.logger.warning("Transcripción falló")
                return None

        except Exception as e:
            print(f"❌ Error en transcripción: {e}")
            self.logger.error(f"Error en transcripción: {e}")
            return None
        finally:
            self.state.set_state(STATE_MONITORING)

    def _save_transcription(self, audio_file, transcription, duration):
        """Guarda transcripción en archivo"""
        try:
            # Crear directorio si no existe
            os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)

            # Generar nombre de archivo (mismo timestamp que el audio)
            timestamp = (
                os.path.basename(audio_file).replace("cmd_", "").replace(".wav", "")
            )
            txt_filename = os.path.join(TRANSCRIPTIONS_DIR, f"trans_{timestamp}.txt")

            # Guardar con metadata
            with open(txt_filename, "w", encoding="utf-8") as f:
                f.write(f"# Transcripción de comando\n")
                f.write(f"# Audio: {audio_file}\n")
                f.write(f"# Duración: {duration:.2f}s\n")
                f.write(f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Motor STT: {Config.STT_ENGINE if STT_ENABLED else 'N/A'}\n")
                f.write(f"\n{transcription}\n")

            self.logger.info(f"Transcripción guardada: {txt_filename}")
            print(f"   💾 Guardado en: {txt_filename}")

        except Exception as e:
            self.logger.error(f"Error guardando transcripción: {e}")
            print(f"   ⚠️ No se pudo guardar transcripción: {e}")

    def _process_with_gemini(self, transcription, audio_file):
        """Procesa transcripción con Gemini NLU y ejecuta acción"""
        try:
            self.state.set_state(STATE_PROCESSING_NLU)
            print(f"\n🤖 Procesando con Gemini...\n")

            # Interpretar comando con Gemini
            result = self.gemini_engine.process_command(transcription)

            if not result:
                print(f"⚠️ Gemini no pudo interpretar el comando")
                self.logger.warning("Interpretación Gemini falló")
                return None

            # Log del resultado
            self.logger.info(
                f"Gemini - Acción: {result.get('action')}, Confianza: {result.get('confidence', 0):.2f}"
            )

            # Ejecutar acción si auto-ejecutar está habilitado
            if GEMINI_AUTO_EXECUTE and result["action"] != "aclaracion_requerida":
                execution_result = self.vehicle_controller.execute_action(
                    result["action"], result.get("parameters", {})
                )
                result["execution"] = execution_result

                # Mostrar respuesta natural
                if result.get("natural_response"):
                    print(f"\n💬 Jeepy: {result['natural_response']}\n")
            else:
                # Solo mostrar qué haría sin ejecutar
                print(f"   🔍 Acción detectada: {result['action']}")
                print(
                    f"   📊 Parámetros: {json.dumps(result.get('parameters', {}), indent=2)}"
                )
                if result.get("natural_response"):
                    print(f"   💬 Respuesta: {result['natural_response']}\n")

            # Guardar resultado si está habilitado
            if GEMINI_SAVE_RESULTS:
                self._save_gemini_result(audio_file, transcription, result)

            return result

        except Exception as e:
            print(f"❌ Error procesando con Gemini: {e}")
            self.logger.error(f"Error en procesamiento Gemini: {e}")
            import traceback

            traceback.print_exc()
            return None
        finally:
            self.state.set_state(STATE_MONITORING)

    def _save_gemini_result(self, audio_file, transcription, result):
        """Guarda resultado de interpretación Gemini"""
        try:
            # Crear directorio si no existe
            os.makedirs(INTERPRETATIONS_DIR, exist_ok=True)

            # Generar nombre de archivo (mismo timestamp que el audio)
            timestamp = (
                os.path.basename(audio_file).replace("cmd_", "").replace(".wav", "")
            )
            json_filename = os.path.join(
                INTERPRETATIONS_DIR, f"interpret_{timestamp}.json"
            )

            # Compilar resultado completo
            full_result = {
                "audio_file": audio_file,
                "transcription": transcription,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "gemini_model": Config.GEMINI_MODEL if GEMINI_ENABLED else "N/A",
                "interpretation": result,
            }

            # Guardar como JSON
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(full_result, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Interpretación guardada: {json_filename}")
            print(f"   💾 Interpretación guardada: {json_filename}")

        except Exception as e:
            self.logger.error(f"Error guardando interpretación: {e}")
            print(f"   ⚠️ No se pudo guardar interpretación: {e}")


class SlidingWindowBuffer:
    """
    Buffer circular que mantiene audio para ventanas deslizantes.
    """

    def __init__(self, window_size, stride_size):
        self.window_size = window_size
        self.stride_size = stride_size
        self.buffer = np.zeros(window_size, dtype=np.float32)

    def add_samples(self, samples):
        """Añade nuevas muestras al buffer (desplaza y añade al final)"""
        # Desplazar el buffer hacia la izquierda
        self.buffer = np.roll(self.buffer, -len(samples))
        # Escribir nuevas muestras al final
        self.buffer[-len(samples) :] = samples

    def get_window(self):
        """Retorna la ventana actual completa"""
        return self.buffer

    def is_ready(self):
        """Verifica si hay suficientes datos para una ventana (siempre True si inicializamos con ceros)"""
        return True


class ConfirmationTracker:
    """
    Rastrea detecciones consecutivas para confirmar activación.
    """

    def __init__(self, required_count, window_ms):
        self.required_count = required_count
        self.window_duration = window_ms / 1000.0
        self.detections = []  # Lista de tuplas (timestamp, confidence)
        self.last_activation_time = 0
        self.cooldown_duration = COOLDOWN_SECONDS

    def add_detection(self, confidence, timestamp):
        """Añade una detección positiva"""
        self.detections.append((timestamp, confidence))
        self.clear_old_detections(timestamp)

    def clear_old_detections(self, current_time):
        """Elimina detecciones fuera de la ventana de tiempo"""
        self.detections = [
            d for d in self.detections if current_time - d[0] <= self.window_duration
        ]

    def is_confirmed(self):
        """Verifica si hay suficientes detecciones consecutivas"""
        return len(self.detections) >= self.required_count

    def clear(self):
        """Limpia el historial de detecciones"""
        self.detections = []

    def is_in_cooldown(self, current_time):
        """Verifica si estamos en período de cooldown"""
        return (current_time - self.last_activation_time) < self.cooldown_duration

    def activate(self, timestamp):
        """Marca una activación confirmada"""
        self.last_activation_time = timestamp


class CircularAudioBuffer:
    """
    Buffer circular que mantiene los últimos N segundos de audio.
    Útil para capturar audio antes de la detección de palabra clave.
    """

    def __init__(self, buffer_duration_seconds, sample_rate):
        self.sample_rate = sample_rate
        self.buffer_size = int(sample_rate * buffer_duration_seconds)
        self.buffer = np.zeros(self.buffer_size, dtype=np.float32)

    def write(self, samples):
        """Escribe nuevas muestras en el buffer circular"""
        self.buffer = np.roll(self.buffer, -len(samples))
        self.buffer[-len(samples) :] = samples

    def get_buffer_contents(self):
        """Retorna el contenido completo del buffer en orden cronológico"""
        return self.buffer


class KWSStatistics:
    """
    Rastrea y registra estadísticas del sistema KWS.
    """

    def __init__(self):
        self.start_time = time.time()
        self.total_inferences = 0
        self.total_detections_above_threshold = 0
        self.total_confirmed_activations = 0
        self.inference_times = []

    def record_inference(self, inference_time):
        """Registra el tiempo de una inferencia"""
        self.total_inferences += 1
        self.inference_times.append(inference_time)
        if len(self.inference_times) > 1000:  # Mantener solo los últimos 1000
            self.inference_times.pop(0)

    def record_detection(self, confidence, confirmed=False):
        """Registra una detección"""
        if confirmed:
            self.total_confirmed_activations += 1
        else:
            self.total_detections_above_threshold += 1

    def get_stats_dict(self):
        """Retorna diccionario con todas las estadísticas"""
        avg_inf = (
            sum(self.inference_times) / len(self.inference_times)
            if self.inference_times
            else 0
        )
        return {
            "uptime_seconds": time.time() - self.start_time,
            "total_inferences": self.total_inferences,
            "detections_above_threshold": self.total_detections_above_threshold,
            "confirmed_activations": self.total_confirmed_activations,
            "avg_inference_time_ms": avg_inf * 1000,
        }

    def log_periodic_stats(self, logger):
        """Registra estadísticas periódicas en el log"""
        logger.info("Estadísticas KWS", extra=self.get_stats_dict())


class ActivationEvent:
    """
    Clase para estructurar eventos de activación.
    """

    def __init__(
        self, timestamp, confidence, pre_buffer_duration, confirmation_detections
    ):
        self.timestamp = timestamp
        self.confidence = confidence
        self.pre_buffer_duration = pre_buffer_duration
        self.confirmation_detections = confirmation_detections

    def to_dict(self):
        """Convierte el evento a diccionario para logging"""
        return {
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "pre_buffer_duration": self.pre_buffer_duration,
            "confirmation_detections": self.confirmation_detections,
        }

    def save_debug_audio(self, audio_data, path):
        """Guarda audio de debug si está habilitado"""
        if not os.path.exists(path):
            os.makedirs(path)
        filename = os.path.join(
            path, f"activation_{self.timestamp.replace(':', '-')}.wav"
        )
        # Aquí se necesitaría guardar el wav, pero por simplicidad solo imprimimos
        print(f"Guardando audio debug en {filename}")
        # Implementación real requeriría wave module y conversión a int16


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra"):
            log_record.update(record.extra)
        elif record.args and isinstance(record.args, dict):
            log_record.update(record.args)
        return json.dumps(log_record)


def setup_logger(log_level, log_file):
    """
    Configura el sistema de logging estructurado.
    """
    logger = logging.getLogger("KWS_Monitor")
    logger.setLevel(getattr(logging, log_level))

    # File Handler
    fh = logging.FileHandler(log_file)
    fh.setFormatter(JsonFormatter())
    logger.addHandler(fh)

    # Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)

    return logger


def get_input_device_index():
    """Identifica el índice del dispositivo de entrada (micrófono) para PyAudio."""
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get("deviceCount")

    print("\n--- Dispositivos de Audio Disponibles ---")
    for i in range(0, numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if (device_info.get("maxInputChannels")) > 0:
            print(f"  Input Device Index {i} - {device_info.get('name')}")

    p.terminate()

    # Pídele al usuario que introduzca el índice manualmente
    try:
        index = int(input("\nPor favor, introduce el índice de tu micrófono: "))
        return index
    except ValueError:
        print("Entrada no válida. Usando el índice 0 por defecto.")
        return 0


def extract_mfcc(audio_chunk):
    """
    Función para extraer MFCCs, idéntica a la usada en el entrenamiento.
    """
    try:
        # Extraer MFCCs
        # Nota: librosa espera muestras de punto flotante (dtype=float32)
        mfccs = librosa.feature.mfcc(y=audio_chunk, sr=SAMPLE_RATE, n_mfcc=MFCC_COUNT)

        # Aplicar Padding
        if mfccs.shape[1] < MAX_PADDING_LENGTH:
            padding_width = MAX_PADDING_LENGTH - mfccs.shape[1]
            mfccs = np.pad(
                mfccs, pad_width=((0, 0), (0, padding_width)), mode="constant"
            )
        else:
            mfccs = mfccs[:, :MAX_PADDING_LENGTH]

        # Asegurar la forma (MFCC_COUNT, MAX_PADDING_LENGTH, 1) y el tipo (float32)
        mfccs = mfccs[np.newaxis, ..., np.newaxis].astype(np.float32)
        return mfccs

    except Exception as e:
        print(f"Error en la extracción de MFCCs: {e}")
        return None


def initialize_tflite_interpreter():
    """
    Carga el modelo TFLite cuantizado y prepara el intérprete.
    """
    try:
        # Cargar el modelo TFLite (En RPi, usar tflite_runtime.interpreter)
        interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
        interpreter.allocate_tensors()

        # Obtener los detalles de las capas de entrada y salida
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        print("✅ Intérprete TFLite cargado con éxito.")
        return interpreter, input_details, output_details
    except Exception as e:
        print(
            f"❌ Error al cargar el modelo TFLite. Asegúrate de que el archivo existe y las dependencias están instaladas. Error: {e}"
        )
        return None, None, None


def kws_monitor(device_index, interactive=ENABLE_INTERACTIVE_MODE):
    """
    Bucle principal de monitoreo de audio en vivo con mejoras Fases 4-5.
    """
    # 1. INICIALIZACIÓN
    logger = setup_logger(LOG_LEVEL, LOG_FILE)
    logger.info("Iniciando Monitor KWS Mejorado (Fases 1-5)")

    audio_queue = queue.Queue(maxsize=QUEUE_SIZE)
    stop_event = threading.Event()
    system_state = SystemState()

    # 2. INICIAR HILOS
    capture_thread = AudioCaptureThread(
        device_index, audio_queue, stop_event, system_state
    )
    inference_thread = InferenceThread(audio_queue, stop_event, system_state, logger)

    capture_thread.start()
    inference_thread.start()

    print("\n" + "=" * 70)
    print("🚗 JEEPY KWS MONITOR - Sistema de Activación por Voz")
    print("=" * 70)
    print(f"Umbral de activación: {ACTIVATION_THRESHOLD}")
    print(f"VAD habilitado | Confirmaciones requeridas: {CONFIRMATION_COUNT}")
    print(f"Comandos de control habilitados: {ENABLE_CONTROL_COMMANDS}")

    # Mostrar estado de STT
    if STT_ENABLED and ENABLE_STT_PROCESSING:
        print(f"🎤 STT habilitado: {Config.STT_ENGINE}")
        print(f"   Transcripciones: {TRANSCRIPTIONS_DIR}")
    else:
        print("ℹ️  STT deshabilitado (solo KWS)")

    if interactive:
        print("\n💡 Modo interactivo habilitado:")
        print("   - Escribe 'pause' para pausar")
        print("   - Escribe 'resume' para continuar")
        print("   - Escribe 'status' para ver estado detallado")
        print("   - Escribe 'stats' para ver estadísticas")
        print("   - Escribe 'recalibrate' para recalibrar")
        print("   - Escribe 'quit' o Ctrl+C para salir")
    print("=" * 70 + "\n")

    # 3. BUCLE DE MONITOREO PRINCIPAL (UI)
    if interactive:
        # Hilo para entrada de comandos
        def input_worker():
            while not stop_event.is_set():
                try:
                    cmd = input().strip().lower()
                    if cmd in ["quit", "exit", "q"]:
                        system_state.send_control_command("stop")
                    elif cmd in CONTROL_COMMANDS:
                        system_state.send_control_command(CONTROL_COMMANDS[cmd])
                    elif cmd in [
                        "pause",
                        "resume",
                        "status",
                        "stats",
                        "recalibrate",
                        "stop",
                    ]:
                        system_state.send_control_command(cmd)
                    elif cmd:
                        print(f"❓ Comando desconocido: {cmd}")
                except EOFError:
                    break
                except:
                    pass

        input_thread = threading.Thread(target=input_worker, daemon=True)
        input_thread.start()

    try:
        last_cpu_check = 0
        last_ui_update = 0
        ui_update_interval = 0.1  # 10Hz

        while not stop_event.is_set():
            time.sleep(0.05)
            current_time = time.time()

            # Actualizar CPU periódicamente
            if current_time - last_cpu_check > CPU_MONITOR_INTERVAL:
                cpu = psutil.cpu_percent()
                system_state.update_metrics(cpu=cpu)
                last_cpu_check = current_time

            # Actualizar UI
            if current_time - last_ui_update > ui_update_interval:
                print(f"\r{system_state.get_status_string()}", end="", flush=True)
                last_ui_update = current_time

            # Verificar salud de hilos
            if not capture_thread.is_alive():
                logger.error("Hilo de captura murió. Deteniendo sistema...")
                system_state.set_state(STATE_ERROR)
                break

            if not inference_thread.is_alive():
                logger.error("Hilo de inferencia murió. Deteniendo sistema...")
                system_state.set_state(STATE_ERROR)
                break

            # Verificar estado de error
            if system_state.get_state() == STATE_ERROR:
                logger.error("Sistema en estado de error. Deteniendo...")
                break

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupción de usuario detectada...")
    finally:
        print("\n🛑 Deteniendo sistema...")
        stop_event.set()

        print("   Esperando hilos...")
        capture_thread.join(timeout=3.0)
        inference_thread.join(timeout=3.0)

        if system_state.get_state() == STATE_ERROR:
            print("❌ Sistema detenido con errores")
            logger.error("Sistema detenido con errores")
        else:
            print("✅ Sistema detenido correctamente")
            logger.info("Sistema detenido correctamente")

        print()


if __name__ == "__main__":
    # Usamos la importación de tf.lite.Interpreter. Si estás en RPi y tienes problemas,
    # reemplaza 'tensorflow as tf' por 'import tflite_runtime.interpreter as tflite'
    # y ajusta el código según la documentación de tflite-runtime.

    # Seleccionar dispositivo de audio
    mic_index = get_input_device_index()

    kws_monitor(mic_index)
