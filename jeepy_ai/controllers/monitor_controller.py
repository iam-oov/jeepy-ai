"""
Controller: MonitorController
Orquestra los servicios y flujos de captura, inferencia y procesamiento.
"""

import threading
import queue
import logging
from typing import Optional

from jeepy_ai.entities import SystemState
from jeepy_ai.repositories import AudioRepository, CommandRepository, ConfigRepository
from jeepy_ai.services import (
    AudioCaptureService,
    KWSInferenceService,
    CommandProcessorService,
)


class MonitorController:
    """Controller que orquestra el monitor de audio (patrón SCREAM)."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        config: Optional[ConfigRepository] = None,
    ):
        """
        Inicializa el controller.

        Args:
            logger: Logger para eventos
            config: Repositorio de configuración
        """
        self.logger = logger or self._create_default_logger()
        self.config = config or ConfigRepository()
        self.config.load_from_env()

        # Entidades
        self.system_state = SystemState()

        # Repositorios
        self.audio_repo = AudioRepository()
        self.command_repo = CommandRepository()

        # Servicios (threads)
        self.audio_service: Optional[AudioCaptureService] = None
        self.kws_service: Optional[KWSInferenceService] = None
        self.processor_service: Optional[CommandProcessorService] = None

        # Colas para comunicación entre servicios
        self.audio_queue: queue.Queue = queue.Queue(
            maxsize=20
        )  # LIFO para audio real-time
        self.processing_queue: queue.Queue = queue.Queue(
            maxsize=10
        )  # FIFO para procesamiento

        # Control
        self.stop_event = threading.Event()
        self.is_running = False

    def start(self) -> bool:
        """
        Inicia el monitor.

        Returns:
            True si se inició correctamente, False en caso contrario
        """
        try:
            if self.is_running:
                self.logger.warning("Monitor ya está en ejecución")
                return False

            self.logger.info("Iniciando MonitorController...")

            # Obtener índice de dispositivo
            device_index = self.config.get("DEVICE_INDEX", 0)

            # Crear servicios
            self.audio_service = AudioCaptureService(
                device_index=device_index,
                audio_queue=self.audio_queue,
                stop_event=self.stop_event,
                system_state=self.system_state,
            )

            self.kws_service = KWSInferenceService(
                audio_queue=self.audio_queue,
                processing_queue=self.processing_queue,
                stop_event=self.stop_event,
                system_state=self.system_state,
                logger=self.logger,
            )

            self.processor_service = CommandProcessorService(
                processing_queue=self.processing_queue,
                stop_event=self.stop_event,
                system_state=self.system_state,
                logger=self.logger,
            )

            # Iniciar servicios
            self.audio_service.start()
            self.kws_service.start()
            self.processor_service.start()

            self.is_running = True
            self.logger.info("✓ MonitorController iniciado correctamente")
            print("🎙️  Jeepy AI Monitor iniciado. Presiona Ctrl+C para detener.")

            return True

        except Exception as e:
            self.logger.error(f"Error al iniciar MonitorController: {e}")
            self.stop()
            return False

    def stop(self):
        """Detiene el monitor y espera a que los servicios terminen."""
        if not self.is_running:
            return

        self.logger.info("Deteniendo MonitorController...")
        self.stop_event.set()

        # Esperar a que los threads terminen
        if self.audio_service and self.audio_service.is_alive():
            self.audio_service.join(timeout=5)

        if self.kws_service and self.kws_service.is_alive():
            self.kws_service.join(timeout=5)

        if self.processor_service and self.processor_service.is_alive():
            self.processor_service.join(timeout=5)

        self.is_running = False
        self.logger.info("✓ MonitorController detenido")

    def get_status(self) -> dict:
        """Retorna estado actual del sistema."""
        return {
            "is_running": self.is_running,
            "state": self.system_state.get_state(),
            "status_string": self.system_state.get_status_string(),
            "cpu_usage": self.system_state.cpu_usage,
            "fps": self.system_state.fps,
            "audio_queue_size": self.audio_queue.qsize(),
            "processing_queue_size": self.processing_queue.qsize(),
        }

    @staticmethod
    def _create_default_logger() -> logging.Logger:
        """Crea logger por defecto."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger("MonitorController")
