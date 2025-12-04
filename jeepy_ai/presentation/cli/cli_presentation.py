"""
Presentation: CLIPresentation
Interfaz de línea de comandos para el monitor.
"""

import time
import psutil
import logging
from typing import Optional

from jeepy_ai.controllers import MonitorController
from jeepy_ai.application.usecases import (
    StartMonitoringUseCase,
    StopMonitoringUseCase,
    GetSystemStatusUseCase,
)


class CLIPresentation:
    """Presentación: Interfaz CLI para Jeepy AI Monitor."""

    def __init__(self, monitor_controller: Optional[MonitorController] = None):
        """
        Inicializa la presentación.

        Args:
            monitor_controller: Controller del monitor (si es None, se crea uno)
        """
        self.logger = logging.getLogger(__name__)
        self.controller = monitor_controller or MonitorController(logger=self.logger)

        # Casos de uso
        self.start_usecase = StartMonitoringUseCase(self.controller)
        self.stop_usecase = StopMonitoringUseCase(self.controller)
        self.status_usecase = GetSystemStatusUseCase(self.controller)

    def run(self):
        """Ejecuta la presentación en modo interactivo."""
        try:
            # Iniciar monitoreo
            if not self.start_usecase.execute():
                print("❌ Error al iniciar el monitor")
                return

            # Loop de monitoreo
            try:
                while self.controller.is_running:
                    time.sleep(2.0)

                    # Obtener estado
                    status = self.status_usecase.execute()

                    # Actualizar métricas de CPU
                    cpu_usage = psutil.cpu_percent()
                    self.controller.system_state.update_metrics(cpu=cpu_usage)

                    # Mostrar estado
                    print(
                        f"\r{self.controller.system_state.get_status_string()}",
                        end="",
                        flush=True,
                    )

            except KeyboardInterrupt:
                print("\n🛑 Deteniendo monitor...")
                self.stop_usecase.execute()

        except Exception as e:
            self.logger.error(f"Error en CLIPresentation: {e}")
            self.stop_usecase.execute()

    @staticmethod
    def print_welcome():
        """Imprime mensaje de bienvenida."""
        print("""
        ╔════════════════════════════════════════╗
        ║         🎙️  JEEPY AI MONITOR 🎙️         ║
        ║      Voice Control System for Jeep     ║
        ╚════════════════════════════════════════╝
        """)

    @staticmethod
    def print_goodbye():
        """Imprime mensaje de despedida."""
        print("""
        ╔════════════════════════════════════════╗
        ║          ✅ Gracias por usar Jeepy!     ║
        ╚════════════════════════════════════════╝
        """)
