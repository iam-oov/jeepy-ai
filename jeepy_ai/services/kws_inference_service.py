"""
Service: KWSInferenceService
Hilo consumidor que detecta palabra clave y gestiona grabación.
"""

import threading
import queue
import time
import os
from datetime import datetime
import numpy as np

from jeepy_ai.entities import SystemState

# Importar constantes cuando sea necesario
from jeepy_ai.entities.system_state import SystemStateConstants


class KWSInferenceService(threading.Thread):
    """Servicio: Procesa audio para KWS e inferencia (thread seguro)."""

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

        # Placeholder para inicializaciones futuras
        # self.kws_model = None
        # self.window_buffer = None
        # self.recording_buffer = None

    def run(self):
        """Loop principal del servicio."""
        self.logger.info("KWSInferenceService iniciado")

        while not self.stop_event.is_set():
            try:
                chunk = self.audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error al obtener chunk: {e}")
                continue

            current_state = self.system_state.get_state()

            # Lógica según estado
            if current_state == SystemStateConstants.STATE_MONITORING:
                # Procesar chunk para KWS
                pass

            elif current_state == SystemStateConstants.STATE_RECORDING:
                # Acumular chunk en buffer de grabación
                pass

        self.logger.info("KWSInferenceService detenido")

    def _finish_recording(self, recording_buffer):
        """Finaliza grabación y encola para procesamiento."""
        self.system_state.set_state(SystemStateConstants.STATE_PROCESSING)

        full_audio = np.concatenate(recording_buffer)
        filename = os.path.join(
            "./captured_commands/",
            f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
        )

        try:
            self.processing_queue.put((filename, len(full_audio) / 16000), block=False)
            self.logger.info(f"Comando encolado: {filename}")
        except queue.Full:
            self.logger.warning("Cola de procesamiento llena")
