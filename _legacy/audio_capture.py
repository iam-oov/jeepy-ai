"""
Módulo de Captura de Audio - Jeepy AI
Contiene el hilo productor que captura audio del micrófono.
"""

import threading
import time
import pyaudio
import numpy as np
import queue

from src.monitor.state import AudioChunk, SystemState

# --- CONSTANTES DE AUDIO ---
FORMAT = pyaudio.paFloat32
CHANNELS = 1
SAMPLE_RATE = 16000
STRIDE_MS = 250
STRIDE_SIZE = int(SAMPLE_RATE * STRIDE_MS / 1000)

# --- CONSTANTES DE ROBUSTEZ ---
MAX_MICROPHONE_RECONNECT_ATTEMPTS = 5
MICROPHONE_RECONNECT_DELAY = 2.0
AUDIO_CHUNK_TIMEOUT = 2.0


class AudioCaptureThread(threading.Thread):
    """Hilo productor: Captura audio con reconexión automática."""

    def __init__(
        self,
        device_index: int,
        audio_queue: queue.Queue,
        stop_event: threading.Event,
        system_state: SystemState,
    ):
        super().__init__()
        self.device_index = device_index
        self.audio_queue = audio_queue
        self.stop_event = stop_event
        self.system_state = system_state
        self.daemon = True
        self.last_chunk_time = time.time()

    def _open_stream(self, p: pyaudio.PyAudio):
        """Abre un stream de audio con manejo de errores."""
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

            reconnect_attempts = 0
            try:
                while not self.stop_event.is_set():
                    if time.time() - self.last_chunk_time > AUDIO_CHUNK_TIMEOUT:
                        print("⚠ Timeout: micrófono congelado, reconectando...")
                        self.system_state.set_error("Micrófono congelado")
                        break

                    try:
                        data = stream.read(STRIDE_SIZE, exception_on_overflow=False)
                        np_data = np.frombuffer(data, dtype=np.float32)
                        self.last_chunk_time = time.time()

                        rms = np.sqrt(np.mean(np_data**2))
                        chunk = AudioChunk(np_data, time.time(), rms)

                        try:
                            self.audio_queue.put(chunk, block=False)
                        except queue.Full:
                            try:
                                self.audio_queue.get_nowait()
                                self.audio_queue.put(chunk, block=False)
                            except queue.Empty:
                                pass
                    except IOError as e:
                        print(f"⚠ Error I/O: {e}, reconectando...")
                        self.system_state.set_error(f"Error I/O: {e}")
                        break
            finally:
                if stream:
                    stream.stop_stream()
                    stream.close()

        p.terminate()
        if reconnect_attempts >= MAX_MICROPHONE_RECONNECT_ATTEMPTS:
            print("❌ Máximo de reconexiones alcanzado")
            self.system_state.set_error("Máximo de reconexiones")
        else:
            print("✓ Captura detenida")
