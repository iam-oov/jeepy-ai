"""
Entity: ErrorRecoveryManager
Gestiona reintentos y recuperación ante errores.
"""

import time

MAX_INFERENCE_RETRIES = 3
ERROR_RECOVERY_COOLDOWN = 1.0


class ErrorRecoveryManager:
    """Gestiona reintentos y recuperación ante errores."""

    def __init__(self, max_retries: int = MAX_INFERENCE_RETRIES):
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

    def get_retry_count(self, error_type: str) -> int:
        """Obtiene el número de reintentos para un error."""
        return self.error_counts.get(error_type, 0)
