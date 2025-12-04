"""
Módulo de Estado - Jeepy AI
Contiene clases para gestionar el estado compartido y la recuperación de errores.
"""

import threading
import time

# --- CONSTANTES DE ESTADO ---
STATE_MONITORING = "monitoring"
STATE_RECORDING = "recording"
STATE_PROCESSING = "processing"
STATE_TRANSCRIBING = "transcribing"
STATE_PROCESSING_NLU = "processing_nlu"
STATE_ERROR = "error"
STATE_PAUSED = "paused"

# --- CONSTANTES DE ROBUSTEZ ---
MAX_INFERENCE_RETRIES = 3
ERROR_RECOVERY_COOLDOWN = 1.0


class ErrorRecoveryManager:
    """Gestiona reintentos y recuperación ante errores."""

    def __init__(self, max_retries=MAX_INFERENCE_RETRIES):
        self.max_retries = max_retries
        self.error_counts = {}
        self.last_error_time = {}

    def should_retry(self, error_type: str) -> bool:
        """Determina si se debe reintentar ante un error."""
        current_time = time.time()
        if error_type in self.last_error_time and (
            current_time - self.last_error_time[error_type] > ERROR_RECOVERY_COOLDOWN
        ):
            self.error_counts[error_type] = 0

        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_error_time[error_type] = current_time

        return self.error_counts[error_type] <= self.max_retries

    def reset(self, error_type: str):
        """Resetea el contador de errores para un tipo específico."""
        self.error_counts[error_type] = 0


class AudioChunk:
    """Objeto para transportar datos de audio y metadatos entre hilos."""

    def __init__(self, data, timestamp, rms):
        self.data = data
        self.timestamp = timestamp
        self.rms = rms


class SystemState:
    """Gestiona el estado compartido del sistema de forma thread-safe."""

    def __init__(self):
        self.fps = 0.0
        self.cpu_usage = 0.0
        self.last_prediction = 0.0
        self.is_speaking = False
        self.noise_level = 0.0
        self.current_state = STATE_MONITORING
        self.last_error = None
        self.lock = threading.Lock()

    def set_state(self, state: str):
        with self.lock:
            if self.current_state != state:
                self.current_state = state

    def get_state(self) -> str:
        with self.lock:
            return self.current_state

    def set_error(self, error_msg: str):
        with self.lock:
            self.last_error = error_msg
            self.current_state = STATE_ERROR

    def get_status_string(self) -> str:
        with self.lock:
            state_icons = {
                STATE_MONITORING: "👀",
                STATE_RECORDING: "🔴",
                STATE_PROCESSING: "⚙️",
                STATE_TRANSCRIBING: "📝",
                STATE_PROCESSING_NLU: "🤖",
                STATE_ERROR: "❌",
                STATE_PAUSED: "⏸️",
            }
            state_icon = state_icons.get(self.current_state, "❓")
            vad_state = "🗣️" if self.is_speaking else ".."
            return (
                f"{state_icon} CPU: {self.cpu_usage:4.1f}% | "
                f"FPS: {self.fps:4.1f} | VAD: {vad_state} | "
                f"Conf: {self.last_prediction:.4f} | "
                f"Noise: {self.noise_level:.4f}"
            )
