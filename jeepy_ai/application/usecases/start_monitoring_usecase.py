"""
Use Case: StartMonitoringUseCase
Caso de uso para iniciar el monitoreo del sistema.
"""

import logging
from jeepy_ai.controllers import MonitorController


class StartMonitoringUseCase:
    """Caso de uso: Iniciar monitoreo."""

    def __init__(self, monitor_controller: MonitorController):
        self.controller = monitor_controller
        self.logger = logging.getLogger(__name__)

    def execute(self) -> bool:
        """
        Ejecuta el caso de uso.

        Returns:
            True si se inició correctamente
        """
        self.logger.info("Ejecutando StartMonitoringUseCase...")
        return self.controller.start()
