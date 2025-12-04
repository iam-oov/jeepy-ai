"""
Punto de Entrada Principal - Jeepy AI Monitor
Arquitectura: SCREAM (Screen, Controller, Repository, Entity, Application, Service)
"""

import logging
from jeepy_ai.presentation.cli.cli_presentation import CLIPresentation


def setup_logging():
    """Configura logging del sistema."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("jeepy_ai_monitor.log"),
            logging.StreamHandler(),
        ],
    )


def main():
    """Punto de entrada principal."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Crear presentación CLI
        cli = CLIPresentation()

        # Mostrar bienvenida
        cli.print_welcome()

        # Ejecutar monitor
        cli.run()

        # Mostrar despedida
        cli.print_goodbye()

    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
