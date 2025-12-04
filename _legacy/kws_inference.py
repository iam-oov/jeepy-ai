"""
Módulo de Inferencia KWS - Jeepy AI
Contiene el hilo consumidor que detecta la palabra clave y gestiona la grabación.
"""

import threading
import queue
import time
import os
from datetime import datetime
import numpy as np
import librosa
import tensorflow as tf

from src.monitor.state import (
    SystemState,
    STATE_MONITORING,
    STATE_RECORDING,
    STATE_PROCESSING,
)
from src.utils import (
    SlidingWindowBuffer,
    CircularAudioBuffer,
    ConfirmationTracker,
    FeedbackManager,
    save_wav_file,
)

# --- CONSTANTES ---
# (Mover constantes relevantes de kws_monitor.py aquí)


class InferenceThread(threading.Thread):
    """Hilo consumidor: Procesa audio, VAD e inferencia KWS."""

    def __init__(
        self,
        audio_queue: queue.Queue,
        processing_queue: queue.Queue,
        stop_event: threading.Event,
        system_state: SystemState,
        logger,
    ):
        super().__init__()
        self.audio_queue = audio_queue
        self.processing_queue = processing_queue
        self.stop_event = stop_event
        self.system_state = system_state
        self.logger = logger
        self.daemon = True

    def run(self):
        # ... (código de inicialización de TFLite, buffers, etc. de kws_monitor.py) ...

        while not self.stop_event.is_set():
            try:
                chunk = self.audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            current_state = self.system_state.get_state()

            if current_state == STATE_MONITORING:
                # ... (lógica de KWS de kws_monitor.py) ...
                if confirmation_tracker.is_confirmed():
                    self.system_state.set_state(STATE_RECORDING)
                    # ...

            elif current_state == STATE_RECORDING:
                # ... (lógica de grabación de kws_monitor.py) ...
                if silence_detected or timeout:
                    self._finish_recording(recording_buffer)
                    self.system_state.set_state(STATE_MONITORING)

    def _finish_recording(self, recording_buffer):
        """Guarda el audio y lo encola para procesamiento."""
        self.system_state.set_state(STATE_PROCESSING)

        full_audio = np.concatenate(recording_buffer)
        filename = os.path.join(
            "./captured_commands/",
            f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
        )
        save_wav_file(full_audio, filename)
        duration = len(full_audio) / 16000

        try:
            self.processing_queue.put((filename, duration))
            self.logger.info(f"Comando encolado para procesar: {filename}")
        except queue.Full:
            self.logger.warning("Cola de procesamiento llena. Comando descartado.")
