"""
Entity: SystemState
Gestiona el estado compartido del sistema de forma thread-safe.
"""

import threading


class SystemStateConstants:
    """Constantes de estado del sistema."""

    STATE_MONITORING = "monitoring"
    STATE_RECORDING = "recording"
    STATE_PROCESSING = "processing"
    STATE_TRANSCRIBING = "transcribing"
    STATE_PROCESSING_NLU = "processing_nlu"
    STATE_ERROR = "error"
    STATE_PAUSED = "paused"

    ALL_STATES = [
        STATE_MONITORING,
        STATE_RECORDING,
        STATE_PROCESSING,
        STATE_TRANSCRIBING,
        STATE_PROCESSING_NLU,
        STATE_ERROR,
        STATE_PAUSED,
    ]


class SystemState:
    """Gestiona el estado compartido del sistema."""

    def __init__(self):
        self.fps = 0.0
        self.cpu_usage = 0.0
        self.last_prediction = 0.0
        self.is_speaking = False
        self.noise_level = 0.0
        self.current_state = SystemStateConstants.STATE_MONITORING
        self.last_error = None
        self.lock = threading.Lock()

    def set_state(self, state: str):
        """Cambia el estado del sistema (thread-safe)."""
        with self.lock:
            if state in SystemStateConstants.ALL_STATES:
                if self.current_state != state:
                    self.current_state = state

    def get_state(self) -> str:
        """Obtiene el estado actual (thread-safe)."""
        with self.lock:
            return self.current_state

    def set_error(self, error_msg: str):
        """Marca error en el sistema (thread-safe)."""
        with self.lock:
            self.last_error = error_msg
            self.current_state = SystemStateConstants.STATE_ERROR

    def update_metrics(
        self,
        fps: float | None = None,
        cpu: float | None = None,
        noise: float | None = None,
        prediction: float | None = None,
    ):
        """Actualiza métricas del sistema (thread-safe)."""
        with self.lock:
            if fps is not None:
                self.fps = fps
            if cpu is not None:
                self.cpu_usage = cpu
            if noise is not None:
                self.noise_level = noise
            if prediction is not None:
                self.last_prediction = prediction

    def get_status_string(self) -> str:
        """Retorna string formateado con estado actual (thread-safe)."""
        with self.lock:
            state_icons = {
                SystemStateConstants.STATE_MONITORING: "👀",
                SystemStateConstants.STATE_RECORDING: "🔴",
                SystemStateConstants.STATE_PROCESSING: "⚙️",
                SystemStateConstants.STATE_TRANSCRIBING: "📝",
                SystemStateConstants.STATE_PROCESSING_NLU: "🤖",
                SystemStateConstants.STATE_ERROR: "❌",
                SystemStateConstants.STATE_PAUSED: "⏸️",
            }
            state_icon = state_icons.get(self.current_state, "❓")
            vad_state = "🗣️" if self.is_speaking else ".."
            return (
                f"{state_icon} CPU: {self.cpu_usage:4.1f}% | "
                f"FPS: {self.fps:4.1f} | VAD: {vad_state} | "
                f"Conf: {self.last_prediction:.4f} | "
                f"Noise: {self.noise_level:.4f}"
            )
