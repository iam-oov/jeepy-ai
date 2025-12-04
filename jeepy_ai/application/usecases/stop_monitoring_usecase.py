"""
Use Case: StopMonitoringUseCase
Caso de uso para detener el monitoreo del sistema.
"""

import logging
from jeepy_ai.controllers import MonitorController


class StopMonitoringUseCase:
    """Caso de uso: Detener monitoreo."""

    def __init__(self, monitor_controller: MonitorController):
        self.controller = monitor_controller
        self.logger = logging.getLogger(__name__)

    def execute(self):
        """Ejecuta el caso de uso."""
        self.logger.info("Ejecutando StopMonitoringUseCase...")
        self.controller.stop()
