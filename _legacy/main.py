"""
Punto de Entrada Principal del Monitor KWS - Jeepy AI
Inicializa y gestiona los hilos de captura, inferencia y procesamiento.
"""

import threading
import queue
import time
import psutil
import logging

from src.monitor.state import SystemState
from src.monitor.audio_capture import AudioCaptureThread
from src.monitor.kws_inference import InferenceThread
from src.monitor.command_processor import CommandProcessorThread
from src.utils import setup_logger, get_input_device_index

# --- CONSTANTES ---
QUEUE_SIZE = 20
CPU_MONITOR_INTERVAL = 2.0


def main():
    """Función principal para ejecutar el monitor KWS."""
    logger = setup_logger("INFO", "kws_monitor.log")
    logger.info("Iniciando Jeepy AI Monitor...")

    audio_queue = queue.Queue(maxsize=QUEUE_SIZE)
    processing_queue = queue.Queue(maxsize=10)
    stop_event = threading.Event()
    system_state = SystemState()

    device_index = get_input_device_index()

    capture_thread = AudioCaptureThread(
        device_index, audio_queue, stop_event, system_state
    )
    inference_thread = InferenceThread(
        audio_queue, processing_queue, stop_event, system_state, logger
    )
    processor_thread = CommandProcessorThread(
        processing_queue, stop_event, system_state, logger
    )

    capture_thread.start()
    inference_thread.start()
    processor_thread.start()

    print("Jeepy AI Monitor iniciado. Presiona Ctrl+C para detener.")

    try:
        while not stop_event.is_set():
            time.sleep(CPU_MONITOR_INTERVAL)
            cpu_usage = psutil.cpu_percent()
            system_state.update_metrics(cpu=cpu_usage)
            print(f"\\r{system_state.get_status_string()}", end="", flush=True)
    except KeyboardInterrupt:
        print("\\nDeteniendo Jeepy AI Monitor...")
    finally:
        stop_event.set()
        capture_thread.join()
        inference_thread.join()
        processor_thread.join()
        print("Jeepy AI Monitor detenido.")


if __name__ == "__main__":
    main()
