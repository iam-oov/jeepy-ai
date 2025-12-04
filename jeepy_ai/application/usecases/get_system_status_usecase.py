"""
Use Case: GetSystemStatusUseCase
Caso de uso para obtener estado del sistema.
"""

import logging
from typing import Dict, Any
from jeepy_ai.controllers import MonitorController


class GetSystemStatusUseCase:
    """Caso de uso: Obtener estado del sistema."""

    def __init__(self, monitor_controller: MonitorController):
        self.controller = monitor_controller
        self.logger = logging.getLogger(__name__)

    def execute(self) -> Dict[str, Any]:
        """
        Ejecuta el caso de uso.

        Returns:
            Diccionario con estado del sistema
        """
        return self.controller.get_status()
