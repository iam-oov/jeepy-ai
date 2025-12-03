import pyaudio
import numpy as np
import librosa
import time
import tensorflow as tf  # Usaremos tf.lite.Interpreter en lugar de tflite-runtime para simplicidad en el desarrollo
import logging
import json
from datetime import datetime
import os
import threading
import queue
import psutil

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


# --- CLASES DE MEJORA ---


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

    def get_status_string(self):
        with self.lock:
            vad_state = "🗣️" if self.is_speaking else ".."
            return f"CPU: {self.cpu_usage:4.1f}% | FPS: {self.fps:4.1f} | VAD: {vad_state} | Conf: {self.last_prediction:.4f} | Noise: {self.noise_level:.4f}"


class AudioCaptureThread(threading.Thread):
    """Hilo productor: Captura audio y calcula RMS"""

    def __init__(self, device_index, queue, stop_event):
        super().__init__()
        self.device_index = device_index
        self.queue = queue
        self.stop_event = stop_event
        self.daemon = True

    def run(self):
        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=STRIDE_SIZE,
                input_device_index=self.device_index,
            )

            while not self.stop_event.is_set():
                try:
                    data = stream.read(STRIDE_SIZE, exception_on_overflow=False)
                    np_data = np.frombuffer(data, dtype=np.float32)

                    # Calcular RMS para VAD
                    rms = np.sqrt(np.mean(np_data**2))

                    chunk = AudioChunk(np_data, time.time(), rms)

                    try:
                        self.queue.put(chunk, block=False)
                    except queue.Full:
                        # Drop frame strategy: sacar el viejo y poner el nuevo
                        try:
                            self.queue.get_nowait()
                            self.queue.put(chunk, block=False)
                        except:
                            pass  # Queue contention edge case

                except Exception as e:
                    print(f"Error captura audio: {e}")
                    break

        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()


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
            return

        sliding_buffer = SlidingWindowBuffer(WINDOW_SIZE, STRIDE_SIZE)
        pre_activation_buffer = CircularAudioBuffer(
            PRE_ACTIVATION_BUFFER_SECONDS, SAMPLE_RATE
        )
        confirmation_tracker = ConfirmationTracker(
            CONFIRMATION_COUNT, CONFIRMATION_WINDOW_MS
        )
        stats = KWSStatistics()

        # Variables para VAD y métricas
        noise_floor = VAD_INITIAL_THRESHOLD_RMS
        vad_threshold = VAD_INITIAL_THRESHOLD_RMS * 1.5
        inference_count_window = []

        while not self.stop_event.is_set():
            try:
                chunk = self.queue.get(timeout=1.0)
            except queue.Empty:
                continue

            # 1. Actualizar buffers
            sliding_buffer.add_samples(chunk.data)
            pre_activation_buffer.write(chunk.data)

            # 2. Lógica VAD y Ruido Adaptativo
            # Actualizar piso de ruido (promedio exponencial lento)
            noise_floor = (0.95 * noise_floor) + (0.05 * chunk.rms)
            vad_threshold = noise_floor * 1.5  # Umbral dinámico simple

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

                # 4. Lógica de Activación (igual que antes)
                if prob >= ACTIVATION_THRESHOLD:
                    if not confirmation_tracker.is_in_cooldown(now):
                        confirmation_tracker.add_detection(prob, now)
                        stats.record_detection(prob, confirmed=False)

                        if confirmation_tracker.is_confirmed():
                            self.logger.info(
                                "ACTIVACIÓN CONFIRMADA",
                                extra={"confidence": float(prob)},
                            )
                            print("\n\n>>> ¡JEEPY DETECTADO! <<<\n")

                            # Aquí iría la lógica de grabación real
                            # Por ahora simulamos y limpiamos
                            confirmation_tracker.activate(now)
                            confirmation_tracker.clear()
                else:
                    confirmation_tracker.clear_old_detections(now)


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


def kws_monitor(device_index):
    """
    Bucle principal de monitoreo de audio en vivo con mejoras Fase 2 (Threading).
    """
    # 1. INICIALIZACIÓN
    logger = setup_logger(LOG_LEVEL, LOG_FILE)
    logger.info("Iniciando Monitor KWS Fase 2 (Multithreaded)")

    audio_queue = queue.Queue(maxsize=QUEUE_SIZE)
    stop_event = threading.Event()
    system_state = SystemState()

    # 2. INICIAR HILOS
    capture_thread = AudioCaptureThread(device_index, audio_queue, stop_event)
    inference_thread = InferenceThread(audio_queue, stop_event, system_state, logger)

    capture_thread.start()
    inference_thread.start()

    print("\n--- MONITOREO KWS ACTIVO (Multithreaded) ---")
    print(f"Umbral: {ACTIVATION_THRESHOLD} | VAD Activo")

    # 3. BUCLE DE MONITOREO PRINCIPAL (UI)
    try:
        last_cpu_check = 0
        while True:
            time.sleep(0.1)  # Actualización UI a 10Hz

            # Actualizar CPU periódicamente
            if time.time() - last_cpu_check > CPU_MONITOR_INTERVAL:
                cpu = psutil.cpu_percent()
                system_state.update_metrics(cpu=cpu)
                last_cpu_check = time.time()

            # Imprimir estado
            print(f"\r{system_state.get_status_string()}", end="")

            # Verificar salud de hilos
            if not capture_thread.is_alive() or not inference_thread.is_alive():
                logger.error("Uno de los hilos ha muerto. Reiniciando sistema...")
                break

    except KeyboardInterrupt:
        print("\nDeteniendo sistema...")
    finally:
        stop_event.set()
        capture_thread.join(timeout=2.0)
        inference_thread.join(timeout=2.0)
        logger.info("Sistema detenido correctamente")


if __name__ == "__main__":
    # Usamos la importación de tf.lite.Interpreter. Si estás en RPi y tienes problemas,
    # reemplaza 'tensorflow as tf' por 'import tflite_runtime.interpreter as tflite'
    # y ajusta el código según la documentación de tflite-runtime.

    # Seleccionar dispositivo de audio
    mic_index = get_input_device_index()

    kws_monitor(mic_index)
