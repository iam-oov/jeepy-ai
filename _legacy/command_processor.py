"""
Módulo de Procesamiento de Comandos - Jeepy AI
Contiene el hilo consumidor que procesa comandos grabados (STT, NLU, Acción).
"""

import threading
import queue
import os
from datetime import datetime

from src.monitor.state import (
    SystemState,
    STATE_TRANSCRIBING,
    STATE_PROCESSING_NLU,
    STATE_MONITORING,
)
from src.stt_engine import STTManager
from src.gemini_engine import GeminiEngine, VehicleController
from src.config import Config

# --- CONSTANTES ---
STT_ENABLED = True  # Asumimos que está habilitado si este módulo se usa
GEMINI_ENABLED = True
STT_SAVE_TRANSCRIPTIONS = True
TRANSCRIPTIONS_DIR = "./transcriptions/"
GEMINI_SAVE_RESULTS = True
INTERPRETATIONS_DIR = "./interpretations/"
STT_AUTO_DELETE_AUDIO = True


class CommandProcessorThread(threading.Thread):
    """Hilo consumidor que procesa comandos grabados."""

    def __init__(
        self,
        processing_queue: queue.Queue,
        stop_event: threading.Event,
        system_state: SystemState,
        logger,
    ):
        super().__init__()
        self.processing_queue = processing_queue
        self.stop_event = stop_event
        self.system_state = system_state
        self.logger = logger
        self.daemon = True

        self.stt_manager = STTManager() if STT_ENABLED else None
        self.gemini_engine = GeminiEngine() if GEMINI_ENABLED else None
        self.vehicle_controller = VehicleController() if GEMINI_ENABLED else None

    def run(self):
        self.logger.info("Procesador de comandos iniciado")
        while not self.stop_event.is_set():
            try:
                audio_file, duration = self.processing_queue.get(timeout=1.0)

                transcription = self._transcribe_command(audio_file, duration)
                if transcription and self.gemini_engine:
                    self._process_with_gemini(transcription, audio_file)

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error en CommandProcessorThread: {e}")

        self.logger.info("Procesador de comandos detenido")

    def _transcribe_command(self, audio_file, duration):
        """Transcribe comando de audio a texto."""
        try:
            self.system_state.set_state(STATE_TRANSCRIBING)
            print(f"📝 Transcribiendo comando...")
            transcription = self.stt_manager.transcribe(audio_file)

            if transcription:
                self.logger.info(f"Transcripción: {transcription}")
                print(f'\\n💬 Transcripción: "{transcription}"\\n')
                if STT_SAVE_TRANSCRIPTIONS:
                    self._save_transcription(audio_file, transcription, duration)
                return transcription
            else:
                print(f"⚠️ No se pudo transcribir el comando")
                self.logger.warning("Transcripción falló")
                return None
        except Exception as e:
            print(f"❌ Error en transcripción: {e}")
            self.logger.error(f"Error en transcripción: {e}")
            return None

    def _save_transcription(self, audio_file, transcription, duration):
        """Guarda la transcripción en un archivo."""
        # ... (código de _save_transcription de kws_monitor.py) ...

    def _process_with_gemini(self, transcription, audio_file):
        """Procesa la transcripción con Gemini NLU."""
        try:
            self.system_state.set_state(STATE_PROCESSING_NLU)
            print(f"\\n🤖 Procesando con Gemini...\\n")
            result = self.gemini_engine.process_command(transcription)

            if not result:
                print(f"⚠️ Gemini no pudo interpretar el comando")
                return

            if result["action"] != "aclaracion_requerida":
                self.vehicle_controller.execute_action(
                    result["action"], result.get("parameters", {})
                )

            if GEMINI_SAVE_RESULTS:
                self._save_gemini_result(audio_file, transcription, result)

        except Exception as e:
            print(f"❌ Error procesando con Gemini: {e}")
        finally:
            self.system_state.set_state(STATE_MONITORING)
            if STT_AUTO_DELETE_AUDIO:
                try:
                    os.remove(audio_file)
                except OSError as e:
                    self.logger.error(f"Error eliminando archivo de audio: {e}")

    def _save_gemini_result(self, audio_file, transcription, result):
        """Guarda el resultado de Gemini en un archivo."""
        # ... (código de _save_gemini_result de kws_monitor.py) ...
