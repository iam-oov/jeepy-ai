"""
Service: CommandProcessorService
Hilo consumidor que procesa comandos (STT, NLU, Acción).
"""

import threading
import queue
import logging

from jeepy_ai.entities import SystemState
from jeepy_ai.entities.system_state import SystemStateConstants


class CommandProcessorService(threading.Thread):
    """Servicio: Procesa comandos grabados (STT, NLU) de forma asincrónica."""

    def __init__(
        self,
        processing_queue: queue.Queue,
        stop_event: threading.Event,
        system_state: SystemState,
        logger: logging.Logger,
    ):
        super().__init__()
        self.processing_queue = processing_queue
        self.stop_event = stop_event
        self.system_state = system_state
        self.logger = logger
        self.daemon = True

        # Placeholder para servicios inyectados
        # self.stt_manager = None
        # self.gemini_engine = None
        # self.repositories = {}

    def run(self):
        """Loop principal del servicio."""
        self.logger.info("CommandProcessorService iniciado")

        while not self.stop_event.is_set():
            try:
                audio_file, duration = self.processing_queue.get(timeout=1.0)
                self._process_command(audio_file, duration)

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error en CommandProcessorService: {e}")

        self.logger.info("CommandProcessorService detenido")

    def _process_command(self, audio_file: str, duration: float):
        """Procesa un comando completo (STT -> NLU -> Acción)."""
        try:
            # 1. Transcripción (STT)
            transcription = self._transcribe_command(audio_file, duration)
            if not transcription:
                return

            # 2. Procesamiento con Gemini (NLU + Acción)
            if transcription:
                self._process_with_gemini(transcription, audio_file)

        except Exception as e:
            self.logger.error(f"Error procesando comando: {e}")
            self.system_state.set_error(f"Error procesamiento: {e}")

    def _transcribe_command(self, audio_file: str, duration: float) -> str | None:
        """Transcribe comando de audio a texto."""
        try:
            self.system_state.set_state(SystemStateConstants.STATE_TRANSCRIBING)
            print(f"📝 Transcribiendo comando...")

            # TODO: Inyectar STTManager y llamar transcripción
            # transcription = self.stt_manager.transcribe(audio_file)

            self.logger.info(f"Comando transcrito: (implementar STT)")
            return None  # Placeholder

        except Exception as e:
            self.logger.error(f"Error en transcripción: {e}")
            return None

    def _process_with_gemini(self, transcription: str, audio_file: str):
        """Procesa con Gemini para interpretación y ejecución."""
        try:
            self.system_state.set_state(SystemStateConstants.STATE_PROCESSING_NLU)
            print(f"🤖 Procesando con Gemini...")

            # TODO: Inyectar GeminiEngine y VehicleController
            # result = self.gemini_engine.process_command(transcription)

            self.logger.info(f"Comando procesado con Gemini")
            self.system_state.set_state(SystemStateConstants.STATE_MONITORING)

        except Exception as e:
            self.logger.error(f"Error en Gemini: {e}")
            self.system_state.set_state(SystemStateConstants.STATE_MONITORING)
